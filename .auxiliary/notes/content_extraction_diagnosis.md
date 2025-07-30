# Content Extraction Issue Diagnosis

## Problem Summary
Content extraction fails for certain Sphinx sites (like pytest) returning empty signatures, descriptions, and content snippets, while working perfectly for others (like Python docs).

## Root Cause Analysis

### Current Algorithm Flow:
1. `_extract_object_documentation()` builds URL with anchor fragment
2. `parse_documentation_html()` finds main content container using theme
3. Searches for element with `id = element_id` (the anchor)
4. If element found, extracts content based on element type (`dt`, `section`, or fallback)
5. If element NOT found, returns `{ 'error': '...' }` 
6. Error results are filtered out, causing empty responses

### Failing Case (pytest):
- **URL**: `https://docs.pytest.org/en/latest/reference/fixtures.html#fixture`  
- **Anchor**: `fixture`
- **HTML Structure**:
  ```html
  <section id="fixtures-reference">
    <span id="fixture"></span>
    <h1>Fixtures reference</h1>
    <p>Content goes here...</p>
  </section>
  ```
- **Issue**: Element `<span id="fixture">` is found, but it's a `<span>` (not `dt` or `section`)
- **Fallback**: Code uses `element.get_text(strip=True)` which returns empty string for empty span
- **Result**: Empty signature, empty description

### Working Case (Python docs):
- **URL**: `https://docs.python.org/3/library/functions.html#print`
- **Anchor**: `print`  
- **HTML Structure**:
  ```html
  <dt id="print">
    <code>print(*objects, ...)</code>
  </dt>
  <dd>
    <p>Print objects to the text stream...</p>
  </dd>
  ```
- **Success**: Element `<dt id="print">` is found and has proper dt/dd structure

## Proposed Fix

### Strategy: Smarter Element Context Detection

Instead of only handling the direct anchor element, we should:

1. **Find the anchor element** (current behavior)
2. **Analyze the context** around the anchor to find the actual content
3. **Extract content from the appropriate container** (section, heading, etc.)

### Implementation Plan:

#### **1. Enhanced Element Detection**
```python
def _extract_content_from_anchor(container, element_id):
    ''' Extracts content using smart context detection around anchor. '''
    element = container.find(id=element_id)
    if not element:
        return {'error': f"Object '{element_id}' not found in page"}
    
    # Current logic for dt/dd pairs (Python docs style)  
    if element.name == 'dt':
        return _extract_dt_content(element)
    
    # Enhanced logic for section-based content (pytest/Furo style)
    elif element.name in ('span', 'a'):  # Anchor elements
        return _extract_anchor_context_content(element)
    
    # Current fallback for section elements
    elif element.name == 'section':
        return _extract_section_content(element)
    
    # Enhanced fallback 
    else:
        return _extract_generic_content(element)
```

#### **2. New Context Extraction Functions**
```python
def _extract_anchor_context_content(element):
    ''' Extracts content from anchor element context. '''
    # Strategy 1: Find parent section and extract from there
    parent_section = element.find_parent('section')
    if parent_section:
        return _extract_section_content_enhanced(parent_section, element)
    
    # Strategy 2: Find following sibling heading and content
    next_heading = element.find_next_sibling(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if next_heading:
        return _extract_heading_content(next_heading)
    
    # Strategy 3: Look for content in nearby elements
    return _extract_nearby_content(element)

def _extract_section_content_enhanced(section, anchor_element):
    ''' Enhanced section extraction with anchor awareness. '''
    # Find the main heading (signature)
    heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    signature = heading.get_text(strip=True) if heading else ''
    
    # Find description content (first paragraph after heading/anchor)
    content_start = anchor_element.next_sibling or heading
    description_element = _find_next_content_element(content_start)
    description = description_element.get_text(strip=True) if description_element else ''
    
    return signature, description

def _find_next_content_element(start_element):
    ''' Finds the next meaningful content element (p, div, etc.). '''
    current = start_element
    while current:
        current = current.next_sibling
        if hasattr(current, 'name') and current.name in ('p', 'div', 'dl', 'ul', 'ol'):
            return current
    return None
```

#### **3. Enhanced Theme Support**
The Furo theme (used by pytest) has different patterns than the classic Python docs theme:

- **Python docs**: `<dt id="anchor">` + `<dd>` pairs
- **Furo theme**: `<span id="anchor">` + section content  
- **RTD theme**: Various patterns with sections and headings

We should enhance theme detection to handle these patterns better.

## Benefits of This Approach

1. **Broader compatibility** - Handles multiple Sphinx theme patterns
2. **Robust fallbacks** - Multiple strategies for finding content
3. **Maintains performance** - Still uses efficient DOM traversal
4. **Backward compatible** - Existing dt/dd extraction still works

## Testing Strategy

1. **Test with failing sites**: pytest, any other Furo-based sites
2. **Regression test with working sites**: Python docs, RTD theme sites  
3. **Edge cases**: Sites with unusual anchor patterns
4. **Theme coverage**: Test major Sphinx themes (Furo, RTD, Alabaster, etc.)

## Implementation Phases

### Phase 1: Core Enhancement
- Add `_extract_anchor_context_content()` function
- Update `parse_documentation_html()` to handle `span` and `a` elements  
- Basic section context extraction

### Phase 2: Advanced Context Detection  
- Implement `_extract_section_content_enhanced()`
- Add sibling heading detection
- Improve nearby content detection

### Phase 3: Theme-Specific Optimizations
- Add Furo theme-specific extraction patterns
- Enhance theme detection accuracy
- Add support for other modern themes

## Risk Assessment

**Low Risk**: This is primarily adding new code paths while preserving existing working functionality. The dt/dd extraction that works for Python docs remains unchanged.

**Mitigation**: Extensive testing with both working and failing sites to ensure no regressions.