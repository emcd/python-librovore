#!/usr/bin/env python3
# ruff: noqa: E501
"""Analyze MkDocs section structure and navigation patterns."""

import json
from collections import defaultdict

def main():
    with open('.auxiliary/scribbles/mkdocs-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print('=== MKDOCS SECTION STRUCTURE ANALYSIS ===')

    for analysis in data:
        theme = analysis['theme']
        print(f"\n--- {analysis['file']} ({theme}) ---")

        # Analyze headings
        headings = analysis['sections']['headings']
        if headings:
            print(f"Headings found: {len(headings)}")
            for h in headings[:3]:  # First 3 headings
                print(f"  {h['level']}: '{h['text'][:50]}...' (classes: {h['classes']}, id: {h['id']})")

        # Analyze main containers
        main_containers = analysis['sections']['main_containers']
        main_by_selector = defaultdict(list)
        for container in main_containers:
            main_by_selector[container['selector']].append(container)

        print(f"\nMain content containers: {len(main_containers)}")
        for selector, containers in main_by_selector.items():
            print(f"  {selector}: {len(containers)} found")
            if containers:
                example = containers[0]
                print(f"    Example: tag={example['tag']}, classes={example['classes']}, "
                      f"role={example['role']}, {example['child_headings']} headings, "
                      f"{example['child_paragraphs']} paragraphs, {example['child_code_blocks']} code blocks")

        # Analyze navigation patterns
        nav_patterns = analysis['sections']['navigation_patterns']
        nav_by_selector = defaultdict(list)
        for nav in nav_patterns:
            nav_by_selector[nav['selector']].append(nav)

        print(f"\nNavigation elements: {len(nav_patterns)}")
        for selector, navs in nav_by_selector.items():
            if navs:
                nav = navs[0]
                print(f"  {selector}: {nav['tag']} with {nav['links']} links (classes: {nav['classes']})")

if __name__ == '__main__':
    main()