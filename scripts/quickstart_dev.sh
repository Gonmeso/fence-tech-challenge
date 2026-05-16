#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ask_yes_no() {
  local prompt="$1"
  local answer

  read -r -p "$prompt [y/N] " answer
  case "$answer" in
    y | Y | yes | YES) return 0 ;;
    *) return 1 ;;
  esac
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    echo "uv found: $(uv --version)"
    return
  fi

  if ! ask_yes_no "uv is missing. Install it with the official installer?"; then
    echo "uv is required. Aborting." >&2
    exit 1
  fi

  curl -LsSf https://astral.sh/uv/install.sh | sh
}

install_foundry() {
  if command -v forge >/dev/null 2>&1 &&
    command -v cast >/dev/null 2>&1 &&
    command -v anvil >/dev/null 2>&1; then
    echo "foundry found: $(forge --version | head -n 1)"
    return
  fi

  if ! ask_yes_no "Foundry is missing. Install it with foundryup?"; then
    echo "Foundry is required. Aborting." >&2
    exit 1
  fi

  curl -L https://foundry.paradigm.xyz | bash

  if command -v foundryup >/dev/null 2>&1; then
    foundryup
  else
    echo "foundryup was installed, but is not on PATH yet." >&2
    echo "Open a new shell or source your shell profile, then run foundryup." >&2
    exit 1
  fi
}

main() {
  cd "$REPO_ROOT"

  install_uv
  install_foundry

  echo "Updating git submodules"
  git submodule update --init --recursive

  echo "Creating backend virtualenv and installing dependencies"
  uv sync --project backend

  echo "Installing pre-commit hooks"
  uv run --project backend pre-commit install

  echo "Building smart contract"
  (
    cd smart-contract
    forge build
  )

  echo "Development environment is ready."
}

main "$@"
