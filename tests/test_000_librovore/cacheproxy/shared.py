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


''' Shared constants for cacheproxy tests. '''

from urllib.parse import ParseResult as Url

import httpx as _httpx


_URL_HTTP_TEST = Url(
    scheme = 'http', netloc = 'example.com', path = '/test',
    params = '', query = '', fragment = '' )
_URL_HTTP_MISSING = Url(
    scheme = 'http', netloc = 'example.com', path = '/missing',
    params = '', query = '', fragment = '' )
_URL_FILE_TEST = Url(
    scheme = 'file', netloc = '', path = '/test/file.txt',
    params = '', query = '', fragment = '' )
_URL_FILE_MISSING = Url(
    scheme = 'file', netloc = '', path = '/test/missing.txt',
    params = '', query = '', fragment = '' )
_URL_FTP_TEST = Url(
    scheme = 'ftp', netloc = 'example.com', path = '/test',
    params = '', query = '', fragment = '' )
_URL_EMPTY_SCHEME = Url(
    scheme = '', netloc = '', path = '/test/file.txt',
    params = '', query = '', fragment = '' )

_HEADERS_TEXT_PLAIN = _httpx.Headers( { 'content-type': 'text/plain' } )
_HEADERS_TEXT_HTML = _httpx.Headers( { 'content-type': 'text/html' } )
_HEADERS_APP_JSON = _httpx.Headers( {
    'content-type': 'application/json; charset=utf-8' } )
_HEADERS_IMAGE_PNG = _httpx.Headers( { 'content-type': 'image/png' } )
