#!/bin/bash
# Download Rustdoc documentation samples for analysis

set -e

SAMPLES_DIR=".auxiliary/scribbles/rustdoc-samples"
mkdir -p "$SAMPLES_DIR"

echo "Downloading Rustdoc documentation samples for analysis..."

# Rust Standard Library - The canonical example
echo "🦀 Downloading Rust Standard Library documentation..."

curl -s "https://doc.rust-lang.org/std/" \
     -o "${SAMPLES_DIR}/std-main.html"

curl -s "https://doc.rust-lang.org/std/vec/index.html" \
     -o "${SAMPLES_DIR}/std-vec-module.html"

curl -s "https://doc.rust-lang.org/std/vec/struct.Vec.html" \
     -o "${SAMPLES_DIR}/std-vec-struct.html"

curl -s "https://doc.rust-lang.org/std/string/struct.String.html" \
     -o "${SAMPLES_DIR}/std-string-struct.html"

curl -s "https://doc.rust-lang.org/std/option/enum.Option.html" \
     -o "${SAMPLES_DIR}/std-option-enum.html"

curl -s "https://doc.rust-lang.org/std/io/trait.Read.html" \
     -o "${SAMPLES_DIR}/std-read-trait.html"

curl -s "https://doc.rust-lang.org/std/macro.println.html" \
     -o "${SAMPLES_DIR}/std-println-macro.html"

# All items page - comprehensive inventory
curl -s "https://doc.rust-lang.org/std/all.html" \
     -o "${SAMPLES_DIR}/std-all-items.html"

# Download index files
curl -s "https://doc.rust-lang.org/std/vec/sidebar-items1.91.1.js" \
     -o "${SAMPLES_DIR}/std-vec-sidebar-items.js" 2>/dev/null || echo "  ⚠ Sidebar items may have different version"

curl -s "https://doc.rust-lang.org/crates1.91.1.js" \
     -o "${SAMPLES_DIR}/std-crates.js" 2>/dev/null || echo "  ⚠ Crates list may have different version"

echo "  ✓ Downloaded Rust std library samples"

# docs.rs - Community crate documentation
echo "📚 Downloading docs.rs samples (serde)..."

curl -s "https://docs.rs/serde/latest/serde/" \
     -o "${SAMPLES_DIR}/serde-main.html"

curl -s "https://docs.rs/serde/latest/serde/trait.Serialize.html" \
     -o "${SAMPLES_DIR}/serde-serialize-trait.html"

curl -s "https://docs.rs/serde/latest/serde/trait.Deserialize.html" \
     -o "${SAMPLES_DIR}/serde-deserialize-trait.html"

curl -s "https://docs.rs/serde/latest/serde/all.html" \
     -o "${SAMPLES_DIR}/serde-all-items.html"

echo "  ✓ Downloaded serde samples"

# Another popular crate
echo "⚡ Downloading docs.rs samples (tokio)..."

curl -s "https://docs.rs/tokio/latest/tokio/" \
     -o "${SAMPLES_DIR}/tokio-main.html"

curl -s "https://docs.rs/tokio/latest/tokio/macro.main.html" \
     -o "${SAMPLES_DIR}/tokio-main-macro.html"

echo "  ✓ Downloaded tokio samples"

echo ""
echo "Download complete! Files saved to: $SAMPLES_DIR"
echo ""
echo "Downloaded samples:"
ls -lh "$SAMPLES_DIR"/*.html | wc -l | xargs echo "  HTML files:"
ls -lh "$SAMPLES_DIR"/*.js 2>/dev/null | wc -l | xargs echo "  JS files:"
echo ""
echo "Next steps:"
echo "1. Run analysis: hatch --env develop run python .auxiliary/scripts/analyze_pydoctor_rustdoc.py"
echo "2. View results: cat .auxiliary/scribbles/pydoctor-rustdoc-analysis.json"
echo "3. Create comprehensive summary script if needed"
