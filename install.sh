#!/usr/bin/env bash
# agy-switch installer — usage:
#   curl -fsSL https://raw.githubusercontent.com/ZhangNy301/agy-switch/main/install.sh | bash
# or, from a cloned repo:  ./install.sh
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/ZhangNy301/agy-switch/main"
DEST="${HOME}/.local/bin"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"

echo "agy-switch installer"

# --- requirement: python >= 3.7 -------------------------------------------
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && \
     "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 7) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "error: Python 3.7+ is required but was not found on PATH." >&2
  echo "  Debian/Ubuntu: sudo apt install python3" >&2
  echo "  macOS (brew):  brew install python3" >&2
  exit 1
fi
echo "  python: $($PY -V 2>&1)"

mkdir -p "$DEST"

# --- install the script -----------------------------------------------------
if [ -n "$SRC_DIR" ] && [ -f "$SRC_DIR/bin/agy-switch" ]; then
  cp "$SRC_DIR/bin/agy-switch" "$DEST/agy-switch"
else
  if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl is required to download agy-switch" >&2; exit 1
  fi
  curl -fsSL "$REPO_RAW/bin/agy-switch" -o "$DEST/agy-switch"
fi
chmod +x "$DEST/agy-switch"
ln -sf agy-switch "$DEST/asw"
echo "  installed: $DEST/agy-switch (+ asw alias)"

# --- PATH check -------------------------------------------------------------
case ":$PATH:" in
  *":$DEST:"*) ;;
  *)
    echo
    echo "note: $DEST is not on your PATH. Add this to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    ;;
esac

echo
echo "done. next steps:"
echo "  agy-switch login    # add your first account"
echo "  asw                 # interactive switcher"
