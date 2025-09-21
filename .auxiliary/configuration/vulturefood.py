ComparisonResult        # unused variable
NominativeArguments     # unused variable
PositionalArguments     # unused variable
package_name            # unused variable

# --- BEGIN: Injected by Copier ---
Omnierror              # unused base exception class for derivation
# --- END: Injected by Copier ---

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

# Universal pattern helper functions (part of converter API)
convert_code_block_to_markdown           # Code block converter function
html_to_markdown_sphinx                  # Sphinx HTML to markdown converter function
_extract_description_with_strategy       # Sphinx extraction strategy function

# Phase 2 capability-based architecture (being implemented)
StructureProcessorCapabilities          # Capability advertisement class for structure processors
content_extraction_features             # Attribute of StructureProcessorCapabilities
get_confidence_for_type                  # Method of StructureProcessorCapabilities
supports_inventory_type                  # Method of StructureProcessorCapabilities
can_process_inventory_type               # Method of StructureDetection base class
_filter_objects_by_structure_capabilities # Helper function for capability filtering
ContentExtractionFeature                # Enum for content extraction capability features
Signatures                               # ContentExtractionFeature enum value
Descriptions                             # ContentExtractionFeature enum value
Arguments                                # ContentExtractionFeature enum value
Returns                                  # ContentExtractionFeature enum value
Attributes                               # ContentExtractionFeature enum value
CodeExamples                             # ContentExtractionFeature enum value
CrossReferences                          # ContentExtractionFeature enum value
Navigation                               # ContentExtractionFeature enum value

