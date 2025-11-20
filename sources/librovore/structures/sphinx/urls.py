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


from urllib.parse import ParseResult as _Url


def derive_documentation_url(
    base_url: _Url, object_uri: str, object_name: str
) -> _Url:
    ''' Derives documentation URL from base URL ParseResult and object URI. '''
    uri_with_name = object_uri.replace( '$', object_name )
    if '#' in uri_with_name:
        path_part, fragment_part = uri_with_name.split( '#', 1 )
        new_path = f"{base_url.path}/{path_part}"
        return base_url._replace( path = new_path, fragment = fragment_part )
    new_path = f"{base_url.path}/{uri_with_name}"
    return base_url._replace( path = new_path )


def derive_html_url( base_url: _Url ) -> _Url:
    ''' Derives index.html URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/index.html"
    return base_url._replace( path = new_path )


def derive_inventory_url( base_url: _Url ) -> _Url:
    ''' Derives objects.inv URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/objects.inv"
    return base_url._replace( path = new_path )


def derive_searchindex_url( base_url: _Url ) -> _Url:
    ''' Derives searchindex.js URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/searchindex.js"
    return base_url._replace( path = new_path )