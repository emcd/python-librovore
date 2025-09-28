#!/usr/bin/env python3
"""
Analyze downloaded Sphinx theme HTML files to extract structural patterns
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

    # Look for various code block containers
    code_selectors = [
        '.highlight', '.literal-block', '.code-block',
        'pre', '.doctest', '.parsed-literal'
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
                'content_preview': block.get_text()[:100].replace('\n', '\\n'),
            }

            # Look for language indicators
            all_classes = block_info['classes'] + block_info['parent_classes']
            for cls in all_classes:
                lang_keywords = [
                    'python', 'javascript', 'c++', 'java',
                    'html', 'css', 'bash'
                ]
                if any(lang in cls.lower() for lang in lang_keywords):
                    results['syntax_patterns'].add(cls)
                results['css_classes'].add(cls)

            results['code_blocks'].append(block_info)

    return results


def analyze_api_documentation(soup, theme_name):
    """Analyze API documentation structure (dt/dd patterns, signatures)."""
    results = {
        'theme': theme_name,
        'function_signatures': [],
        'dt_dd_patterns': [],
        'api_classes': set(),
    }

    # Find definition lists (dl elements)
    dls = soup.find_all('dl')
    for dl in dls:
        dt_elements = dl.find_all('dt')
        for dt in dt_elements:
            dd = dt.find_next_sibling('dd')

            signature_info = {
                'dt_classes': list(dt.get('class', [])),
                'dt_attributes': dict(dt.attrs),
                'dt_text': dt.get_text().strip(),
                'dd_classes': list(dd.get('class', [])) if dd else [],
                'dd_preview': (dd.get_text()[:200].replace('\n', ' ')
                              if dd else ''),
            }

            # Look for function signature patterns
            dt_text = dt.get_text()
            keywords = ['def ', 'function', 'class ', 'async ', '(', ')']
            if any(keyword in dt_text for keyword in keywords):
                results['function_signatures'].append(signature_info)

            results['dt_dd_patterns'].append(signature_info)

            # Collect CSS classes
            dt_classes = signature_info['dt_classes']
            dd_classes = signature_info['dd_classes']
            for cls in dt_classes + dd_classes:
                results['api_classes'].add(cls)

    return results


def analyze_section_structure(soup, theme_name):
    """Analyze section structure and heading patterns."""
    results = {
        'theme': theme_name,
        'headings': [],
        'sections': [],
        'navigation_patterns': [],
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

    # Analyze section containers
    section_selectors = [
        'section', '.section', '.content', '.body', 'article', 'main'
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

    # Analyze navigation patterns
    nav_selectors = ['.toc', '.navigation', '.sidebar', '.menu', 'nav']
    for selector in nav_selectors:
        navs = soup.select(selector)
        for nav in navs:
            nav_info = {
                'selector': selector,
                'tag': nav.name,
                'classes': list(nav.get('class', [])),
                'links': len(nav.find_all('a')),
            }
            results['navigation_patterns'].append(nav_info)

    return results


def analyze_html_file(file_path):
    """Analyze a single HTML file."""
    print(f"Analyzing {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract theme from filename
    theme_name = file_path.stem.split('-')[0]

    return {
        'file': str(file_path),
        'theme': theme_name,
        'code_blocks': analyze_code_blocks(soup, theme_name),
        'api_docs': analyze_api_documentation(soup, theme_name),
        'sections': analyze_section_structure(soup, theme_name),
    }


def main():
    """Main analysis function."""
    samples_dir = Path('.auxiliary/scribbles/sphinx-samples')
    html_files = list(samples_dir.glob('*.html'))

    if not html_files:
        print("No HTML files found in samples directory")
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
    print("\n=== SUMMARY ===")
    for analysis in all_analyses:
        theme = analysis['theme']
        code_blocks = len(analysis['code_blocks']['code_blocks'])
        syntax_patterns = len(analysis['code_blocks']['syntax_patterns'])
        function_sigs = len(analysis['api_docs']['function_signatures'])
        headings = len(analysis['sections']['headings'])

        print(f"{theme}: {code_blocks} code blocks, "
              f"{syntax_patterns} syntax patterns, "
              f"{function_sigs} function signatures, {headings} headings")


if __name__ == '__main__':
    main()