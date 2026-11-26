# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Rustdoc documentation structure detection. '''


from bs4 import BeautifulSoup as _BeautifulSoup

from . import __
from . import extraction as _extraction


_scribe = __.acquire_scribe( __name__ )


class RustdocDetection( __.StructureDetection ):
    ''' Detection result for Rustdoc documentation sources. '''

    source: str
    normalized_source: str = ''
    rustdoc_version: __.typx.Optional[ str ] = None

    @classmethod
    def get_capabilities( cls ) -> __.StructureProcessorCapabilities:
        ''' Rustdoc processor capabilities based on structure analysis. '''
        return __.StructureProcessorCapabilities(
            supported_inventory_types = frozenset( { 'rustdoc' } ),
            content_extraction_features = frozenset( {
                __.ContentExtractionFeatures.Signatures,
                __.ContentExtractionFeatures.Descriptions,
                __.ContentExtractionFeatures.CodeExamples,
                __.ContentExtractionFeatures.CrossReferences,
            } ),
            confidence_by_inventory_type = __.immut.Dictionary( {
                'rustdoc': 0.95
            } )
        )

    async def extract_contents(
        self,
        auxdata: __.ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ __.InventoryObject ], /,
    ) -> tuple[ __.ContentDocument, ... ]:
        ''' Extracts documentation content for specified objects. '''
        documents = await _extraction.extract_contents(
            auxdata, source, objects )
        return tuple( documents )


async def detect_rustdoc(
    auxdata: __.ApplicationGlobals, source_url: __.typx.Any
) -> tuple[ bool, __.typx.Optional[ str ] ]:
    ''' Detects if source is Rustdoc-generated documentation. '''
    try:
        html_content = await __.retrieve_url_as_text(
            auxdata.content_cache, source_url, duration_max = 10.0 )
    except __.DocumentationInaccessibility:
        return False, None
    if __.is_absent( html_content ):
        return False, None
    try: soup = _BeautifulSoup( html_content, 'lxml' )
    except Exception as exc:
        _scribe.debug( f"HTML parsing failed for {source_url}: {exc}" )
        return False, None
    is_rustdoc, version = detect_rustdoc_markers( soup )
    return is_rustdoc, version


def detect_rustdoc_markers(
    soup: __.typx.Any
) -> tuple[ bool, __.typx.Optional[ str ] ]:
    ''' Detects Rustdoc-specific HTML markers. '''
    rustdoc_version = None
    meta_generator = soup.find( 'meta', attrs = { 'name': 'generator' } )
    if meta_generator:
        content = meta_generator.get( 'content', '' )
        if 'rustdoc' in str( content ).lower( ):
            return True, str( content )
    if soup.find( 'rustdoc-topbar' ):
        version_attr = soup.find( attrs = { 'data-rustdoc-version': True } )
        if version_attr:
            rustdoc_version = version_attr.get( 'data-rustdoc-version' )
        return True, rustdoc_version
    if soup.find( attrs = { 'data-rustdoc-version': True } ):
        version_attr = soup.find( attrs = { 'data-rustdoc-version': True } )
        rustdoc_version = version_attr.get( 'data-rustdoc-version' )
        return True, rustdoc_version
    css_pattern = __.re.compile( r'rustdoc.*\.css' )
    if soup.find( 'link', href = css_pattern ):
        return True, None
    return False, None
