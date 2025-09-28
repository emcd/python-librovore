#!/bin/bash
# Download remaining Sphinx theme samples for analysis

set -e

SAMPLES_DIR=".auxiliary/scribbles/sphinx-samples"
mkdir -p "$SAMPLES_DIR"

# Remaining themes to analyze
themes=(
    "default-alabaster"
    "pydata-sphinx-theme"
    "python-docs-theme"
    "default-agogo"
    "default-classic"
    "default-nature"
)

echo "Downloading remaining Sphinx theme samples..."

for theme in "${themes[@]}"; do
    echo "Downloading $theme..."

    # Download blocks page
    curl -s "https://sphinx-themes.org/sample-sites/${theme}/kitchen-sink/blocks/" \
         -o "${SAMPLES_DIR}/${theme}-blocks.html"

    # Download Python API domain page
    curl -s "https://sphinx-themes.org/sample-sites/${theme}/kitchen-sink/domains/api_python_domain/" \
         -o "${SAMPLES_DIR}/${theme}-python-api.html"

    # Download structure page
    curl -s "https://sphinx-themes.org/sample-sites/${theme}/kitchen-sink/structure/" \
         -o "${SAMPLES_DIR}/${theme}-structure.html"

    echo "  ✓ Downloaded blocks, API, and structure pages"
done

echo ""
echo "Download complete! Files saved to: $SAMPLES_DIR"
echo ""
echo "Next steps:"
echo "1. Run analysis: hatch --env develop run python .auxiliary/scribbles/analyze_sphinx_html.py"
echo "2. View patterns: hatch --env develop run python .auxiliary/scribbles/extract_code_patterns.py"
echo "3. Check sections: hatch --env develop run python .auxiliary/scribbles/section_analysis.py"