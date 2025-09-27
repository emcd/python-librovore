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


''' Family of exceptions for package API. '''


import urllib.parse as _urlparse

from . import __


class Omniexception( __.immut.Object, BaseException ):
    ''' Base for all exceptions raised by package API. '''

    _attribute_visibility_includes_: __.cabc.Collection[ str ] = (
        frozenset( ( '__cause__', '__context__', ) ) )


class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions with self-rendering capability. '''

    @__.abc.abstractmethod
    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders exception as JSON-compatible dictionary. '''
        raise NotImplementedError

    @__.abc.abstractmethod  
    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( '''
                Controls whether implementation-specific details (internal 
                field names, version numbers, priority scores) are included. 
                When False, only user-facing information is shown.
            ''' ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders exception as Markdown lines for display. '''
        raise NotImplementedError


class DetectionConfidenceInvalidity( Omnierror, ValueError ):
    ''' Detection confidence value is out of valid range. '''

    def __init__( self, confidence: float ):
        self.confidence = confidence
        super( ).__init__( f"Confidence {confidence} not in range [0.0, 1.0]" )


class DocumentationContentAbsence( Omnierror, ValueError ):
    ''' Documentation main content container not found. '''

    def __init__( self, url: str ):
        message = f"No main content found in documentation at '{url}'."
        self.url = url
        super( ).__init__( message )


class DocumentationInaccessibility( Omnierror, RuntimeError ):
    ''' Documentation file or resource absent or inaccessible. '''

    def __init__( self, url: str, cause: str | Exception ):
        message = f"Documentation at '{url}' is inaccessible. Cause: {cause}"
        self.url = url
        super( ).__init__( message )


class DocumentationObjectAbsence( Omnierror, ValueError ):
    ''' Requested object not found in documentation page. '''

    def __init__( self, object_id: str, url: str ):
        message = (
            f"Object '{object_id}' not found in documentation page "
            f"at '{url}'" )
        self.object_id = object_id
        self.url = url
        super( ).__init__( message )


class DocumentationParseFailure( Omnierror, ValueError ):
    ''' Documentation HTML parsing failed or content malformed. '''

    def __init__( self, url: str, cause: str | Exception ):
        message = f"Cannot parse documentation at '{url}'. Cause: {cause}"
        self.url = url
        super( ).__init__( message )


class ExtensionCacheFailure( Omnierror, RuntimeError ):
    ''' Extension cache operation failed. '''

    def __init__( self, cache_path: __.Path, message: str ):
        self.cache_path = cache_path
        super( ).__init__( f"Cache error at '{cache_path}': {message}" )


class ExtensionConfigurationInvalidity( Omnierror, ValueError ):
    ''' Extension configuration is invalid. '''

    def __init__( self, extension_name: str, message: str ):
        self.extension_name = extension_name
        super( ).__init__( f"Extension '{extension_name}': {message}" )


class ExtensionInstallFailure( Omnierror, RuntimeError ):
    ''' Extension package installation failed. '''

    def __init__( self, package_spec: str, message: str ):
        self.package_spec = package_spec
        super( ).__init__( f"Failed to install '{package_spec}': {message}" )


class ExtensionRegisterFailure( Omnierror, TypeError ):
    ''' Invalid plugin could not be registered. '''

    def __init__( self, message: str ):
        # TODO: Canned message with extension name as argument.
        super( ).__init__( message )


class ExtensionVersionConflict( Omnierror, ImportError ):
    ''' Extension has incompatible version requirements. '''

    def __init__( self, package_name: str, required: str, available: str ):
        self.package_name = package_name
        self.required = required
        self.available = available
        super( ).__init__(
            f"Version conflict for '{package_name}': "
            f"required {required}, available {available}" )


class HttpContentTypeInvalidity( Omnierror, ValueError ):
    ''' HTTP content type is not suitable for requested operation. '''

    def __init__( self, url: str, content_type: str, operation: str ):
        self.url = url
        self.content_type = content_type
        self.operation = operation
        super( ).__init__(
            f"Content type '{content_type}' not suitable for {operation} "
            f"operation on URL: {url}" )


class InventoryFilterInvalidity( Omnierror, ValueError ):
    ''' Inventory filter is invalid. '''

    def __init__( self, message: str ):
        super( ).__init__( message )


class InventoryInaccessibility( Omnierror, RuntimeError ):
    ''' Inventory file or resource absent or inaccessible. '''

    def __init__(
        self,
        source: str,
        cause: __.typx.Optional[ BaseException ] = None,
    ):
        self.source = source
        self.cause = cause
        message = f"Inventory at '{source}' is inaccessible."
        if cause is not None:
            message += f" Cause: {cause}"
        super( ).__init__( message )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders inventory inaccessibility as JSON-compatible dict. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'inventory_inaccessible',
            title = 'Inventory Location Inaccessible',
            message = str( self ),
            source = self.source,
            cause = str( self.cause ) if self.cause is not None else None,
            suggestion = (
                'Check that the URL is correct and the documentation site is '
                'accessible.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders inventory inaccessibility as Markdown lines. '''
        lines = [ "## Error: Inventory Location Inaccessible" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Check that the URL is correct and the "
            "documentation site is accessible." )
        if reveal_internals:
            lines.append( f"**Source:** {self.source}" )
            if self.cause is not None:
                lines.append( f"**Cause:** {self.cause}" )
            lines.append( "**Error Type:** inventory_inaccessible" )
        return tuple( lines )


class InventoryInvalidity( Omnierror, ValueError ):
    ''' Inventory has invalid format or cannot be parsed. '''

    def __init__(
        self,
        source: str,
        cause: str | Exception,
    ):
        self.source = source
        self.cause = cause
        message = f"Inventory at '{source}' is invalid. Cause: {cause}"
        super( ).__init__( message )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders inventory invalidity as JSON-compatible dict. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'inventory_invalid',
            title = 'Invalid Inventory Format',
            message = str( self ),
            source = self.source,
            cause = str( self.cause ),
            suggestion = (
                'Verify that the inventory format is supported and the file '
                'is not corrupted.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders inventory invalidity as Markdown lines. '''
        lines = [ "## Error: Invalid Inventory Format" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Verify that the inventory format is supported "
            "and the file is not corrupted." )
        if reveal_internals:
            lines.append( f"**Source:** {self.source}" )
            lines.append( f"**Cause:** {self.cause}" )
            lines.append( "**Error Type:** inventory_invalid" )
        return tuple( lines )


class InventoryUrlInvalidity( Omnierror, ValueError ):
    ''' Inventory URL is malformed or invalid. '''

    def __init__( self, source: str ):
        message = f"Invalid URL format: {source}"
        self.source = source
        super( ).__init__( message )


class InventoryUrlNoSupport( Omnierror, NotImplementedError ):
    ''' Inventory URL has unsupported component. '''

    def __init__(
        self, url: _urlparse.ParseResult, component: str,
        value: __.Absential[ str ] = __.absent,
    ):
        url_s = _urlparse.urlunparse( url )
        message_c = f"Component '{component}' "
        message_i = f"not supported in inventory URL '{url_s}'."
        message = (
            f"{message_c} {message_i}" if __.is_absent( value )
            else f"{message_c} with value '{value}' {message_i}" )
        self.url = url
        super( ).__init__( message )


class ProcessorGenusInvalidity( Omnierror, ValueError ):
    ''' Invalid processor genus provided. '''

    def __init__( self, genus: __.typx.Any ):
        message = f"Invalid ProcessorGenera: {genus}"
        self.genus = genus
        super( ).__init__( message )


class ProcessorInavailability( Omnierror, RuntimeError ):
    ''' No processor found to handle source. '''

    def __init__(
        self,
        source: str,
        genus: __.Absential[ str ] = __.absent,
    ):
        self.source = source
        self.genus = genus  
        message = f"No processor found to handle source: {source}"
        if not __.is_absent( genus ):
            message += f" (genus: {genus})"
        super( ).__init__( message )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders processor unavailability as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'processor_unavailable',
            title = 'No Compatible Processor Found',
            message = str( self ),
            source = self.source,
            genus = self.genus if not __.is_absent( self.genus ) else None,
            suggestion = (
                'Verify the URL points to a supported documentation format.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders processor unavailability as Markdown lines for display. '''
        lines = [ "## Error: No Compatible Processor Found" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Verify the URL points to a supported "
            "documentation format." )
        if reveal_internals:
            lines.append( f"**Source:** {self.source}" )
            if not __.is_absent( self.genus ):
                lines.append( f"**Genus:** {self.genus}" )
            lines.append( "**Error Type:** processor_unavailable" )
        return tuple( lines )


class ProcessorInvalidity( Omnierror, TypeError ):
    ''' Processor has wrong type. '''

    def __init__( self, expected: str, actual: type ):
        message = f"Expected {expected}, got {actual}."
        self.expected_type = expected
        self.actual_type = actual
        super( ).__init__( message )


class RobotsTxtAccessFailure( Omnierror, RuntimeError ):
    ''' Robots.txt file access failure (network issue, not policy). '''

    def __init__( self, domain: str, cause: BaseException ):
        message = (
            f"Failed to access robots.txt at '{domain}' due to network issue: "
            f"{cause}" )
        self.domain = domain
        self.cause = cause
        super( ).__init__( message )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders robots.txt access failure as JSON-compatible dict. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'robots_txt_access_failure',
            title = 'Robots.txt Access Failure',
            message = str( self ),
            domain = self.domain,
            cause = str( self.cause ),
            suggestion = (
                'This is likely a temporary network issue or server '
                'configuration problem. The site content may still be '
                'accessible.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders robots.txt access failure as Markdown lines. '''
        lines = [ "## Error: Robots.txt Access Failure" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** This is likely a temporary network issue or "
            "server configuration problem. The site content may still be "
            "accessible." )
        if reveal_internals:
            lines.append( f"**Domain:** {self.domain}" )
            lines.append( f"**Cause:** {self.cause}" )
            lines.append( "**Error Type:** robots_txt_access_failure" )
        return tuple( lines )


class StructureIncompatibility( Omnierror, ValueError ):
    ''' Documentation structure incompatible with processor. '''

    def __init__( self, processor_name: str, source: str ):
        self.processor_name = processor_name
        self.source = source
        super( ).__init__(
            f"No content extracted by {processor_name} from {source}. "
            f"The documentation structure may be incompatible with "
            f"this processor." )


class StructureProcessFailure( Omnierror, RuntimeError ):
    ''' Structure processor failed to complete processing. '''

    def __init__( self, processor_name: str, source: str, cause: str ):
        self.processor_name = processor_name
        self.source = source
        super( ).__init__(
            f"Processor {processor_name} failed processing {source}. "
            f"Cause: {cause}" )


class ContentExtractFailure( StructureProcessFailure ):
    ''' Failed to extract meaningful content from documentation. '''

    def __init__(
        self,
        processor_name: str,
        source: str,
        meaningful_results: int,
        requested_objects: int,
    ):
        self.processor_name = processor_name
        self.source = source
        self.meaningful_results = meaningful_results
        self.requested_objects = requested_objects
        cause = (
            f"Got {meaningful_results} meaningful results from "
            f"{requested_objects} requested objects. "
            f"This may indicate incompatible theme or documentation "
            f"structure." )
        super( ).__init__( processor_name, source, cause )


class ContentIdInvalidity( Omnierror, ValueError ):
    ''' Content ID has invalid format or encoding. '''

    def __init__( self, content_id: str, cause: str ):
        self.content_id = content_id
        self.cause = cause
        super( ).__init__(
            f"Content ID '{content_id}' is invalid. {cause}" )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders content ID invalidity as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'content_id_invalid',
            title = 'Invalid Content ID Format',
            message = str( self ),
            content_id = self.content_id,
            cause = self.cause,
            suggestion = (
                'Verify the content ID was generated correctly and not '
                'corrupted during transmission.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders content ID invalidity as Markdown lines for display. '''
        lines = [ "## Error: Invalid Content ID Format" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Verify the content ID was generated correctly "
            "and not corrupted during transmission." )
        if reveal_internals:
            lines.append( f"**Content ID:** {self.content_id}" )
            lines.append( f"**Cause:** {self.cause}" )
            lines.append( "**Error Type:** content_id_invalid" )
        return tuple( lines )


class ContentIdLocationMismatch( Omnierror, ValueError ):
    ''' Content ID location does not match term query location. '''

    def __init__( self, content_id_location: str, term_location: str ):
        self.content_id_location = content_id_location
        self.term_location = term_location
        super( ).__init__(
            f"Content ID location '{content_id_location}' does not match "
            f"term location '{term_location}'" )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders content ID location mismatch as JSON-compatible dict. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'content_id_location_mismatch',
            title = 'Content ID Location Mismatch',
            message = str( self ),
            content_id_location = self.content_id_location,
            term_location = self.term_location,
            suggestion = (
                'Ensure the content ID was generated from the same location '
                'being queried, or use a content ID from the correct '
                'location.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders content ID location mismatch as Markdown lines. '''
        lines = [ "## Error: Content ID Location Mismatch" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Ensure the content ID was generated from the "
            "same location being queried, or use a content ID from the "
            "correct location." )
        if reveal_internals:
            lines.append(
                f"**Content ID Location:** {self.content_id_location}" )
            lines.append( f"**Term Location:** {self.term_location}" )
            lines.append( "**Error Type:** content_id_location_mismatch" )
        return tuple( lines )


class ContentIdObjectAbsence( Omnierror, ValueError ):
    ''' Object specified in content ID not found in location. '''

    def __init__( self, object_name: str, location: str ):
        self.object_name = object_name
        self.location = location
        super( ).__init__(
            f"Object '{object_name}' not found at location '{location}'" )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders content ID object absence as JSON-compatible dict. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = 'content_id_object_not_found',
            title = 'Content ID Object Not Found',
            message = str( self ),
            object_name = self.object_name,
            location = self.location,
            suggestion = (
                'Verify the object name exists at the location, or check '
                'if the object has been renamed or removed.' ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders content ID object absence as Markdown lines. '''
        lines = [ "## Error: Content ID Object Not Found" ]
        lines.append( f"**Message:** {self}" )
        lines.append(
            "**Suggestion:** Verify the object name exists at the location, "
            "or check if the object has been renamed or removed." )
        if reveal_internals:
            lines.append( f"**Object Name:** {self.object_name}" )
            lines.append( f"**Location:** {self.location}" )
            lines.append( "**Error Type:** content_id_object_not_found" )
        return tuple( lines )


class ThemeDetectFailure( StructureProcessFailure ):
    ''' Theme detection failed during processing. '''

    def __init__( self, processor_name: str, source: str, theme_error: str ):
        self.theme_error = theme_error
        super( ).__init__(
            processor_name, source, f"Theme detection failed: {theme_error}" )


class UrlImpermissibility( Omnierror, PermissionError ):
    ''' URL access blocked by robots.txt directive. '''

    def __init__( self, url: str, user_agent: str ):
        message = (
            f"URL '{url}' blocked by robots.txt for "
            f"user agent '{user_agent}'" )
        self.url = url
        self.user_agent = user_agent
        super( ).__init__( message )


class ContextInvalidity( Omnierror, TypeError ):
    ''' Invalid context type provided to operation. '''


