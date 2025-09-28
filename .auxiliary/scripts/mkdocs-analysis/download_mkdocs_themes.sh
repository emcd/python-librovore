#!/bin/bash
# Download MkDocs theme samples for analysis

set -e

SAMPLES_DIR=".auxiliary/scribbles/mkdocs-samples"
mkdir -p "$SAMPLES_DIR"

echo "Downloading MkDocs theme samples for analysis..."

# Material for MkDocs - using their own documentation
echo "🎨 Downloading Material for MkDocs samples..."

# Main documentation page with code examples
curl -s "https://squidfunk.github.io/mkdocs-material/" \
     -o "${SAMPLES_DIR}/material-main.html"

# Code blocks and syntax highlighting page
curl -s "https://squidfunk.github.io/mkdocs-material/reference/code-blocks/" \
     -o "${SAMPLES_DIR}/material-code-blocks.html"

# API documentation example (if they have mkdocstrings)
curl -s "https://squidfunk.github.io/mkdocs-material/reference/" \
     -o "${SAMPLES_DIR}/material-reference.html"

echo "  ✓ Downloaded Material for MkDocs samples"

# ReadTheDocs theme - need to find good examples
echo "📚 Downloading ReadTheDocs theme samples..."

# MkDocs own documentation uses ReadTheDocs theme
curl -s "https://www.mkdocs.org/" \
     -o "${SAMPLES_DIR}/readthedocs-main.html"

curl -s "https://www.mkdocs.org/user-guide/writing-your-docs/" \
     -o "${SAMPLES_DIR}/readthedocs-writing-docs.html"

curl -s "https://www.mkdocs.org/user-guide/configuration/" \
     -o "${SAMPLES_DIR}/readthedocs-configuration.html"

echo "  ✓ Downloaded ReadTheDocs theme samples"

# Default MkDocs theme - Bootstrap based
echo "🥾 Downloading default MkDocs theme samples..."

# Need to find sites using default theme - this might be harder
# Let's try some basic MkDocs sites

# FastAPI docs use a custom theme but might have similar patterns
curl -s "https://fastapi.tiangolo.com/" \
     -o "${SAMPLES_DIR}/mkdocs-default-example1.html"

# Alternative: download a basic getting started page
curl -s "https://www.mkdocs.org/getting-started/" \
     -o "${SAMPLES_DIR}/mkdocs-default-getting-started.html"

echo "  ✓ Downloaded default theme samples"

# Additional samples with API documentation (mkdocstrings)
echo "🔧 Downloading mkdocstrings API documentation samples..."

# Pydantic docs use Material + mkdocstrings
curl -s "https://docs.pydantic.dev/latest/api/main/" \
     -o "${SAMPLES_DIR}/material-mkdocstrings-pydantic.html"

# HTTPX docs also use Material + mkdocstrings
curl -s "https://www.python-httpx.org/api/" \
     -o "${SAMPLES_DIR}/material-mkdocstrings-httpx.html"

echo "  ✓ Downloaded mkdocstrings samples"

echo ""
echo "Download complete! Files saved to: $SAMPLES_DIR"
echo ""
echo "Downloaded samples:"
ls -la "$SAMPLES_DIR"/*.html | wc -l | xargs echo "  Total files:"
echo ""
echo "Next steps:"
echo "1. Run analysis: hatch --env develop run python .auxiliary/scripts/mkdocs-analysis/analyze_mkdocs_html.py"
echo "2. View patterns: hatch --env develop run python .auxiliary/scripts/mkdocs-analysis/extract_code_patterns.py"
echo "3. Check sections: hatch --env develop run python .auxiliary/scripts/mkdocs-analysis/section_analysis.py"
echo "4. Full summary: hatch --env develop run python .auxiliary/scripts/mkdocs-analysis/comprehensive_summary.py"