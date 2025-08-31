ComparisonResult        # unused variable
NominativeArguments     # unused variable
PositionalArguments     # unused variable
package_name            # unused variable

# --- BEGIN: Injected by Copier ---
Omnierror              # unused base exception class for derivation
# --- END: Injected by Copier ---

# CLI dataclass fields (used via tyro argument parsing)
silence                 # DisplayTarget field for --quiet/--silent CLI args

# Enum values (part of IntFlag interface, used via Documentation)
Signature               # InventoryQueryDetails enum value
Summary                 # InventoryQueryDetails enum value

# Type aliases (used in function signatures)
GroupByArgument         # CLI and server function parameter type
UrlPatternResult        # URL pattern matching result type

# Type collections (used in type annotations and exports)
ContentDocuments        # Type alias for content document collections
InventoryObjects        # Type alias for inventory object collections  
SearchResults           # Type alias for search result collections
DetectionsResultUnion   # Type alias for detection result unions

# Exception hierarchy (exported via star imports, part of API)
ExtensionCacheFailure       # Extension cache operation exceptions
ExtensionRegisterFailure    # Extension registration exceptions
ExtensionVersionConflict    # Extension version conflict exceptions
InventoryFilterInvalidity   # Inventory filter validation exceptions
ProcessorGenusInvalidity    # Processor genus validation exceptions
ProcessorInvalidity         # Processor validation exceptions
StructureIncompatibility    # Structure compatibility exceptions  
ContentExtractFailure       # Content extraction exceptions
ThemeDetectFailure          # Theme detection exceptions

# Exception attributes (part of exception interface)
expected_type           # ProcessorInvalidity exception attribute
actual_type             # ProcessorInvalidity exception attribute


# Extension manager exports (public API via xtnsmgr module)
cleanup_expired_caches              # Cache cleanup utility function
get_module_info                     # Module introspection utility
invalidate                          # Cache invalidation function
list_registered_processors          # Registry inspection utility

# Abstract method implementations (protocol compliance)
from_source                         # Detection.from_source implementations across subclasses

# Data structures for future use (preserved for upcoming refactoring)
DetectionsForLocation               # Location-specific detection grouping

# Phase 2->4 transition: Union types unused after Phase 2, will be removed in Phase 4
ContentResult                       # Union type for content query results (Phase 4 cleanup)
InventoryResult                     # Union type for inventory query results (Phase 4 cleanup)
ProcessorsSurveyResultUnion         # Union type for processor survey results (Phase 4 cleanup)
