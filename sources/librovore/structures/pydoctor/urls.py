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


''' URL manipulation and normalization functions. '''


import urllib.parse as _urlparse

from urllib.parse import ParseResult as _Url

from . import __


def normalize_base_url( source: str ) -> _Url:
    ''' Extracts clean base documentation URL from any source. '''
    try: url = _urlparse.urlparse( source )
    except Exception as exc:
        raise __.InventoryUrlInvalidity( source ) from exc
    match url.scheme:
        case '':
            path = __.Path( source )
            if path.is_file( ) or ( not path.exists( ) and path.suffix ):
                path = path.parent
            url = _urlparse.urlparse( path.resolve( ).as_uri( ) )
        case 'http' | 'https' | 'file': pass
        case _: raise __.InventoryUrlInvalidity( source )
    path = url.path.rstrip( '/' )
    return _urlparse.ParseResult(
        scheme = url.scheme, netloc = url.netloc, path = path,
        params = '', query = '', fragment = '' )


def derive_documentation_url(
    base_url: _Url, object_uri: str
) -> _Url:
    ''' Derives documentation URL from base URL and object URI. '''
    # Pydoctor URIs are already relative paths like "module/class.html"
    new_path = f"{base_url.path}/{object_uri}"
    return base_url._replace( path = new_path )


def derive_index_url( base_url: _Url ) -> _Url:
    ''' Derives index.html URL from base URL. '''
    new_path = f"{base_url.path}/index.html"
    return base_url._replace( path = new_path )
