#!/usr/bin/env python3
# ruff: noqa: E501, C901, PLR0912, PLR0915
"""Comprehensive summary of all MkDocs theme patterns."""

import json
from collections import defaultdict

def main():
    with open('.auxiliary/scribbles/mkdocs-samples/analysis_results.json', 'r') as f:
        data = json.load(f)

    print("🔥 COMPREHENSIVE MKDOCS THEMES ANALYSIS 🔥")
    print("=" * 60)

    # Group by theme
    theme_data = defaultdict(list)
    for analysis in data:
        theme = analysis['theme']
        theme_data[theme].append(analysis)

    # 1. CODE BLOCK CONSISTENCY CHECK
    print("\n🎯 CODE BLOCK PATTERNS - MKDOCS ANALYSIS")
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

    # 2. MAIN CONTAINER ANALYSIS
    print("\n🎯 MAIN CONTENT CONTAINERS - THEME PATTERNS")
    print("-" * 50)

    container_patterns = {}
    for theme, analyses in theme_data.items():
        containers = defaultdict(int)

        for analysis in analyses:
            for container in analysis['sections']['main_containers']:
                key = f"{container['tag']}.{'.'.join(container['classes']) if container['classes'] else 'no-class'}"
                if container['role']:
                    key += f"[role={container['role']}]"
                containers[key] += 1

        if containers:
            container_patterns[theme] = dict(containers)

    for theme, patterns in container_patterns.items():
        print(f"\n📂 {theme.upper()}:")
        print(f"   Containers: {patterns}")

    # 3. NAVIGATION ANALYSIS
    print("\n🎯 NAVIGATION PATTERNS - THEME ANALYSIS")
    print("-" * 50)

    nav_patterns = {}
    for theme, analyses in theme_data.items():
        nav_elements = defaultdict(int)

        for analysis in analyses:
            for nav in analysis['sections']['navigation_patterns']:
                nav_key = f"{nav['tag']}.{'.'.join(nav['classes']) if nav['classes'] else 'no-class'}"
                nav_elements[nav_key] += 1

        if nav_elements:
            nav_patterns[theme] = dict(nav_elements)

    for theme, patterns in nav_patterns.items():
        print(f"\n🧭 {theme.upper()}:")
        for nav_pattern, count in patterns.items():
            print(f"   {nav_pattern}: {count}")

    # 4. LANGUAGE DETECTION ANALYSIS
    print("\n🎯 LANGUAGE DETECTION PATTERNS")
    print("-" * 50)

    print("\n🔍 CODE BLOCK LANGUAGE PATTERNS BY THEME:")

    for theme, analyses in theme_data.items():
        print(f"\n{theme.upper()}:")

        language_patterns = set()
        for analysis in analyses:
            for pattern in analysis['code_blocks']['syntax_patterns']:
                if 'language-' in pattern:
                    language_patterns.add(pattern)

        if language_patterns:
            print(f"  Language patterns: {sorted(language_patterns)}")
        else:
            print("  No explicit language patterns found")

    # 5. EXTRACTION STRATEGY RECOMMENDATIONS
    print("\n🚀 EXTRACTION STRATEGY RECOMMENDATIONS")
    print("=" * 60)

    print("\n1. CODE BLOCK LANGUAGE DETECTION:")
    print("   🔍 PATTERN DISCOVERY:")
    print("   ✅ Material Theme: Uses 'language-{lang}' CSS classes on code elements")
    print("   ✅ ReadTheDocs Theme: Uses 'language-{lang}' CSS classes on code elements")
    print("   ✅ Default Theme: Mixed patterns, some use 'language-{lang}' classes")
    print("   ⚠️  INCONSISTENT: Unlike Sphinx, MkDocs language detection varies by theme")

    print("\n2. MAIN CONTENT EXTRACTION:")
    print("   📋 PRIORITY ORDER BY THEME:")

    extraction_priorities = {
        'material': ['main.md-main', 'article.md-content__inner', 'div.md-content'],
        'readthedocs': ['div.col-md-9[role="main"]', 'div.container'],
        'mkdocs_default': ['div.col-md-9[role="main"]', 'div.container'],
    }

    for theme, selectors in extraction_priorities.items():
        print(f"   {theme}: {selectors}")

    print("\n3. NAVIGATION CLEANUP:")
    cleanup_patterns = {
        'material': ['nav.md-nav', 'div.md-sidebar', 'nav.md-header__inner'],
        'readthedocs': ['div.navbar', 'ul.nav.navbar-nav'],
        'mkdocs_default': ['div.navbar', 'ul.nav.navbar-nav'],
    }

    for theme, cleanup in cleanup_patterns.items():
        print(f"   {theme}: {cleanup}")

    print("\n4. CODE BLOCK EXTRACTION:")
    print("   ✅ UNIVERSAL SELECTOR: '.highlight' (consistent across all themes)")
    print("   ✅ LANGUAGE DETECTION: Check for 'language-{lang}' CSS classes")
    print("   ⚠️  FALLBACK: Some themes don't use explicit language classes")

    # 6. COMPARISON WITH SPHINX
    print("\n🎯 MKDOCS vs SPHINX COMPARISON")
    print("-" * 50)

    print("\n📊 KEY DIFFERENCES:")
    print("✅ Code Blocks:")
    print("   • MkDocs: Uses '.highlight' container (same as Sphinx)")
    print("   • MkDocs: Language detection via 'language-{lang}' classes")
    print("   • Sphinx: Language detection via 'highlight-{lang}' parent classes")
    print("   • VERDICT: Different but predictable patterns")

    print("\n✅ Main Content:")
    print("   • MkDocs Material: 'main.md-main' > 'article.md-content__inner'")
    print("   • MkDocs ReadTheDocs: 'div.col-md-9[role=\"main\"]'")
    print("   • Sphinx: Theme-specific but more standardized")
    print("   • VERDICT: MkDocs has clear theme-specific patterns")

    print("\n✅ Navigation:")
    print("   • MkDocs: Heavily theme-dependent navigation patterns")
    print("   • Sphinx: More consistent navigation patterns")
    print("   • VERDICT: MkDocs requires more theme-aware cleanup")

    print("\n🎯 FINAL VERDICT: MKDOCS THEMES HAVE CLEAR PATTERNS!")
    print("✅ Code blocks: Consistent '.highlight' container, theme-specific language detection")
    print("✅ Content extraction: Clear theme-specific main content selectors")
    print("✅ Navigation cleanup: Theme-aware patterns identified")
    print("✅ Ready for librovore implementation!")

if __name__ == '__main__':
    main()