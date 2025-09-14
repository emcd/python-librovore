#!/usr/bin/env python3
# ruff: noqa: E501
"""Analyze section structure for content extraction patterns."""

import json

def main():
    with open('.auxiliary/scribbles/sphinx-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print('=== SECTION STRUCTURE ANALYSIS ===')
    for analysis in data:
        print(f"\n--- {analysis['file']} ---")

        # Analyze heading patterns
        headings = analysis['sections']['headings']
        if headings:
            print(f"Headings found: {len(headings)}")
            for h in headings[:3]:  # First 3 headings
                print(f"  {h['level']}: '{h['text'][:50]}...' (classes: {h['classes']}, id: {h['id']})")

        # Analyze section containers
        sections = analysis['sections']['sections']
        print(f"Section containers: {len(sections)}")

        # Group by selector
        section_types = {}
        for section in sections:
            selector = section['selector']
            if selector not in section_types:
                section_types[selector] = []
            section_types[selector].append(section)

        for selector, secs in section_types.items():
            print(f"  {selector}: {len(secs)} instances")
            if secs:
                example = secs[0]
                print(f"    Example: tag={example['tag']}, classes={example['classes']}, "
                      f"role={example['role']}, {example['child_headings']} headings, "
                      f"{example['child_paragraphs']} paragraphs")

        # Navigation patterns
        nav_patterns = analysis['sections']['navigation_patterns']
        if nav_patterns:
            print(f"Navigation elements: {len(nav_patterns)}")
            for nav in nav_patterns[:2]:  # First 2 nav elements
                print(f"  {nav['selector']}: {nav['tag']} with {nav['links']} links (classes: {nav['classes']})")

if __name__ == '__main__':
    main()