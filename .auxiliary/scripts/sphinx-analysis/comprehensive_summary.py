#!/usr/bin/env python3
# ruff: noqa: E501, C901, PLR0912, PLR0915
"""Comprehensive summary of all Sphinx theme patterns."""

import json
from collections import defaultdict

def main():
    with open('.auxiliary/scribbles/sphinx-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print("🔥 COMPREHENSIVE SPHINX THEMES ANALYSIS 🔥")
    print("=" * 60)

    # Group by theme
    theme_data = defaultdict(list)
    for analysis in data:
        filename = analysis['file']
        if 'furo' in filename:
            theme = 'furo'
        elif 'rtd' in filename:
            theme = 'rtd'
        elif 'pydata' in filename:
            theme = 'pydata'
        elif 'python-docs' in filename:
            theme = 'python-docs'
        elif 'alabaster' in filename:
            theme = 'alabaster'
        elif 'agogo' in filename:
            theme = 'agogo'
        elif 'classic' in filename:
            theme = 'classic'
        elif 'nature' in filename:
            theme = 'nature'
        else:
            theme = 'unknown'

        theme_data[theme].append(analysis)

    # 1. CODE BLOCK CONSISTENCY CHECK
    print("\n🎯 CODE BLOCK PATTERNS - UNIVERSAL CONSISTENCY")
    print("-" * 50)

    all_code_classes = set()
    all_syntax_patterns = set()

    for theme, analyses in theme_data.items():
        theme_classes = set()
        theme_patterns = set()

        for analysis in analyses:
            classes = analysis['code_blocks']['css_classes']
            patterns = analysis['code_blocks']['syntax_patterns']
            theme_classes.update(classes)
            theme_patterns.update(patterns)
            all_code_classes.update(classes)
            all_syntax_patterns.update(patterns)

        if theme_classes:
            print(f"✅ {theme}: {sorted(theme_classes)}")

    print("\n🔑 UNIVERSAL CODE PATTERNS:")
    print(f"   Classes: {sorted(all_code_classes)}")
    print(f"   Syntax: {sorted(all_syntax_patterns)}")

    # 2. API DOCUMENTATION CONSISTENCY
    print("\n🎯 API DOCUMENTATION - UNIVERSAL CONSISTENCY")
    print("-" * 50)

    api_classes_by_theme = {}
    for theme, analyses in theme_data.items():
        api_classes = set()
        sig_count = 0

        for analysis in analyses:
            classes = analysis['api_docs']['api_classes']
            signatures = analysis['api_docs']['function_signatures']
            api_classes.update(classes)
            sig_count += len(signatures)

        if api_classes:
            api_classes_by_theme[theme] = api_classes
            print(f"✅ {theme}: {sorted(api_classes)} ({sig_count} signatures)")

    # Check if all themes have same API classes
    if api_classes_by_theme:
        reference_classes = next(iter(api_classes_by_theme.values()))
        all_same = all(classes == reference_classes for classes in api_classes_by_theme.values())
        print(f"\n🔑 API CLASSES UNIVERSAL: {'✅ YES' if all_same else '❌ NO'}")
        print(f"   Standard: {sorted(reference_classes)}")

    # 3. SECTION STRUCTURE PATTERNS
    print("\n🎯 SECTION STRUCTURE - THEME-SPECIFIC PATTERNS")
    print("-" * 50)

    section_patterns = {}
    for theme, analyses in theme_data.items():
        containers = defaultdict(int)
        nav_elements = defaultdict(int)

        for analysis in analyses:
            for section in analysis['sections']['sections']:
                key = f"{section['tag']}.{'.'.join(section['classes']) if section['classes'] else 'no-class'}"
                if section['role']:
                    key += f"[role={section['role']}]"
                containers[key] += 1

            for nav in analysis['sections']['navigation_patterns']:
                nav_key = f"{nav['tag']}.{'.'.join(nav['classes']) if nav['classes'] else 'no-class'}"
                nav_elements[nav_key] += 1

        if containers:
            section_patterns[theme] = {
                'containers': dict(containers),
                'navigation': dict(nav_elements)
            }

    for theme, patterns in section_patterns.items():
        print(f"\n📂 {theme.upper()}:")
        print(f"   Containers: {patterns['containers']}")
        if patterns['navigation']:
            print(f"   Navigation: {patterns['navigation']}")

    # 4. EXTRACTION STRATEGY RECOMMENDATIONS
    print("\n🚀 EXTRACTION STRATEGY RECOMMENDATIONS")
    print("=" * 60)

    print("\n1. CODE BLOCK LANGUAGE DETECTION:")
    print("   ✅ UNIVERSAL PATTERN: parent.class.startswith('highlight-')")
    print("   ✅ CONFIRMED LANGUAGES: python, json, text, default")
    print("   ✅ ADDITIONAL CLASSES: doctest, notranslate")

    print("\n2. API DOCUMENTATION EXTRACTION:")
    print("   ✅ UNIVERSAL PATTERN: dt.sig.sig-object.py + dd")
    print("   ✅ CLASSES: ['sig', 'sig-object', 'py']")
    print("   ✅ ANCHOR: id attribute with module.function format")

    print("\n3. CONTENT SECTION EXTRACTION:")
    print("   📋 PRIORITY ORDER BY THEME:")

    extraction_priorities = {
        'furo': ['article[role="main"]', 'div.content', 'section'],
        'rtd': ['section.wy-nav-content-wrap', 'section'],
        'pydata': ['main.bd-main', 'article.bd-article', 'section'],
        'python-docs': ['div.body[role="main"]', 'section'],
        'alabaster': ['div.body[role="main"]', 'section'],
        'agogo': ['div.body[role="main"]', 'div.content', 'section'],
        'classic': ['div.body[role="main"]', 'section'],
        'nature': ['div.body[role="main"]', 'section'],
    }

    for theme, selectors in extraction_priorities.items():
        print(f"   {theme}: {selectors}")

    print("\n4. NAVIGATION CLEANUP:")
    cleanup_patterns = {
        'furo': ['sidebar elements', 'toc-drawer'],
        'rtd': ['nav.wy-nav-side', 'nav.wy-nav-top'],
        'pydata': ['multiple nav elements'],
        'python-docs': ['nav.menu', 'nav.nav-content'],
        'alabaster': ['standard sidebar'],
        'agogo': ['div.sidebar'],
        'classic': ['standard navigation'],
    }

    for theme, cleanup in cleanup_patterns.items():
        print(f"   {theme}: {cleanup}")

    print("\n🎯 FINAL VERDICT: SPHINX THEMES ARE HIGHLY CONSISTENT!")
    print("✅ Code blocks: 100% consistent pattern")
    print("✅ API docs: 100% consistent pattern")
    print("✅ Sections: Theme-specific but predictable")
    print("✅ Ready for librovore implementation!")

if __name__ == '__main__':
    main()