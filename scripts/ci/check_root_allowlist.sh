#!/usr/bin/env bash
set -euo pipefail

# Guard voor de rootregel uit instructions/blocks/definitie.policy.md
# (DEF-684, DEF-685, ALG-399): geen ad-hoc werk-, analyse-, resultaat- of
# databaseartefacten in de root.
#
# Sinds de trackingmigratie van ALG-399 is dat bronblok de normtekst; de native
# projectregels onder .claude/rules/ zijn gegenereerde verwijzingen zonder eigen
# beleid. ALLOWED_ROOT_FILES hieronder blijft de machineleesbare tegenhanger.
# Wijzigt de een, werk dan de ander bij: het bronblok verwijst terug naar dit
# script en tests/unit/scripts/test_check_root_allowlist.py bewaakt die
# koppeling. Een nieuw rootbestand toevoegen is daarmee een bewuste PR-stap.
#
# Gedrag, naar het model van check_no_root_db_files.sh:
# - CI (GITHUB_ACTIONS=true): faalt op elk GETRACKT rootbestand buiten de lijst.
# - Pre-commit (lokaal):      faalt op elk GESTAGED rootbestand buiten de lijst.
#
# Scope-grenzen, bewust:
# - Alleen bestanden in de root. Paden met een / zitten in een subdirectory en
#   worden overgeslagen; ad-hoc root-*mappen* vallen dus buiten deze guard
#   (open vraag 2 van DEF-685, apart af te wegen).
# - Alleen getrackte respectievelijk gestagede bestanden. Untracked bestanden
#   blijven buiten schot: deze guard bewaakt wat de repository publiceert, niet
#   wat iemand lokaal in de werkmap laat slingeren. Dat de gegenereerde
#   instructiepublicaties daadwerkelijk getrackt zijn, bewaakt een eigen poort
#   (scripts/check-instruction-publications.py --require-tracked).
#
# Optioneel argument: pad naar de te controleren repo-root (gebruikt door de
# tests, zodat de guard toetsbaar is zonder de echte werkmap aan te raken).

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Alleen een echte directory telt als doel. pre-commit kan bij een gewijzigde
# configuratie bestandsnamen meegeven; die mogen hier niet als root gelden.
TARGET_ROOT="${1:-}"
if [[ -n "$TARGET_ROOT" && ! -d "$TARGET_ROOT" ]]; then
  TARGET_ROOT=""
fi
if [[ -z "$TARGET_ROOT" ]]; then
  TARGET_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
cd "$TARGET_ROOT"

echo -e "${YELLOW}🔎 Rootbestanden toetsen aan de allowlist...${NC}"

# Fail-closed: zonder bruikbare git-werkboom kan de guard niets vaststellen.
# Zonder deze check zou een mislukte git-aanroep (geen repo, dubious ownership,
# kapotte index) een lege kandidatenlijst opleveren en dus ten onrechte groen.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo -e "${RED}❌ Geen bruikbare git-werkboom in: ${TARGET_ROOT}${NC}"
  echo
  echo "De guard kan niet vaststellen welke rootbestanden getrackt of gestaged"
  echo "zijn en faalt daarom gesloten, in plaats van onterecht groen te melden."
  exit 1
fi

# Toegestane rootbestanden. Globs volgen de normtekst van regel 1, maar zijn
# op de extensie afgesloten: een kaal requirements* zou ook requirements.bak of
# requirements-analyse.md toelaten, precies de categorie die hier weg moet.
ALLOWED_ROOT_FILES=(
  "README.md"
  "CLAUDE.md"
  "AGENTS.md"
  "Makefile"
  "CHANGELOG.md"
  "requirements*.in"
  "requirements*.txt"
  "pyproject.toml"
  "pytest.ini"
  ".pre-commit-config.yaml"
  ".gitignore"
  ".gitleaks.toml"
  ".gitleaksignore"
)

if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  MODE="ci"
else
  MODE="precommit"
fi

is_allowed() {
  local file="$1"
  local pattern
  for pattern in "${ALLOWED_ROOT_FILES[@]}"; do
    # shellcheck disable=SC2053  # rechterkant bewust ongequote: glob-match.
    if [[ "$file" == $pattern ]]; then
      return 0
    fi
  done
  return 1
}

# Schrijft de te controleren bestanden NUL-gescheiden naar stdout, zodat
# spaties in namen intact blijven. De aanroeper toetst de exitstatus.
list_candidates() {
  if [[ "$MODE" == "ci" ]]; then
    git ls-files -z
  elif git rev-parse --verify -q HEAD >/dev/null; then
    git diff --name-only --cached --diff-filter=ACMR -z
  else
    # Nog geen enkele commit: alles in de index is nieuw gestaged.
    git ls-files --cached -z
  fi
}

# Niet direct in een process substitution lezen: de exitstatus daarvan gaat
# verloren, waardoor een mislukte git-aanroep als "niets gevonden" zou passeren.
CANDIDATES_FILE="$(mktemp)"
trap 'rm -f "$CANDIDATES_FILE"' EXIT

if ! list_candidates >"$CANDIDATES_FILE"; then
  echo -e "${RED}❌ Git leverde geen bruikbare bestandslijst (modus: ${MODE}).${NC}"
  echo
  echo "De guard faalt gesloten in plaats van onterecht groen te melden."
  exit 1
fi

unknown_files=()

while IFS= read -r -d '' file; do
  # Alleen de root: paden met een / zitten in een subdirectory.
  case "$file" in
  */*) continue ;;
  "") continue ;;
  esac

  if ! is_allowed "$file"; then
    unknown_files+=("$file")
  fi
done <"$CANDIDATES_FILE"

has_violations=0

if [[ ${#unknown_files[@]} -gt 0 ]]; then
  has_violations=1
  echo -e "${RED}❌ Rootbestanden buiten de allowlist:${NC}"
  for file in "${unknown_files[@]}"; do
    echo "  - $file"
  done
  echo
  echo "In de root horen uitsluitend native projectinstructies en standaard"
  echo "repository-, build-, test- en securityconfiguratie."
  echo "Verplaats werk-, analyse- en resultaatbestanden naar de daarvoor bestemde"
  echo "subdirectory (docs/, project-documentation/, reports/, scripts/)."
  echo
  if [[ "$MODE" == "ci" ]]; then
    # In CI is het bestand al gecommit; unstagen helpt dan niet meer.
    echo "Verwijder het uit de index met: git rm --cached <bestand>"
    echo "en commit die verwijdering; het bestand zelf blijft lokaal staan."
  else
    echo "Dit blokkeert onder meer een onbedoelde 'git add -A'."
    echo "Herstel met: git restore --staged <bestand>"
  fi
  echo
  echo "Hoort het bestand hier wel thuis? Voeg het dan bewust toe aan"
  echo "ALLOWED_ROOT_FILES in scripts/ci/check_root_allowlist.sh én aan de"
  echo "rootregel in instructions/blocks/definitie.policy.md; genereer daarna de"
  echo "instructiepublicaties opnieuw."
fi

if [[ "$has_violations" -eq 1 ]]; then
  exit 1
fi

echo -e "${GREEN}✅ Alle rootbestanden staan op de allowlist.${NC}"
