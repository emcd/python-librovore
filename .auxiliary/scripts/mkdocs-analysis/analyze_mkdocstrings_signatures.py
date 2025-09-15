#!/usr/bin/env python3
# ruff: noqa: E501, C901, PLR0915
"""
Detailed analysis of mkdocstrings signature patterns.
Focus on finding signature classes similar to Sphinx's dt.sig.sig-object.py pattern.
"""

from bs4 import BeautifulSoup
from pathlib import Path

def analyze_mkdocstrings_signatures(soup, file_path):
    """Analyze mkdocstrings for function/class signature patterns."""
    results = {
        'file': str(file_path),
        'signatures': [],
        'signature_patterns': [],
        'heading_patterns': [],
        'id_patterns': [],
    }

    # Look for elements that might contain signatures
    signature_candidates = [
        # Direct signature selectors
        '[id*="function"]', '[id*="class"]', '[id*="method"]',
        # Common mkdocstrings patterns
        '.doc-heading', '.doc-signature', '.signature',
        # Heading elements that might be signatures
        'h1[id]', 'h2[id]', 'h3[id]', 'h4[id]', 'h5[id]', 'h6[id]',
        # Elements with specific data attributes
        '[data-mkdocs]', '[data-object]',
        # Any element with function-like text
    ]

    for selector in signature_candidates:
        elements = soup.select(selector)
        for element in elements:
            element_text = element.get_text().strip()

            # Check if this looks like a function/class signature
            if any(keyword in element_text.lower() for keyword in ['def ', 'class ', 'function', 'method', '(', ')']):
                signature_info = {
                    'selector': selector,
                    'tag': element.name,
                    'classes': list(element.get('class', [])),
                    'id': element.get('id'),
                    'text': element_text[:200],  # First 200 chars
                    'attributes': dict(element.attrs),
                    'parent_tag': element.parent.name if element.parent else None,
                    'parent_classes': list(element.parent.get('class', [])) if element.parent else [],
                    'has_code_child': len(element.find_all('code')) > 0,
                    'has_pre_child': len(element.find_all('pre')) > 0,
                }

                results['signatures'].append(signature_info)

    # Look for specific heading patterns with IDs
    headings_with_ids = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], id=True)
    for heading in headings_with_ids:
        heading_id = heading.get('id', '')
        heading_text = heading.get_text().strip()

        if any(indicator in heading_id.lower() for indicator in ['function', 'class', 'method']) or \
           any(keyword in heading_text.lower() for keyword in ['def ', 'class ', 'function', 'method']):

            heading_info = {
                'tag': heading.name,
                'id': heading_id,
                'text': heading_text[:200],
                'classes': list(heading.get('class', [])),
                'parent_classes': list(heading.parent.get('class', [])) if heading.parent else [],
                'next_sibling_tag': heading.find_next_sibling().name if heading.find_next_sibling() else None,
            }
            results['heading_patterns'].append(heading_info)

    # Look for ID patterns that might indicate signatures
    all_elements_with_ids = soup.find_all(id=True)
    for element in all_elements_with_ids:
        element_id = element.get('id', '')
        if any(pattern in element_id.lower() for pattern in ['function', 'class', 'method', '.', '__']):
            id_info = {
                'tag': element.name,
                'id': element_id,
                'classes': list(element.get('class', [])),
                'text_preview': element.get_text()[:100].replace('\n', ' '),
            }
            results['id_patterns'].append(id_info)

    return results

def main():
    """Analyze mkdocstrings samples for signature patterns."""
    samples_dir = Path('.auxiliary/scribbles/mkdocs-samples')

    # Focus on mkdocstrings files
    mkdocstrings_files = list(samples_dir.glob('*mkdocstrings*.html'))

    if not mkdocstrings_files:
        print("No mkdocstrings files found")
        return

    all_results = []

    for html_file in mkdocstrings_files:
        print(f"Analyzing mkdocstrings patterns in: {html_file}")

        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        results = analyze_mkdocstrings_signatures(soup, html_file)
        all_results.append(results)

    # Print detailed analysis
    print("\n" + "="*80)
    print("MKDOCSTRINGS SIGNATURE ANALYSIS")
    print("="*80)

    for results in all_results:
        print(f"\n📁 FILE: {results['file']}")
        print("-" * 60)

        if results['signatures']:
            print(f"\n🎯 FUNCTION/CLASS SIGNATURES FOUND: {len(results['signatures'])}")
            for i, sig in enumerate(results['signatures'][:5]):  # Show first 5
                print(f"\nSignature {i+1}:")
                print(f"  Selector: {sig['selector']}")
                print(f"  Tag: {sig['tag']}")
                print(f"  Classes: {sig['classes']}")
                print(f"  ID: {sig['id']}")
                print(f"  Text: {sig['text'][:100]}...")
                print(f"  Parent classes: {sig['parent_classes']}")
                print(f"  Has code child: {sig['has_code_child']}")

        if results['heading_patterns']:
            print(f"\n📋 HEADING PATTERNS WITH IDS: {len(results['heading_patterns'])}")
            for heading in results['heading_patterns'][:5]:  # Show first 5
                print(f"  {heading['tag']} id=\"{heading['id']}\": {heading['text'][:80]}...")

        if results['id_patterns']:
            print(f"\n🔗 RELEVANT ID PATTERNS: {len(results['id_patterns'])}")
            for pattern in results['id_patterns'][:10]:  # Show first 10
                print(f"  {pattern['tag']} id=\"{pattern['id']}\" classes={pattern['classes']}")

    # Summary analysis
    print("\n" + "="*80)
    print("SUMMARY: MKDOCSTRINGS vs SPHINX SIGNATURE PATTERNS")
    print("="*80)

    all_signature_classes = set()
    all_signature_tags = set()
    all_id_patterns = set()

    for results in all_results:
        for sig in results['signatures']:
            all_signature_classes.update(sig['classes'])
            all_signature_tags.add(sig['tag'])

        for pattern in results['id_patterns']:
            all_id_patterns.add(pattern['id'])

    print(f"\n🎯 SIGNATURE ELEMENT TAGS: {sorted(all_signature_tags)}")
    print(f"🎯 SIGNATURE CSS CLASSES: {sorted(all_signature_classes)}")
    print(f"🎯 SAMPLE ID PATTERNS: {sorted(list(all_id_patterns)[:10])}")

    print("\n📊 COMPARISON WITH SPHINX:")
    print("   Sphinx pattern: dt.sig.sig-object.py with id='module.function'")
    print("   mkdocstrings pattern: Need to determine from analysis above")

if __name__ == '__main__':
    main()