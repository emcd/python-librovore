#!/bin/bash
# Download Pydoctor documentation samples for analysis

set -e

SAMPLES_DIR=".auxiliary/scribbles/pydoctor-samples"
mkdir -p "$SAMPLES_DIR"

echo "Downloading Pydoctor documentation samples for analysis..."

# Dulwich - Primary example
echo "📦 Downloading Dulwich API documentation..."

curl -s "https://www.dulwich.io/api/" \
     -o "${SAMPLES_DIR}/dulwich-main.html"

curl -s "https://www.dulwich.io/api/dulwich.repo.html" \
     -o "${SAMPLES_DIR}/dulwich-repo-module.html"

curl -s "https://www.dulwich.io/api/dulwich.repo.Repo.html" \
     -o "${SAMPLES_DIR}/dulwich-repo-class.html"

curl -s "https://www.dulwich.io/api/dulwich.client.HttpGitClient.html" \
     -o "${SAMPLES_DIR}/dulwich-client-class.html"

# Download search index files
curl -s "https://www.dulwich.io/api/searchindex.json" \
     -o "${SAMPLES_DIR}/dulwich-searchindex.json"

curl -s "https://www.dulwich.io/api/search.js" \
     -o "${SAMPLES_DIR}/dulwich-search.js"

curl -s "https://www.dulwich.io/api/searchlib.js" \
     -o "${SAMPLES_DIR}/dulwich-searchlib.js"

# Download index pages
curl -s "https://www.dulwich.io/api/moduleIndex.html" \
     -o "${SAMPLES_DIR}/dulwich-moduleIndex.html"

curl -s "https://www.dulwich.io/api/classIndex.html" \
     -o "${SAMPLES_DIR}/dulwich-classIndex.html"

echo "  ✓ Downloaded Dulwich samples"

# Twisted - Another major Pydoctor example
echo "🌀 Downloading Twisted API documentation..."

curl -s "https://twisted.org/documents/current/api/" \
     -o "${SAMPLES_DIR}/twisted-main.html"

curl -s "https://twisted.org/documents/current/api/twisted.internet.html" \
     -o "${SAMPLES_DIR}/twisted-internet-module.html"

curl -s "https://twisted.org/documents/current/api/twisted.internet.reactor.html" \
     -o "${SAMPLES_DIR}/twisted-reactor-module.html"

# Download Twisted search index
curl -s "https://twisted.org/documents/current/api/searchindex.json" \
     -o "${SAMPLES_DIR}/twisted-searchindex.json" 2>/dev/null || echo "  ⚠ Could not download Twisted search index"

echo "  ✓ Downloaded Twisted samples"

echo ""
echo "Download complete! Files saved to: $SAMPLES_DIR"
echo ""
echo "Downloaded samples:"
ls -lh "$SAMPLES_DIR"/*.html | wc -l | xargs echo "  HTML files:"
ls -lh "$SAMPLES_DIR"/*.json 2>/dev/null | wc -l | xargs echo "  JSON files:"
ls -lh "$SAMPLES_DIR"/*.js 2>/dev/null | wc -l | xargs echo "  JS files:"
echo ""
echo "Next steps:"
echo "1. Run analysis: hatch --env develop run python .auxiliary/scripts/analyze_pydoctor_rustdoc.py"
echo "2. View results: cat .auxiliary/scribbles/pydoctor-rustdoc-analysis.json"
echo "3. Create comprehensive summary script if needed"
