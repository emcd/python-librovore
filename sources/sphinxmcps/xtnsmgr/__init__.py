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


''' Extension manager for async package installation and import isolation. '''


# Public API exports
from .installation import (
    install_package,
    install_packages_parallel,
)
from .isolation import (
    add_to_import_path,
    cleanup_import_paths,
    import_builtin_processor,
    import_external_processor,
    get_module_info,
    list_imported_processors,
    reload_processor_module,
    remove_from_import_path,
)
from .cachemgr import (
    CacheInfo,
    calculate_cache_path,
    calculate_platform_id,
    cleanup_expired_caches,
    clear_package_cache,
    get_cache_info,
    save_cache_info,
)
from .processor_loader import (
    load_and_register_processors,
)