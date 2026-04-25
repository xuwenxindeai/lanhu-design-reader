#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${LANHU_DESIGN_READER_REPO:-https://github.com/xuwenxindeai/lanhu-design-reader.git}"
BASE_DIR="${LANHU_DESIGN_READER_HOME:-$HOME/.lanhu-design-reader}"
SRC_DIR="$BASE_DIR/src"
VENV_DIR="$BASE_DIR/venv"
BIN_DIR="${LANHU_DESIGN_READER_BIN_DIR:-$HOME/.local/bin}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_MCP="${INSTALL_MCP:-0}"

info() {
  printf '[lanhu-design-reader] %s\n' "$*"
}

die() {
  printf '[lanhu-design-reader] ERROR: %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

check_python() {
  command_exists "$PYTHON_BIN" || die "Python not found: $PYTHON_BIN. Set PYTHON_BIN=/path/to/python3.10+ and retry."
  "$PYTHON_BIN" - <<'PY' || die "Python 3.10+ is required. Set PYTHON_BIN=python3.12 if needed."
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

install_source() {
  mkdir -p "$BASE_DIR" "$BIN_DIR"

  if [ -d "$SRC_DIR/.git" ]; then
    info "Updating source at $SRC_DIR"
    git -C "$SRC_DIR" pull --ff-only
  else
    command_exists git || die "git is required but was not found."
    info "Cloning source to $SRC_DIR"
    git clone "$REPO_URL" "$SRC_DIR"
  fi
}

install_python_package() {
  info "Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"

  info "Installing package"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  if [ "$INSTALL_MCP" = "1" ]; then
    "$VENV_DIR/bin/pip" install -e "$SRC_DIR[mcp]"
  else
    "$VENV_DIR/bin/pip" install -e "$SRC_DIR"
  fi
}

install_commands() {
  ln -sf "$VENV_DIR/bin/lh-design" "$BIN_DIR/lh-design"

  if [ -x "$VENV_DIR/bin/lh-design-mcp" ]; then
    ln -sf "$VENV_DIR/bin/lh-design-mcp" "$BIN_DIR/lh-design-mcp"
  fi
}

install_config() {
  if [ ! -f "$BASE_DIR/.env" ]; then
    cat > "$BASE_DIR/.env" <<'EOF'
LANHU_COOKIE=
DDS_COOKIE=
EOF
    chmod 600 "$BASE_DIR/.env" 2>/dev/null || true
    info "Created config file at $BASE_DIR/.env"
  else
    info "Keeping existing config file at $BASE_DIR/.env"
  fi
}

print_next_steps() {
  info "Installed command: $BIN_DIR/lh-design"

  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
      printf '\n%s\n' "Add this to your shell config if lh-design is not found:"
      printf '  export PATH="%s:$PATH"\n' "$BIN_DIR"
      ;;
  esac

  printf '\n%s\n' "Configure your Lanhu cookie in:"
  printf '  %s/.env\n' "$BASE_DIR"
  printf '\n%s\n' "Then verify with:"
  printf '  lh-design --help\n'
}

check_python
install_source
install_python_package
install_commands
install_config
"$BIN_DIR/lh-design" --help >/dev/null
print_next_steps
