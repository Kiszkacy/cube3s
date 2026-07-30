#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VERSION_FILE="src/version.py"
PYPROJECT_FILE="pyproject.toml"


read_version_field() {
    sed -n "s/^$1: int = \([0-9][0-9]*\).*/\1/p" "$VERSION_FILE"
}


if ! command -v mpremote > /dev/null; then
    echo "deploy: mpremote not found, run 'uv sync' first" >&2
    exit 1
fi

major="$(read_version_field MAJOR)"
minor="$(read_version_field MINOR)"
build="$(read_version_field BUILD)"

if [ -z "$major" ] || [ -z "$minor" ] || [ -z "$build" ]; then
    echo "deploy: could not parse MAJOR/MINOR/BUILD out of $VERSION_FILE" >&2
    exit 1
fi

build=$((build + 1))
version="$major.$minor.$build"

sed -i "s/^BUILD: int = .*/BUILD: int = $build/" "$VERSION_FILE"
sed -i "s/^version = .*/version = \"$version\"/" "$PYPROJECT_FILE"

echo "deploy: version $version"
mpremote cp -r src/* : + repl
