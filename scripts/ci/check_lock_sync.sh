#!/usr/bin/env bash
# Verifieer dat requirements*.txt een geldige resolutie is van de .in-bronnen.
#
# DEF-559/DEF-711. Deze gate toetst SYNC, niet ACTUALITEIT: hij vraagt of de
# gecommitte lock hoort bij de gecommitte bron, niet of de versies de nieuwste
# zijn. Die tweede as ligt elders — Dependabot levert versie-updates en
# `make audit` (pip-audit) bewaakt de CVE-kant.
#
# Waarom de lock als voorkeur wordt meegegeven: uv gebruikt een bestaand
# output-bestand als versievoorkeur, en `make lock` compileert naar het
# bestaande requirements.txt. Zonder die kopie compileert de check vrij en kiest
# hij de nieuwste versies, waardoor beide per definitie uiteenlopen zodra
# upstream een transitieve dependency uitbrengt — de check faalde dan zelfs
# direct na `make lock`.
#
# Exit-codes (bewust onderscheiden, zodat een test erop kan discrimineren;
# `make` slikt ze op en geeft altijd 2, dus roep dit script direct aan om ze te
# zien):
#   0  lock is in sync
#   1  lock is niet in sync met de .in — draai `make lock`
#   2  uv kan de .in niet resolven — mogelijk een handmatig bewerkte lock
#   3  randvoorwaarde ontbreekt (uv niet gevonden, bestand mist)

set -euo pipefail

EXIT_OK=0
EXIT_DESYNC=1
EXIT_RESOLVE=2
EXIT_PRECONDITIE=3

# Standaard script-relatief: het script ligt in scripts/ci/, dus twee niveaus
# omhoog is de repo-root. Dat voorkomt dat een aanroep vanuit een ándere
# git-repo stilzwijgend díé requirements-bestanden controleert. De env-override
# bestaat voor de tests.
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=${LOCK_SYNC_ROOT:-$(cd "$script_dir/../.." && pwd)}

if [ ! -d "$repo_root" ]; then
    echo "FOUT: $repo_root bestaat niet." >&2
    exit "$EXIT_PRECONDITIE"
fi
cd "$repo_root" || exit "$EXIT_PRECONDITIE"

if ! command -v uv >/dev/null 2>&1; then
    echo "FOUT: uv niet gevonden op PATH — installeer uv om de lock te verifiëren." >&2
    exit "$EXIT_PRECONDITIE"
fi

for bestand in requirements.in requirements.txt requirements-dev.in requirements-dev.txt; do
    if [ ! -f "$bestand" ]; then
        echo "FOUT: $bestand ontbreekt in $repo_root." >&2
        exit "$EXIT_PRECONDITIE"
    fi
done

tmp=$(mktemp -d)
# Alleen EXIT, en met -f. Een handler op INT/TERM ruimt wel op maar beeindigt
# het script niet, waardoor het doorloopt met een verwijderde tmpdir en de
# gebruiker een misleidende resolve-fout ziet; daarna zou de EXIT-trap er een
# tweede keer overheen gaan. Zonder -f kan die falende rm bovendien de exitcode
# van een geslaagde run overschrijven. EXIT vuurt ook bij een signaal.
trap 'rm -rf "$tmp"' EXIT

# De lock dient als versievoorkeur én als vergelijkingsbasis: uv overschrijft
# het bestand, waarna de diff toont of de resolutie afwijkt van wat er gecommit
# staat.
cp requirements.txt "$tmp/req.check"
cp requirements-dev.txt "$tmp/req-dev.check"

compileer() {
    local bron=$1 doel=$2 err=$3
    shift 3
    # ${1+"$@"} in plaats van "$@": onder `set -u` klapt een lege "$@" in
    # bash < 4.4 (macOS levert 3.2) op "unbound variable".
    if ! uv pip compile "$bron" --universal --generate-hashes --no-header \
        ${1+"$@"} -o "$doel" >/dev/null 2>"$err"; then
        echo "FOUT: uv kan $bron niet resolven — is een lock handmatig bewerkt?" >&2
        echo "      (uv $(uv --version 2>/dev/null | head -1))" >&2
        # Redactie: uv noemt index-URL's in resolve-fouten, en die kunnen
        # credentials dragen. Deze uitvoer landt in CI-joblogs.
        sed -n '1,20p' "$err" | sed -E 's#(://)[^/@[:space:]]+@#\1***@#g' >&2
        exit "$EXIT_RESOLVE"
    fi
}

compileer requirements.in "$tmp/req.check" "$tmp/req.err"
compileer requirements-dev.in "$tmp/req-dev.check" "$tmp/req-dev.err" -c requirements.txt

# De check compileert met --no-header, dus het leidende commentaarblok van de
# gecommitte lock hoort niet in de vergelijking.
#
# Dat blok wordt op INHOUD gestript, niet op een vast regelaantal. Een vaste
# `sed '1,2d'` koppelt de gate aan de huidige headervorm van uv: één regel erbij
# en de gate staat permanent rood op iets wat `make lock` niet oplost — precies
# de faalklasse die DEF-559 was. Bovendien maakt een blinde offset de eerste
# regels tot een ongecontroleerde zone, terwijl daar geldige pip-directives
# kunnen staan (`--index-url`, `--extra-index-url`, `--find-links`) die de
# installatiebron verleggen. Die beginnen niet met `#` en blijven nu dus in de
# vergelijking staan.
#
# De --no-header-uitvoer begint met een pakketnaam, en `# via`-regels zijn
# ingesprongen, dus die matchen `^#` niet.
vergelijk() {
    local lock=$1 vers=$2 bron=$3
    local status=0

    awk 'kop==0 && /^#/ {next} {kop=1; print}' "$lock" > "$tmp/lock-body" || status=$?
    if [ "$status" -ne 0 ]; then
        echo "FOUT: kan $lock niet lezen." >&2
        exit "$EXIT_PRECONDITIE"
    fi

    diff "$tmp/lock-body" "$vers" > "$tmp/diff.out" 2>&1 || status=$?
    if [ "$status" -eq 1 ]; then
        echo "FOUT: $lock niet in sync met $bron — draai 'make lock'" >&2
        sed -n '1,20p' "$tmp/diff.out" >&2
        exit "$EXIT_DESYNC"
    elif [ "$status" -ne 0 ]; then
        # diff-status >= 2 betekent "trouble" (ontbrekend of onleesbaar
        # bestand), geen inhoudelijk verschil. Dat als desync melden zou naar
        # `make lock` verwijzen terwijl dat niets oplost.
        echo "FOUT: kan $lock niet vergelijken met de verse resolutie." >&2
        sed -n '1,20p' "$tmp/diff.out" >&2
        exit "$EXIT_PRECONDITIE"
    fi
}

vergelijk requirements.txt "$tmp/req.check" requirements.in
vergelijk requirements-dev.txt "$tmp/req-dev.check" requirements-dev.in

echo "OK: requirements-locks in sync met .in-bronnen."
exit "$EXIT_OK"
