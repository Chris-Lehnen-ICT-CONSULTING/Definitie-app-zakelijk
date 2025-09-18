#!/usr/bin/env bash
# clean_openai_keys.sh
# Doel:
# 1) Verwijder .env.backup (als die bestaat)
# 2) Wis .ruff_cache (bevatte binaries met key-strings)
# 3) Update config/config_development.yaml:
#    - vervang hardcoded "openai_api_key: <waarde>" door "openai_api_key: ${OPENAI_API_KEY}"
# 4) Eindscan op patronen met 'sk-' (mogelijke gelekte keys) en rapporteren
#
# Gebruik:
#   chmod +x clean_openai_keys.sh
#   ./clean_openai_keys.sh
#
# Opties:
#   DRY_RUN=1 ./clean_openai_keys.sh   # toont wat er zou gebeuren, zonder te wijzigen

set -euo pipefail

DRY_RUN="${DRY_RUN:-0}"

say() { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
good() { printf "\033[1;32m[ok]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[err]\033[0m %s\n" "$*"; }

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY_RUN: $*"
  else
    eval "$@"
  fi
}

# 0) Locatiecontrole
PROJECT_ROOT="$(pwd)"
say "Project root: $PROJECT_ROOT"

# 1) .env.backup verwijderen
if [[ -f ".env.backup" ]]; then
  say "Verwijder .env.backup (kan key bevatten)…"
  run "rm -f .env.backup"
  [[ "$DRY_RUN" == "1" ]] || good ".env.backup verwijderd"
else
  warn ".env.backup niet gevonden (prima)"
fi

# 2) .ruff_cache wissen
if [[ -d ".ruff_cache" ]]; then
  say "Wis .ruff_cache/ (kan key-strings in binaries bevatten)…"
  run "rm -rf .ruff_cache"
  [[ "$DRY_RUN" == "1" ]] || good ".ruff_cache gewist"
else
  warn ".ruff_cache/ niet gevonden (prima)"
fi

# 3) config/config_development.yaml patchen
CFG="config/config_development.yaml"
if [[ -f "$CFG" ]]; then
  say "Patch $CFG → hardcoded key vervangen door \${OPENAI_API_KEY}…"

  # Back-up maken (1x per run, als nog niet bestaat)
  BAK="$CFG.bak.$(date +%Y%m%d-%H%M%S)"
  run "cp \"$CFG\" \"$BAK\""
  [[ "$DRY_RUN" == "1" ]] || good "Backup gemaakt: $BAK"

  # macOS/BSD sed: -i '' voor in-place zonder extra backup-extensie
  # Regex:
  # - Zoekt naar lijnen met 'openai_api_key:' gevolgd door iets (waarde/hardcoded)
  # - Vervangt hele regel door 'openai_api_key: ${OPENAI_API_KEY}'
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY_RUN: sed -E -i '' 's|^[[:space:]]*openai_api_key:[[:space:]]*.*$|openai_api_key: \${OPENAI_API_KEY}|g' \"$CFG\""
  else
    sed -E -i '' 's|^[[:space:]]*openai_api_key:[[:space:]]*.*$|openai_api_key: ${OPENAI_API_KEY}|g' "$CFG"
    good "openai_api_key-regel vervangen door env-referentie"
  fi
else
  warn "$CFG niet gevonden — sla stap 3 over (prima als jouw config elders staat)"
fi

# 4) Eindscan: zoek mogelijke key-strings in repo (excl. node_modules/.git/.ruff_cache)
say "Eindscan op 'sk-' patronen (indicatie van gelekte keys)…"
SCAN_CMD="grep -RniE 'sk-[A-Za-z0-9_-]+' . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=.ruff_cache || true"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN: $SCAN_CMD"
else
  # shellcheck disable=SC2086
  MATCHES=$(eval $SCAN_CMD)
  if [[ -n "$MATCHES" ]]; then
    warn "Mogelijke key-achtige strings gevonden (controleer & verwijder/anonimiseer):"
    echo "$MATCHES"
  else
    good "Geen 'sk-' patronen meer gevonden in project (buiten uitgesloten mappen)."
  fi
fi

# 5) Tips: gitignore & history
say "Controleer je .gitignore zodat secrets niet gecommit worden. Suggestie:"
cat <<'EOF'
# Voeg dit toe aan .gitignore (indien nog niet aanwezig):
.env
.env.*
*.env
*secrets*.yaml
*_secrets.yaml
EOF

good "Klaar. Draai opnieuw met DRY_RUN=1 voor dry-run, of zonder voor echte wijzigingen."
