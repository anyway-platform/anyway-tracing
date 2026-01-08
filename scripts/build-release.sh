#!/bin/bash
set -e

cd "$(dirname "$0")/../packages/anyway-sdk"

if [ "$(uname)" = "Darwin" ]; then
    # macOS sed requires space after -i
    sed -i '' 's/{ path = "[^"]*", develop = true }/"^0.50.1"/g' pyproject.toml
else
    # Linux sed
    sed -i 's/{ path = "[^"]*", develop = true }/"^0.50.1"/g' pyproject.toml
fi

poetry build

echo ""
echo "Build complete! Files in dist/"
echo "To publish: poetry publish -r testpypi"
echo "To restore pyproject.toml: git checkout pyproject.toml"
