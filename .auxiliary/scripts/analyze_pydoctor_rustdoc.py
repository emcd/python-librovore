#!/usr/bin/env python3
"""
Quick analysis of Pydoctor and Rustdoc HTML structure.
"""

from bs4 import BeautifulSoup
from pathlib import Path
import json


def analyze_pydoctor_structure(html_path):
    """Analyze Pydoctor HTML structure."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    analysis = {
        'file': str(html_path),
        'generator': None,
        'theme_indicators': [],
        'css_files': [],
        'main_containers': [],
        'navigation_elements': [],
        'code_blocks': [],
        'api_documentation_elements': [],
    }

    # Generator meta tag
    generator = soup.find('meta', {'name': 'generator'})
    if generator:
        analysis['generator'] = generator.get('content')

    # CSS files
    for link in soup.find_all('link', {'rel': 'stylesheet'}):
        href = link.get('href', '')
        analysis['css_files'].append(href)
        themes = ['bootstrap', 'apidocs', 'pydoctor']
        if any(theme in href.lower() for theme in themes):
            analysis['theme_indicators'].append(href)

    # Main content containers
    for selector in ['main', 'article', '.main', '.content', '#main-content']:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:3]:  # Limit to first 3
                analysis['main_containers'].append({
                    'selector': selector,
                    'tag': elem.name,
                    'classes': elem.get('class', []),
                    'id': elem.get('id'),
                })

    # Navigation
    nav_elements = soup.find_all('nav')
    for nav in nav_elements[:3]:
        analysis['navigation_elements'].append({
            'tag': 'nav',
            'classes': nav.get('class', []),
            'id': nav.get('id'),
            'links': len(nav.find_all('a')),
        })

    # Code blocks
    for selector in ['pre', 'code', '.highlight', '.code-block']:
        blocks = soup.select(selector)
        for block in blocks[:5]:  # Sample first 5
            analysis['code_blocks'].append({
                'selector': selector,
                'tag': block.name,
                'classes': block.get('class', []),
                'parent_classes': (
                    block.parent.get('class', []) if block.parent else []
                ),
                'content_preview': block.get_text()[:100].replace('\n', '\\n'),
            })

    # API elements (dt/dd, function signatures, etc.)
    dls = soup.find_all('dl')
    for dl in dls[:3]:
        dt_elements = dl.find_all('dt', recursive=False)
        analysis['api_documentation_elements'].append({
            'tag': 'dl',
            'classes': dl.get('class', []),
            'dt_count': len(dt_elements),
            'sample_dt_classes': [
                dt.get('class', []) for dt in dt_elements[:3]
            ],
        })

    # Check for specific pydoctor elements
    pydoctor_specific = {
        'function_defs': len(soup.find_all(class_='functionDef')),
        'class_defs': len(soup.find_all(class_='classDef')),
        'doc_summaries': len(soup.find_all(class_='docstring')),
        'sig_elements': len(soup.find_all(class_='sig')),
    }
    analysis['pydoctor_specific'] = pydoctor_specific

    return analysis


def analyze_rustdoc_structure(html_path):
    """Analyze Rustdoc HTML structure."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    analysis = {
        'file': str(html_path),
        'generator': None,
        'theme_indicators': [],
        'css_files': [],
        'main_containers': [],
        'navigation_elements': [],
        'code_blocks': [],
        'api_documentation_elements': [],
    }

    # Generator meta tag
    generator = soup.find('meta', {'name': 'generator'})
    if generator:
        analysis['generator'] = generator.get('content')

    # Check for rustdoc-specific meta tags
    rustdoc_vars = soup.find('meta', {'name': 'rustdoc-vars'})
    if rustdoc_vars:
        analysis['rustdoc_vars'] = dict(rustdoc_vars.attrs)

    # CSS files
    for link in soup.find_all('link', {'rel': 'stylesheet'}):
        href = link.get('href', '')
        analysis['css_files'].append(href)
        if 'rustdoc' in href.lower():
            analysis['theme_indicators'].append(href)

    # Main content containers
    for selector in ['main', '.content', '#main-content', '.docblock']:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:3]:
                analysis['main_containers'].append({
                    'selector': selector,
                    'tag': elem.name,
                    'classes': elem.get('class', []),
                    'id': elem.get('id'),
                })

    # Navigation (sidebar)
    nav_elements = soup.find_all(['nav', '.sidebar'])
    for nav in nav_elements[:3]:
        analysis['navigation_elements'].append({
            'tag': nav.name,
            'classes': nav.get('class', []),
            'id': nav.get('id'),
            'links': len(nav.find_all('a')),
        })

    # Code blocks
    for selector in ['pre', 'code', '.example-wrap', '.rust']:
        blocks = soup.select(selector)
        for block in blocks[:5]:
            analysis['code_blocks'].append({
                'selector': selector,
                'tag': block.name,
                'classes': block.get('class', []),
                'parent_classes': (
                    block.parent.get('class', []) if block.parent else []
                ),
                'content_preview': block.get_text()[:100].replace('\n', '\\n'),
            })

    # Rustdoc-specific elements
    rustdoc_specific = {
        'rustdoc_topbar': len(soup.find_all('rustdoc-topbar')),
        'rustdoc_toolbar': len(soup.find_all('rustdoc-toolbar')),
        'docblock': len(soup.find_all(class_='docblock')),
        'item_decl': len(soup.find_all(class_='item-decl')),
        'src_link': len(soup.find_all(class_='src')),
    }
    analysis['rustdoc_specific'] = rustdoc_specific

    return analysis


def main():
    """Analyze all downloaded samples."""
    pydoctor_dir = Path('.auxiliary/scribbles/pydoctor-samples')
    rustdoc_dir = Path('.auxiliary/scribbles/rustdoc-samples')

    results = {
        'pydoctor': [],
        'rustdoc': [],
    }

    print("=== Analyzing Pydoctor samples ===")
    for html_file in pydoctor_dir.glob('*.html'):
        print(f"Analyzing {html_file.name}...")
        analysis = analyze_pydoctor_structure(html_file)
        results['pydoctor'].append(analysis)

    print("\n=== Analyzing Rustdoc samples ===")
    for html_file in rustdoc_dir.glob('*.html'):
        print(f"Analyzing {html_file.name}...")
        analysis = analyze_rustdoc_structure(html_file)
        results['rustdoc'].append(analysis)

    # Save results
    output_file = Path('.auxiliary/scribbles/pydoctor-rustdoc-analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis saved to {output_file}")

    # Print summary
    print("\n=== SUMMARY ===")
    print("\nPydoctor:")
    for analysis in results['pydoctor']:
        print(f"  {Path(analysis['file']).name}:")
        print(f"    Generator: {analysis['generator']}")
        print(f"    CSS files: {len(analysis['css_files'])}")
        print(f"    Code blocks: {len(analysis['code_blocks'])}")
        pydoctor_elems = analysis['pydoctor_specific']
        print(f"    Pydoctor-specific elements: {pydoctor_elems}")

    print("\nRustdoc:")
    for analysis in results['rustdoc']:
        print(f"  {Path(analysis['file']).name}:")
        print(f"    Generator: {analysis['generator']}")
        print(f"    CSS files: {len(analysis['css_files'])}")
        print(f"    Code blocks: {len(analysis['code_blocks'])}")
        print(f"    Rustdoc-specific elements: {analysis['rustdoc_specific']}")


if __name__ == '__main__':
    main()
