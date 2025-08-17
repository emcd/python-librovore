.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
002. Search Architecture Separation
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

The system requires comprehensive search capabilities across multiple documentation formats with different structural characteristics. The original design had duplicate search logic in each processor, leading to:

- **Code duplication** across Sphinx and MkDocs processors
- **Inconsistent search behavior** between different documentation formats
- **Maintenance overhead** when updating search algorithms or adding new match modes
- **Coupling** between search logic and format-specific data extraction

Key forces driving this decision:

- Search quality should be consistent regardless of documentation format
- Adding new processors should not require reimplementing search algorithms
- Search improvements should benefit all supported formats simultaneously  
- Format-specific knowledge should remain in processors while search logic is universal

The system needs to support multiple search modes:
- Exact string matching for precise queries
- Regex pattern matching for complex searches
- Fuzzy matching with configurable thresholds for approximate searches

Decision
===============================================================================

Implement a layered search architecture with clear separation between universal search logic and processor-specific data extraction:

**Universal Search Layer (search.py):**
- Centralized search algorithms using rapidfuzz for fuzzy matching
- Support for exact, regex, and fuzzy matching modes with unified interface
- Consistent scoring and ranking algorithms across all processors
- Structured SearchResult objects with match metadata and scoring

**Processor Responsibility Separation:**
- Processors handle format-specific data extraction and filtering
- Processors apply domain/role/priority filters using format-specific knowledge
- Universal search layer applies name matching and ranking
- Clear handoff points between extraction and search phases

**Search Flow Architecture:**
1. Functions layer receives user query with search parameters
2. Processor layer extracts and filters objects using format-specific logic  
3. Universal search layer applies name matching via ``search.filter_by_name()``
4. Processor layer fetches full documentation content for top candidates
5. Functions layer formats and returns results with consistent structure

Alternatives
===============================================================================

**Alternative 1: Processor-Specific Search Implementations**
- Rejected because it leads to code duplication and inconsistent behavior
- Would require each new processor to reimplement search algorithms
- Makes it difficult to improve search quality across all formats
- Results in maintenance overhead when updating search logic

**Alternative 2: Search-Specific Processor Wrappers**
- Considered but rejected due to added complexity
- Would create additional abstraction layer without clear benefits
- Could lead to unclear responsibility boundaries
- Doesn't address the core duplication issue

**Alternative 3: Hybrid Search with Format-Specific Extensions**
- Rejected as over-engineered for current requirements
- Would allow format-specific search enhancements but adds complexity
- Could be reconsidered if strong format-specific search needs emerge

**Alternative 4: External Search Service**
- Rejected as inappropriate for the deployment model
- Would require additional infrastructure and network dependencies
- Conflicts with goal of standalone operation

Consequences
===============================================================================

**Positive Consequences:**

- **Consistency**: Identical search behavior across all documentation formats
- **Maintainability**: Single location for search algorithm improvements
- **Extensibility**: New processors get full search capabilities automatically
- **Performance**: Optimized search algorithms benefit all formats
- **Quality**: Centralized scoring enables sophisticated relevance ranking

**Negative Consequences:**

- **Limited format-specific optimization**: Cannot easily customize search for format characteristics
- **Abstraction overhead**: Additional layer between processors and search logic
- **Testing complexity**: Must verify search behavior across all processor types

**Implementation Impacts:**

- Processors must implement consistent data extraction interfaces
- Search layer must handle varying object metadata formats
- Functions layer coordinates between processors and search components
- Result formatting must accommodate different processor output structures

**Migration Benefits:**

- Eliminated duplicate search code from existing processors
- Unified search interface simplifies adding new match modes
- Consistent API enables easier testing and validation
- Improved search quality through dedicated optimization focus

**Future Flexibility:**

- Architecture supports adding new search modes without processor changes
- Enables sophisticated ranking algorithms based on multiple factors
- Allows for search analytics and optimization without format coupling
- Provides foundation for potential machine learning enhanced search