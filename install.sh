#!/usr/bin/env bash
set -euo pipefail

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Linux)  PLATFORM="linux" ;;
  Darwin) PLATFORM="darwin" ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac

case "$ARCH" in
  x86_64)  ARCH="x86_64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *)
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
BINARY_NAME="app"

echo "Installing $BINARY_NAME for $PLATFORM/$ARCH..."

# Ensure install directory exists and is writable
if [ ! -d "$INSTALL_DIR" ]; then
  mkdir -p "$INSTALL_DIR"
fi

if [ ! -w "$INSTALL_DIR" ]; then
  echo "Error: $INSTALL_DIR is not writable. Try running with sudo." >&2
  exit 1
fi

echo "Installation complete. Run '$BINARY_NAME --help' to get started."
