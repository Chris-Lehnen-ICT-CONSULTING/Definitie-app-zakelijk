#!/usr/bin/env bash
set -euo pipefail

# macOS LaunchAgent installer for OPENAI_API_KEY_PROD
# - Installs a per-user LaunchAgent that sets OPENAI_API_KEY_PROD at login
# - Useful so GUI apps like VS Code inherit the key without manual exports

LABEL="com.definitie.setenv.openai.prod"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/${LABEL}.plist"

usage() {
  cat <<EOF
Usage:
  $0 install [--key <sk-...>]   Install/Update LaunchAgent to set OPENAI_API_KEY_PROD
  $0 check                       Print the current value from launchctl (if any)
  $0 uninstall                   Remove LaunchAgent and unset variable

Notes:
  - This stores the key (plaintext) in: $PLIST_PATH (chmod 600)
  - After install or uninstall, restart VS Code to pick up changes
EOF
}

ensure_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script only supports macOS (Darwin)." >&2
    exit 1
  fi
  if ! command -v launchctl >/dev/null 2>&1; then
    echo "launchctl not found (required on macOS)." >&2
    exit 1
  fi
}

create_plist() {
  local key_value="$1"
  mkdir -p "$PLIST_DIR"
  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/launchctl</string>
    <string>setenv</string>
    <string>OPENAI_API_KEY_PROD</string>
    <string>${key_value}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/${LABEL}.out.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/${LABEL}.err.log</string>
</dict>
</plist>
PLIST
  chmod 600 "$PLIST_PATH"
}

install_agent() {
  ensure_macos

  local key="${1:-}"
  if [[ -z "$key" ]]; then
    if [[ -n "${OPENAI_API_KEY_PROD:-}" ]]; then
      key="$OPENAI_API_KEY_PROD"
    else
      read -r -p "Enter OPENAI_API_KEY_PROD (sk-...): " key
    fi
  fi

  if [[ -z "$key" ]]; then
    echo "No key provided. Aborting." >&2
    exit 1
  fi

  echo "[setup] Writing LaunchAgent plist to: $PLIST_PATH"
  create_plist "$key"

  echo "[setup] Reloading LaunchAgent..."
  launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl load -w "$PLIST_PATH"

  echo "[setup] Verifying..."
  local got
  got="$(launchctl getenv OPENAI_API_KEY_PROD || true)"
  if [[ -n "$got" ]]; then
    echo "OK: OPENAI_API_KEY_PROD is set for login sessions."
  else
    echo "WARN: launchctl getenv returned empty. Try logging out/in or restarting VS Code." >&2
  fi
}

check_agent() {
  ensure_macos
  local got
  got="$(launchctl getenv OPENAI_API_KEY_PROD || true)"
  if [[ -n "$got" ]]; then
    echo "OPENAI_API_KEY_PROD length: ${#got}"
  else
    echo "OPENAI_API_KEY_PROD not set in login session."
  fi
  if [[ -f "$PLIST_PATH" ]]; then
    echo "LaunchAgent plist found at: $PLIST_PATH"
  else
    echo "LaunchAgent plist not found at: $PLIST_PATH"
  fi
}

uninstall_agent() {
  ensure_macos
  echo "[remove] Unloading and removing LaunchAgent..."
  launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl unsetenv OPENAI_API_KEY_PROD >/dev/null 2>&1 || true
  rm -f "$PLIST_PATH"
  echo "[remove] Done. You may need to restart VS Code to drop the env."
}

main() {
  local cmd="${1:-install}"
  shift || true

  case "$cmd" in
    install)
      local key=""
      if [[ "${1:-}" == "--key" && -n "${2:-}" ]]; then
        key="$2"; shift 2
      fi
      install_agent "$key"
      ;;
    check)
      check_agent
      ;;
    uninstall)
      uninstall_agent
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
