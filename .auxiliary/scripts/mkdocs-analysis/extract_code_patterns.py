#!/usr/bin/env python3
# ruff: noqa: E501
"""Extract and display code block analysis results from MkDocs themes."""

import json

def main():
    with open('.auxiliary/scribbles/mkdocs-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print('=== MKDOCS CODE BLOCK ANALYSIS ===')
    for analysis in data:
        if analysis['code_blocks']['code_blocks']:
            print(f"\n--- {analysis['file']} ({analysis['theme']}) ---")
            for i, block in enumerate(analysis['code_blocks']['code_blocks'][:3]):  # First 3 blocks
                print(f"\nBlock {i+1}:")
                print(f"  Selector: {block['selector']}")
                print(f"  Classes: {block['classes']}")
                print(f"  Parent classes: {block['parent_classes']}")
                print(f"  Grandparent classes: {block['grandparent_classes']}")
                print(f"  Attributes: {block['attributes']}")
                print(f"  Content preview: {block['content_preview'][:80]}...")

            print(f"\n  All syntax patterns found: {analysis['code_blocks']['syntax_patterns']}")
            print(f"  All CSS classes: {sorted(analysis['code_blocks']['css_classes'])}")

    print('\n=== MKDOCS API DOCUMENTATION ANALYSIS ===')
    for analysis in data:
        if analysis['api_docs']['function_signatures']:
            print(f"\n--- {analysis['file']} ({analysis['theme']}) ---")
            print(f"Function signatures found: {len(analysis['api_docs']['function_signatures'])}")

            # Show first signature as example
            if analysis['api_docs']['function_signatures']:
                sig = analysis['api_docs']['function_signatures'][0]
                print("  Example signature:")
                print(f"    Classes: {sig['classes']}")
                print(f"    Text preview: {sig['text_preview'][:100]}...")
                print(f"    Has code: {sig['has_code']}")
                print(f"    Has pre: {sig['has_pre']}")

            print(f"  All API classes: {sorted(analysis['api_docs']['api_classes'])}")

if __name__ == '__main__':
    main()