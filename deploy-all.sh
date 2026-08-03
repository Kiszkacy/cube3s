#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# same as deploy.sh (bumps BUILD, syncs pyproject.toml, opens the REPL), except that the .deploy_marker check is
# skipped, so every file in src/ is pushed no matter when it was last edited. *.example.py stays excluded.
echo "deploy-all: pushing every file in src/, ignoring .deploy_marker"

export DEPLOY_ALL=1
exec bash ./deploy.sh "$@"
