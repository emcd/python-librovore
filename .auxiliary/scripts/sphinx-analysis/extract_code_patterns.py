#!/usr/bin/env python3
# ruff: noqa: E501
"""Extract and display code block analysis results."""

import json

def main():
    with open('.auxiliary/scribbles/sphinx-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print('=== CODE BLOCK ANALYSIS ===')
    for analysis in data:
        if analysis['code_blocks']['code_blocks']:
            print(f"\n--- {analysis['file']} ---")
            for i, block in enumerate(analysis['code_blocks']['code_blocks'][:3]):  # First 3 blocks
                print(f"\nBlock {i+1}:")
                print(f"  Selector: {block['selector']}")
                print(f"  Classes: {block['classes']}")
                print(f"  Parent classes: {block['parent_classes']}")
                print(f"  Attributes: {block['attributes']}")
                print(f"  Content preview: {block['content_preview'][:80]}...")

            print(f"\n  All syntax patterns found: {analysis['code_blocks']['syntax_patterns']}")
            print(f"  All CSS classes: {sorted(analysis['code_blocks']['css_classes'])}")

    print('\n=== API DOCUMENTATION ANALYSIS ===')
    for analysis in data:
        if analysis['api_docs']['function_signatures']:
            print(f"\n--- {analysis['file']} ---")
            print(f"Function signatures found: {len(analysis['api_docs']['function_signatures'])}")

            # Show first signature as example
            sig = analysis['api_docs']['function_signatures'][0]
            print("  Example signature:")
            print(f"    DT classes: {sig['dt_classes']}")
            print(f"    DT text: {sig['dt_text'][:100]}...")
            print(f"    DD preview: {sig['dd_preview'][:100]}...")

            print(f"  All API classes: {sorted(analysis['api_docs']['api_classes'])}")

if __name__ == '__main__':
    main()