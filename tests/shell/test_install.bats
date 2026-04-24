#!/usr/bin/env bats

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/install.sh"

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

@test "exits 1 for unsupported OS" {
  run env -i bash -c "uname() { echo 'Windows_NT'; }; export -f uname; bash '$SCRIPT'"
  # Simulate unsupported OS by overriding uname output via wrapper
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'FreeBSD' ;;
        -m) echo 'x86_64' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    bash '$SCRIPT'
  "
  [ "$status" -eq 1 ]
  [[ "$output" == *"Unsupported OS"* ]]
}

# ---------------------------------------------------------------------------
# Architecture detection
# ---------------------------------------------------------------------------

@test "exits 1 for unsupported architecture" {
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'Linux' ;;
        -m) echo 'mips' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    bash '$SCRIPT'
  "
  [ "$status" -eq 1 ]
  [[ "$output" == *"Unsupported architecture"* ]]
}

# ---------------------------------------------------------------------------
# Custom INSTALL_DIR
# ---------------------------------------------------------------------------

@test "respects custom INSTALL_DIR env var" {
  local tmpdir
  tmpdir="$(mktemp -d)"
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'Linux' ;;
        -m) echo 'x86_64' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    INSTALL_DIR='$tmpdir' bash '$SCRIPT'
  "
  [ "$status" -eq 0 ]
  rmdir "$tmpdir"
}

# ---------------------------------------------------------------------------
# Non-writable INSTALL_DIR
# ---------------------------------------------------------------------------

@test "exits 1 when INSTALL_DIR is not writable" {
  local tmpdir
  tmpdir="$(mktemp -d)"
  chmod 555 "$tmpdir"
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'Linux' ;;
        -m) echo 'x86_64' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    INSTALL_DIR='$tmpdir' bash '$SCRIPT'
  "
  chmod 755 "$tmpdir"
  rmdir "$tmpdir"
  [ "$status" -eq 1 ]
  [[ "$output" == *"not writable"* ]]
}

# ---------------------------------------------------------------------------
# Linux x86_64 happy path
# ---------------------------------------------------------------------------

@test "succeeds on Linux x86_64" {
  local tmpdir
  tmpdir="$(mktemp -d)"
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'Linux' ;;
        -m) echo 'x86_64' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    INSTALL_DIR='$tmpdir' bash '$SCRIPT'
  "
  rmdir "$tmpdir"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Installation complete"* ]]
}

# ---------------------------------------------------------------------------
# Darwin arm64 happy path
# ---------------------------------------------------------------------------

@test "succeeds on Darwin arm64" {
  local tmpdir
  tmpdir="$(mktemp -d)"
  run bash -c "
    uname() {
      case \"\$1\" in
        -s) echo 'Darwin' ;;
        -m) echo 'arm64' ;;
        *)  command uname \"\$@\" ;;
      esac
    }
    export -f uname
    INSTALL_DIR='$tmpdir' bash '$SCRIPT'
  "
  rmdir "$tmpdir"
  [ "$status" -eq 0 ]
}
