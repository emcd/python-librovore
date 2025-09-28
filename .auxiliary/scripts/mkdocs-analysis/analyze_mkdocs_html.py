#!/usr/bin/env python3
# ruff: noqa: E501, PLR2004, PLR0911
"""
Analyze downloaded MkDocs theme HTML files to extract structural patterns
for code blocks, sections, and API documentation.
"""

from bs4 import BeautifulSoup
import json
from pathlib import Path


def analyze_code_blocks(soup, theme_name):
    """Analyze code blocks for syntax identification patterns."""
    results = {
        'theme': theme_name,
        'code_blocks': [],
        'syntax_patterns': set(),
        'css_classes': set(),
    }

    # Look for various code block containers (MkDocs patterns)
    code_selectors = [
        '.codehilite', '.highlight', '.hljs', 'pre code',
        '.language-python', '.language-json', '.language-bash',
        'pre.prettyprint', '.code-block'
    ]

    for selector in code_selectors:
        blocks = soup.select(selector)
        for block in blocks:
            block_info = {
                'selector': selector,
                'classes': list(block.get('class', [])),
                'attributes': dict(block.attrs),
                'parent_classes': (list(block.parent.get('class', []))
                                  if block.parent else []),
                'grandparent_classes': (list(block.parent.parent.get('class', []))
                                       if block.parent and block.parent.parent else []),
                'content_preview': block.get_text()[:100].replace('\n', '\\n'),
            }

            # Look for language indicators in multiple places
            all_classes = (block_info['classes'] +
                          block_info['parent_classes'] +
                          block_info['grandparent_classes'])

            for cls in all_classes:
                lang_keywords = [
                    'python', 'javascript', 'json', 'bash', 'shell',
                    'yaml', 'html', 'css', 'cpp', 'java', 'go'
                ]
                if any(lang in cls.lower() for lang in lang_keywords):
                    results['syntax_patterns'].add(cls)
                results['css_classes'].add(cls)

            # Check data attributes for language info
            for attr, value in block.attrs.items():
                if 'lang' in attr.lower() or 'code' in attr.lower():
                    results['syntax_patterns'].add(f"{attr}={value}")

            results['code_blocks'].append(block_info)

    return results


def analyze_api_documentation(soup, theme_name):
    """Analyze API documentation structure (mkdocstrings patterns)."""
    results = {
        'theme': theme_name,
        'function_signatures': [],
        'api_containers': [],
        'api_classes': set(),
    }

    # Look for mkdocstrings patterns
    api_selectors = [
        '.doc', '.doc-object', '.doc-function', '.doc-class',
        '.py-', '[data-mkdocs]', '.mkdocstrings'
    ]

    for selector in api_selectors:
        elements = soup.select(selector)
        for element in elements:
            container_info = {
                'selector': selector,
                'classes': list(element.get('class', [])),
                'attributes': dict(element.attrs),
                'tag': element.name,
                'text_preview': element.get_text()[:200].replace('\n', ' '),
                'has_code': len(element.find_all('code')) > 0,
                'has_pre': len(element.find_all('pre')) > 0,
            }

            # Look for function signature patterns
            text = element.get_text()
            if (any(keyword in text for keyword in ['def ', 'class ', 'async ', '(', ')']) and
                len(text.split('\n')[0]) < 200):  # Likely a signature
                results['function_signatures'].append(container_info)

            results['api_containers'].append(container_info)

            # Collect CSS classes
            for cls in container_info['classes']:
                results['api_classes'].add(cls)

    return results


