#!/usr/bin/env bash
set -euo pipefail

# Guard voor regel 1 van .claude/rules/project-rules.md (DEF-684, DEF-685):
# geen ad-hoc werk-, analyse-, resultaat- of databaseartefacten in de root.
#
# ALLOWED_ROOT_FILES hieronder is de machineleesbare tegenhanger van die regel.
# Wijzigt de een, werk dan de ander bij: de rule verwijst terug naar dit script.
# Een nieuw rootbestand toevoegen is daarmee een bewuste PR-stap.
#
# Gedrag, naar het model van check_no_root_db_files.sh:
# - CI (GITHUB_ACTIONS=true): faalt op elk GETRACKT rootbestand buiten de lijst.
# - Pre-commit (lokaal):      faalt op elk GESTAGED rootbestand buiten de lijst.
#
# Untracked bestanden blijven buiten schot. De guard forceert het openstaande
# trackingbesluit uit ALG-399 dus niet.
#
# Optioneel argument: pad naar de te controleren repo-root (gebruikt door de
# tests, zodat de guard toetsbaar is zonder de echte werkmap aan te raken).

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

TARGET_ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$TARGET_ROOT"

# Toegestane rootbestanden. Globs volgen de normtekst van regel 1.
ALLOWED_ROOT_FILES=(
  "README.md"
  "CLAUDE.md"
  "Makefile"
  "CHANGELOG.md"
  "requirements*"
  "pyproject.toml"
  "pytest.ini"
  ".pre-commit-config.yaml"
  ".gitignore"
  ".gitleaks*"
)

# AGENTS.md hoort volgens regel 1 in de root, maar blijft tot het besluit in
# ALG-399 ongetrackte, gegenereerde build-output. Daarom staat het bewust niet
# op de allowlist: het krijgt een eigen melding zodra het toch getrackt of
# gestaged wordt. Valt in ALG-399 het besluit "committen", dan verhuist deze
# naam naar ALG-399 en naar ALLOWED_ROOT_FILES hierboven.
DEFERRED_TRACKING_FILE="AGENTS.md"

echo -e "${YELLOW}🔎 Checking root-level files against the allowlist...${NC}"

is_allowed() {
  local bestand="$1"
  local patroon
  for patroon in "${ALLOWED_ROOT_FILES[@]}"; do
    # shellcheck disable=SC2053  # rechterkant bewust ongequote: glob-match.
    if [[ "$bestand" == $patroon ]]; then
      return 0
    fi
  done
  return 1
}

# Levert de te controleren bestanden, NUL-gescheiden zodat spaties in namen
# intact blijven.
list_candidates() {
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    git ls-files -z
  elif git rev-parse --verify -q HEAD >/dev/null; then
    git diff --name-only --cached --diff-filter=ACMR -z
  else
    # Nog geen enkele commit: alles in de index is nieuw gestaged.
    git ls-files --cached -z
  fi
}

unknown_files=()
deferred_files=()

while IFS= read -r -d '' bestand; do
  # Alleen de root: paden met een / zitten in een subdirectory.
  case "$bestand" in
  */*) continue ;;
  "") continue ;;
  esac

  if [[ "$bestand" == "$DEFERRED_TRACKING_FILE" ]]; then
    deferred_files+=("$bestand")
  elif ! is_allowed "$bestand"; then
    unknown_files+=("$bestand")
  fi
done < <(list_candidates)

heeft_violaties=0

if [[ ${#deferred_files[@]} -gt 0 ]]; then
  heeft_violaties=1
  echo -e "${RED}❌ ${DEFERRED_TRACKING_FILE} mag niet worden gestaged of gecommit:${NC}"
  for bestand in "${deferred_files[@]}"; do
    echo "  - $bestand"
  done
  echo
  echo "Regel 1 van .claude/rules/project-rules.md houdt ${DEFERRED_TRACKING_FILE} tot het"
  echo "besluit in ALG-399 ongetrackte, gegenereerde build-output. Dit blokkeert"
  echo "onder meer een onbedoelde 'git add -A'."
  echo "Herstel met: git restore --staged ${DEFERRED_TRACKING_FILE}"
fi

if [[ ${#unknown_files[@]} -gt 0 ]]; then
  heeft_violaties=1
  echo -e "${RED}❌ Rootbestanden buiten de allowlist:${NC}"
  for bestand in "${unknown_files[@]}"; do
    echo "  - $bestand"
  done
  echo
  echo "In de root horen uitsluitend native projectinstructies en standaard"
  echo "repository-, build-, test- en securityconfiguratie."
  echo "Verplaats werk-, analyse- en resultaatbestanden naar de daarvoor bestemde"
  echo "subdirectory (docs/, project-documentation/, reports/, scripts/)."
  echo
  echo "Hoort het bestand hier wel thuis? Voeg het dan bewust toe aan"
  echo "ALLOWED_ROOT_FILES in scripts/ci/check_root_allowlist.sh én aan regel 1"
  echo "van .claude/rules/project-rules.md."
fi

if [[ "$heeft_violaties" -eq 1 ]]; then
  exit 1
fi

echo -e "${GREEN}✅ All root-level files are on the allowlist.${NC}"
