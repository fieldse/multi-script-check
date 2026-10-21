#!/bin/bash
# activate.sh — activate .venv (created by setup.sh) in the current shell
# Must be sourced. It deliberately avoids `set -e` and `exit`, which would act on the caller's shell.

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"

# Show usage information
function usage() {
  cat <<EOF
Usage: source activate.sh [-h|--help]
  -h, --help  Show this help message

Example:
  source ./activate.sh
EOF
}

# True when sourced rather than executed (bash and zsh)
function is_sourced() {
  if [[ -n "${ZSH_VERSION:-}" ]]; then
    [[ "${ZSH_EVAL_CONTEXT:-}" == *:file* ]]
  else
    [[ "${BASH_SOURCE[0]}" != "$0" ]]
  fi
}

# Parse arguments, check the venv exists, activate it
function main() {
  case "${1:-}" in
    -h|--help) usage; return 0 ;;
    "")        ;;
    *)         echo "Unknown option: $1" >&2; usage; return 1 ;;
  esac

  if ! is_sourced; then
    echo "activate.sh must be sourced, not executed." >&2
    usage
    return 1
  fi

  local project_dir
  project_dir="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

  if [[ ! -d "$project_dir/.venv" ]]; then
    echo ".venv not found; run ./setup.sh first." >&2
    return 1
  fi
  source "$project_dir/.venv/bin/activate"
  echo "activated: $VIRTUAL_ENV"
}

main "$@"
