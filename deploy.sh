#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VERSION_FILE="src/version.py"
PYPROJECT_FILE="pyproject.toml"
MARKER_FILE=".deploy_marker"

read_version_field() {
    sed -n "s/^$1: int = \([0-9][0-9]*\).*/\1/p" "$VERSION_FILE"
}

if ! command -v mpremote > /dev/null; then
    echo "deploy: mpremote not found, run 'uv sync' first" >&2
    exit 1
fi

cd src
FILES_TO_COPY=()

if [ -f "../$MARKER_FILE" ] && [ -z "${DEPLOY_ALL:-}" ]; then # DEPLOY_ALL is set by deploy-all.sh
    while IFS= read -r -d '' file; do
        filename="${file#./}"
        FILES_TO_COPY+=("$filename")
    done < <(find . -type f ! -name "*.example.py" ! -name "version.py" ! -path "*/__pycache__/*" -newer "../$MARKER_FILE" -print0)
else
    while IFS= read -r -d '' file; do
        filename="${file#./}"
        FILES_TO_COPY+=("$filename")
    done < <(find . -type f ! -name "*.example.py" ! -name "version.py" ! -path "*/__pycache__/*" -print0)
fi
cd ..

if [ ${#FILES_TO_COPY[@]} -eq 0 ]; then
    echo "deploy: no changes detected, version not bumped."
    exit 0
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

if [[ ! " ${FILES_TO_COPY[@]} " =~ " version.py " ]]; then
    FILES_TO_COPY+=("version.py")
fi

echo "deploy: version bumped to $version"
echo "deploy: Copying ${#FILES_TO_COPY[@]} file(s)..."

PATHS_TO_COPY=()
for f in "${FILES_TO_COPY[@]}"; do
    echo "  -> $f"
    PATHS_TO_COPY+=("src/$f")
done

# IMPORTANT: mpremote cp only keeps the file name, so src/modules/clock.py lands next to main.py in the device root.
# That is intended, the modules/ folder only exists to keep the repository tidy
mpremote cp "${PATHS_TO_COPY[@]}" : + repl

touch "$MARKER_FILE"