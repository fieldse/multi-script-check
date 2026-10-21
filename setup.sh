#!/bin/bash
# setup.sh — create .venv with uv and install requirements.txt if it lists any dependencies
set -euo pipefail

# Show usage information
function usage() {
  cat <<EOF
Usage: $0 [-h|--help]
  -h, --help  Show this help message

Run once after cloning; re-running is safe. Then: source ./activate.sh

Example:
  ./setup.sh
EOF
}

# Exit with an error if uv is not installed
function require_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found; install it from https://docs.astral.sh/uv/" >&2
    exit 1
  fi
}

# Create .venv in the project directory unless it already exists
function create_venv() {
  if [[ -d .venv ]]; then
    echo ".venv already exists"
  else
    uv venv .venv
  fi
}

# Install requirements.txt into .venv when it lists at least one dependency
function install_dependencies() {
  if [[ -f requirements.txt ]] && grep -qvE '^[[:space:]]*(#|$)' requirements.txt; then
    uv pip install --python .venv/bin/python -r requirements.txt
  else
    echo "no dependencies to install"
  fi
}

# Parse arguments and run setup from the project directory
function main() {
  case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "")        ;;
    *)         echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac

  cd "$(dirname "${BASH_SOURCE[0]}")"
  require_uv
  create_venv
  install_dependencies
  echo "setup complete: .venv is ready. Next: source ./activate.sh"
}

main "$@"
