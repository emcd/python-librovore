#!/usr/bin/env python3
# ruff: noqa: E501, PLR0915
"""
Targeted analysis of mkdocstrings autodoc signature patterns.
Found actual signature patterns in HTTPX file!
"""
from bs4 import BeautifulSoup
from pathlib import Path

def analyze_autodoc_signatures(soup, file_path):
    """Analyze mkdocstrings autodoc signature patterns."""
    results = {
        'file': str(file_path),
        'autodoc_signatures': [],
        'autodoc_containers': [],
        'signature_classes': set(),
    }

    # Look for autodoc containers
    autodoc_containers = soup.find_all(class_='autodoc')

    for container in autodoc_containers:
        container_info = {
            'classes': list(container.get('class', [])),
            'tag': container.name,
        }

        # Look for signature elements within autodoc container
        signature_elem = container.find(class_='autodoc-signature')
        if signature_elem:
            signature_info = {
                'signature_classes': list(signature_elem.get('class', [])),
                'signature_tag': signature_elem.name,
                'signature_text': signature_elem.get_text(),
                'signature_html': str(signature_elem)[:500],  # First 500 chars
                'child_elements': []
            }

            # Analyze child elements for detailed structure
            for child in signature_elem.find_all():
                child_info = {
                    'tag': child.name,
                    'classes': list(child.get('class', [])),
                    'text': child.get_text(),
                }
                signature_info['child_elements'].append(child_info)
                results['signature_classes'].update(child.get('class', []))

            container_info['signature'] = signature_info

        # Look for docstring
        docstring_elem = container.find(class_='autodoc-docstring')
        if docstring_elem:
            container_info['docstring'] = {
                'classes': list(docstring_elem.get('class', [])),
                'tag': docstring_elem.name,
                'text_preview': docstring_elem.get_text()[:200],
            }

        results['autodoc_containers'].append(container_info)

        # If this container has a signature, add it to signatures list
        if 'signature' in container_info:
            results['autodoc_signatures'].append(container_info)

    return results

def main():
    """Analyze mkdocstrings autodoc signatures."""
    samples_dir = Path('.auxiliary/scribbles/mkdocs-samples')

    # Look at all mkdocstrings files
    mkdocstrings_files = list(samples_dir.glob('*mkdocstrings*.html'))
    mkdocstrings_files.extend(list(samples_dir.glob('*griffe*.html')))

    all_results = []

    for html_file in mkdocstrings_files:
        print(f"Analyzing autodoc patterns in: {html_file}")

        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        results = analyze_autodoc_signatures(soup, html_file)
        if results['autodoc_signatures']:  # Only include files with signatures
            all_results.append(results)

    # Print detailed analysis
    print("\n" + "="*80)
    print("MKDOCSTRINGS AUTODOC SIGNATURE ANALYSIS")
    print("="*80)

    for results in all_results:
        print(f"\n📁 FILE: {results['file']}")
        print("-" * 60)

        print(f"\n🎯 AUTODOC SIGNATURES FOUND: {len(results['autodoc_signatures'])}")

        for i, container in enumerate(results['autodoc_signatures']):
            signature = container['signature']
            print(f"\nSignature {i+1}:")
            print(f"  Container classes: {container['classes']}")
            print(f"  Signature classes: {signature['signature_classes']}")
            print(f"  Signature text: {signature['signature_text'][:100]}...")
            print(f"  Child element classes: {[child['classes'] for child in signature['child_elements']]}")

            # Show HTML structure
            print("  HTML structure preview:")
            print(f"    {signature['signature_html'][:200]}...")

    # Summary analysis
    print("\n" + "="*80)
    print("SUMMARY: MKDOCSTRINGS SIGNATURE PATTERNS")
    print("="*80)

    all_signature_classes = set()
    all_container_classes = set()

    for results in all_results:
        all_signature_classes.update(results['signature_classes'])
        for container in results['autodoc_containers']:
            all_container_classes.update(container['classes'])

    print(f"\n🎯 AUTODOC CONTAINER CLASSES: {sorted(all_container_classes)}")
    print(f"🎯 SIGNATURE ELEMENT CLASSES: {sorted(all_signature_classes)}")

    print("\n📊 MKDOCSTRINGS SIGNATURE PATTERN:")
    print("   Container: div.autodoc")
    print("   Signature: div.autodoc-signature")
    print("   Docstring: div.autodoc-docstring")
    print("   Parameters: em.autodoc-param")
    print("   Punctuation: span.autodoc-punctuation")

    print("\n📊 COMPARISON WITH SPHINX:")
    print("   Sphinx: dt.sig.sig-object.py + dd")
    print("   mkdocstrings: div.autodoc > div.autodoc-signature + div.autodoc-docstring")
    print("   ✅ Both provide structured signature containers")
    print("   ✅ Both have identifiable CSS patterns")
    print("   ❗ Different HTML structure (div vs dt/dd)")

if __name__ == '__main__':
    main()