ComparisonResult        # unused variable
PositionalArguments     # unused variable
# --- BEGIN: Injected by Copier ---
Omnierror              # unused base exception class for derivation
# --- END: Injected by Copier ---

# Type aliases used in function signatures
GroupByArgument         # CLI and server function parameter type
UrlPatternResult        # URL pattern matching result type

# Type collections used in type annotations and exports
ContentDocuments        # Type alias for content document collections
InventoryObjects        # Type alias for inventory object collections
SearchResults           # Type alias for search result collections

# Exception hierarchy exported via star imports, part of public API
ContentExtractFailure       # Content extraction exceptions
ExtensionCacheFailure       # Extension cache operation exceptions
ExtensionRegisterFailure    # Extension registration exceptions
ExtensionVersionConflict    # Extension version conflict exceptions
InventoryFilterInvalidity   # Inventory filter validation exceptions
ProcessorGenusInvalidity    # Processor genus validation exceptions
ProcessorInvalidity         # Processor validation exceptions
StructureIncompatibility    # Structure compatibility exceptions
ThemeDetectFailure          # Theme detection exceptions

# Exception attributes part of exception interface
actual_type             # ProcessorInvalidity exception attribute
expected_type           # ProcessorInvalidity exception attribute

# Extension manager exports public API via xtnsmgr module
cleanup_expired_caches              # Cache cleanup utility function
get_module_info                     # Module introspection utility
invalidate                          # Cache invalidation function
list_registered_processors          # Registry inspection utility

# Abstract method implementations protocol compliance
from_source                         # Detection.from_source implementations across subclasses

# Data structures for future use preserved for upcoming refactoring
DetectionsForLocation               # Location-specific detection grouping

# Universal pattern helper functions part of converter API
_extract_description_with_strategy       # Sphinx extraction strategy function
html_to_markdown_sphinx                  # Sphinx HTML to markdown converter function

can_process_inventory_type              # Method of StructureDetection base class
content_extraction_features             # Attribute of StructureProcessorCapabilities
get_confidence_for_type                 # Method of StructureProcessorCapabilities
