# vim: set fileencoding=utf-8:
# -*- coding: utf-8 -*-

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


''' JSON rendering functions for CLI output. '''


from . import __




def render_survey_processors_json( 
    result: dict[ str, __.typx.Any ]
) -> str:
    ''' Renders survey processors result as JSON. '''
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


