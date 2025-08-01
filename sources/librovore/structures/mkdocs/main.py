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


''' MkDocs documentation structure processor main implementation. '''


from . import __
from .detection import MkDocsDetection


class MkDocsProcessor( __.Processor ):
    ''' Documentation processor for MkDocs sites with mkdocstrings. '''

    name: str = 'mkdocs'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns MkDocs processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = self.name,
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'domain',
                    description = 'Filter by object domain (e.g., py, js)',
                    type = 'string'
                ),
                __.FilterCapability(
                    name = 'role',
                    description = (
                        'Filter by object role (e.g., class, function)' ),
                    type = 'string'
                ),
                __.FilterCapability(
                    name = 'priority',
                    description = 'Filter by object priority',
                    type = 'string'
                ),
            ],
            results_limit_max = 1000,
            response_time_typical = 'fast',
            notes = (
                'Processes MkDocs sites with mkdocstrings via Sphinx '
                'inventory' )
        )

    async def detect( self, source: str ) -> MkDocsDetection:
        ''' Detects MkDocs documentation structure from source. '''
        from .detection import (
            check_objects_inv as _check_objects_inv,
            check_mkdocs_yml as _check_mkdocs_yml,
            detect_theme as _detect_theme,
        )
        base_url = __.normalize_base_url( source )
        normalized_source = base_url.geturl( )
        has_objects_inv = await _check_objects_inv( base_url )
        has_mkdocs_yml = await _check_mkdocs_yml( base_url )
        confidence = 0.0
        if has_objects_inv: confidence += 0.8
        if has_mkdocs_yml: confidence += 0.4
        confidence = min( confidence, 1.0 )
        theme_metadata = await _detect_theme( base_url )
        theme = theme_metadata.get( 'theme' )
        return MkDocsDetection(
            processor = self,
            confidence = confidence,
            source = source,
            has_objects_inv = has_objects_inv,
            has_mkdocs_yml = has_mkdocs_yml,
            normalized_source = normalized_source,
            theme = theme,
        )