def analyze_section_structure(soup, theme_name):
    """Analyze section structure and heading patterns."""
    results = {
        'theme': theme_name,
        'headings': [],
        'sections': [],
        'navigation_patterns': [],
        'main_containers': [],
    }

    # Analyze heading structure
    for level in range(1, 7):
        headings = soup.find_all(f'h{level}')
        for heading in headings:
            heading_info = {
                'level': level,
                'text': heading.get_text().strip(),
                'classes': list(heading.get('class', [])),
                'id': heading.get('id'),
                'parent_tag': heading.parent.name if heading.parent else None,
                'parent_classes': (list(heading.parent.get('class', []))
                                  if heading.parent else []),
            }
            results['headings'].append(heading_info)

    # Analyze main content containers (MkDocs specific)
    main_selectors = [
        'main', 'article', '.md-main', '.md-content', '.md-content__inner',
        '.wy-nav-content', '.wy-nav-content-wrap', '.rst-content',
        '.col-md-9', '.bs-content', '.container', '.content'
    ]

    for selector in main_selectors:
        containers = soup.select(selector)
        for container in containers:
            container_info = {
                'tag': container.name,
                'selector': selector,
                'classes': list(container.get('class', [])),
                'id': container.get('id'),
                'role': container.get('role'),
                'child_headings': len(container.find_all(
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                )),
                'child_paragraphs': len(container.find_all('p')),
                'child_code_blocks': len(container.select('.codehilite, .highlight, pre code')),
            }
            results['main_containers'].append(container_info)

    # Analyze section containers
    section_selectors = [
        'section', '.section', 'div.section', 'article.section'
    ]

    for selector in section_selectors:
        sections = soup.select(selector)
        for section in sections:
            section_info = {
                'tag': section.name,
                'selector': selector,
                'classes': list(section.get('class', [])),
                'id': section.get('id'),
                'role': section.get('role'),
                'child_headings': len(section.find_all(
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                )),
                'child_paragraphs': len(section.find_all('p')),
            }
            results['sections'].append(section_info)

    # Analyze navigation patterns (MkDocs specific)
    nav_selectors = [
        'nav', '.md-nav', '.md-sidebar', '.wy-nav-side', '.wy-menu',
        '.navbar', '.nav', '.toc', '.navigation', '.sidebar'
    ]

    for selector in nav_selectors:
        navs = soup.select(selector)
        for nav in navs:
            nav_info = {
                'selector': selector,
                'tag': nav.name,
                'classes': list(nav.get('class', [])),
                'links': len(nav.find_all('a')),
                'role': nav.get('role'),
            }
            results['navigation_patterns'].append(nav_info)

    return results


def analyze_html_file(file_path):
    """Analyze a single HTML file."""
    print(f"Analyzing {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract theme from filename or detect from HTML
    theme_name = detect_theme_from_file(file_path, soup)

    return {
        'file': str(file_path),
        'theme': theme_name,
        'code_blocks': analyze_code_blocks(soup, theme_name),
        'api_docs': analyze_api_documentation(soup, theme_name),
        'sections': analyze_section_structure(soup, theme_name),
    }


def detect_theme_from_file(file_path, soup):
    """Detect MkDocs theme from filename or HTML content."""
    filename = file_path.stem.lower()

    # Check filename first
    if 'material' in filename:
        return 'material'
    if 'readthedocs' in filename or 'rtd' in filename:
        return 'readthedocs'
    if 'mkdocs' in filename or 'default' in filename:
        return 'mkdocs_default'

    # Try to detect from HTML content
    html_content = str(soup).lower()

    if 'material' in html_content and 'mkdocs' in html_content:
        return 'material'
    if 'readthedocs' in html_content or 'wy-nav' in html_content:
        return 'readthedocs'
    if 'bootstrap' in html_content and 'mkdocs' in html_content:
        return 'mkdocs_default'

    return 'unknown'


def main():
    """Main analysis function."""
    samples_dir = Path('.auxiliary/scribbles/mkdocs-samples')
    html_files = list(samples_dir.glob('*.html'))

    if not html_files:
        print("No HTML files found in samples directory")
        print(f"Expected directory: {samples_dir}")
        print("Please download MkDocs theme samples first")
        return

    all_analyses = []

    for html_file in html_files:
        try:
            analysis = analyze_html_file(html_file)
            all_analyses.append(analysis)
        except Exception as e:  # noqa: PERF203
            print(f"Error analyzing {html_file}: {e}")

    # Save results
    output_file = samples_dir / 'analysis_results.json'

    # Convert sets to lists for JSON serialization
    def convert_sets(obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, dict):
            return {k: convert_sets(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_sets(item) for item in obj]
        return obj

    serializable_analyses = convert_sets(all_analyses)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_analyses, f, indent=2, ensure_ascii=False)

    print(f"Analysis complete. Results saved to {output_file}")

    # Print summary
    print("\n=== MKDOCS ANALYSIS SUMMARY ===")
    for analysis in all_analyses:
        theme = analysis['theme']
        code_blocks = len(analysis['code_blocks']['code_blocks'])
        syntax_patterns = len(analysis['code_blocks']['syntax_patterns'])
        function_sigs = len(analysis['api_docs']['function_signatures'])
        main_containers = len(analysis['sections']['main_containers'])

        print(f"{theme}: {code_blocks} code blocks, "
              f"{syntax_patterns} syntax patterns, "
              f"{function_sigs} function signatures, "
              f"{main_containers} main containers")


if __name__ == '__main__':
    main()