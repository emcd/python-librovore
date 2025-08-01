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


''' Interface for extension development. '''

# ruff: noqa: F401,F403,F405


from . import __

from .cacheproxy import probe_url, retrieve_url, retrieve_url_as_text
from .exceptions import *
from .interfaces import *
from .urls import *


InventoryProcessorsRegistry: __.typx.TypeAlias = (
    __.accret.ValidatorDictionary[ str, InventoryProcessor ] )
StructureProcessorsRegistry: __.typx.TypeAlias = (
    __.accret.ValidatorDictionary[ str, Processor ] )
ProcessorsRegistry: __.typx.TypeAlias = StructureProcessorsRegistry


def _inventory_validator( name: str, value: InventoryProcessor ) -> bool:
    return isinstance( value, InventoryProcessor )


def _structure_validator( name: str, value: Processor ) -> bool:
    return isinstance( value, Processor )


inventory_processors: InventoryProcessorsRegistry = (
    __.accret.ValidatorDictionary( _inventory_validator ) )
structure_processors: StructureProcessorsRegistry = (
    __.accret.ValidatorDictionary( _structure_validator ) )
processors: ProcessorsRegistry = structure_processors
