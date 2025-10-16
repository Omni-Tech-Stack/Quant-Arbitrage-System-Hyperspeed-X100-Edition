#!/bin/bash
# Verification script for SYMEN-MAX integration

set -e

echo "=== SYMEN-MAX INTEGRATION VERIFICATION ==="
echo ""

echo "Environment:"
echo "  Node.js: $(node --version)"
echo "  Rust: $(rustc --version)"
echo ""

echo "Build Artifacts:"
if [ -f "native/math_engine.node" ]; then
    SIZE=$(du -h native/math_engine.node | cut -f1)
    echo "  ✓ native/math_engine.node ($SIZE)"
else
    echo "  ✗ native/math_engine.node missing"
    exit 1
fi

if [ -f "dist/index.js" ]; then
    echo "  ✓ dist/index.js"
else
    echo "  ✗ dist/index.js missing"
    exit 1
fi

if [ -f "dist/index.d.ts" ]; then
    echo "  ✓ dist/index.d.ts"
else
    echo "  ✗ dist/index.d.ts missing"
    exit 1
fi

echo ""
echo "Running integration tests..."
echo ""

yarn test

echo ""
echo "=== ALL VERIFICATIONS PASSED ==="
