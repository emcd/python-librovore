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


''' Application state management. '''


import appcore.cli as _appcore_cli

from . import __
from . import cacheproxy as _cacheproxy
from . import interfaces as _interfaces


class DisplayOptions( _appcore_cli.DisplayOptions ):
    ''' Consolidated display configuration for CLI output. '''

    format: _interfaces.DisplayFormat = _interfaces.DisplayFormat.Markdown


class Globals( __.Globals ):
    ''' Librovore-specific global state container.

        Extends appcore.Globals with cache instances configured from
        application configuration.
    '''

    display: DisplayOptions = __.dcls.field( default_factory = DisplayOptions )
    content_cache: _cacheproxy.ContentCache
    probe_cache: _cacheproxy.ProbeCache
    robots_cache: _cacheproxy.RobotsCache
