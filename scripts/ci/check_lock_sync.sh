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
    # -f zegt niets over leesbaarheid. Zonder deze controle klapt de latere `cp`
    # onder `set -e` op exit 1, wat volgens het contract "desync" betekent — en
    # dan verwijst de melding naar `make lock`, wat een rechtenprobleem niet
    # oplost.
    if [ ! -r "$bestand" ]; then
        echo "FOUT: $bestand is niet leesbaar in $repo_root." >&2
        exit "$EXIT_PRECONDITIE"
    fi
done

# Expliciete template: `mktemp -d` zonder template respecteert TMPDIR op GNU
# wel en op BSD/macOS niet — die kiest altijd /var/folders. Met een template is
# de locatie op beide platforms voorspelbaar, en daardoor ook toetsbaar.
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lock-sync.XXXXXX") || {
    echo "FOUT: kan geen tijdelijke map aanmaken." >&2
    exit "$EXIT_PRECONDITIE"
}
# Alleen EXIT, en met -f. Een handler op INT/TERM ruimt wel op maar beeindigt
# het script niet, waardoor het doorloopt met een verwijderde tmpdir en de
# gebruiker een misleidende resolve-fout ziet; daarna zou de EXIT-trap er een
# tweede keer overheen gaan. Zonder -f kan die falende rm bovendien de exitcode
# van een geslaagde run overschrijven. EXIT vuurt ook bij een signaal.
trap 'rm -rf "$tmp"' EXIT

# De lock dient als versievoorkeur én als vergelijkingsbasis: uv overschrijft
# het bestand, waarna de diff toont of de resolutie afwijkt van wat er gecommit
# staat. Een falende kopie is een randvoorwaarde-fout, geen desync.
cp requirements.txt "$tmp/req.check" || {
    echo "FOUT: kan requirements.txt niet kopiëren naar de werkmap." >&2
    exit "$EXIT_PRECONDITIE"
}
cp requirements-dev.txt "$tmp/req-dev.check" || {
    echo "FOUT: kan requirements-dev.txt niet kopiëren naar de werkmap." >&2
    exit "$EXIT_PRECONDITIE"
}

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

# Volgorde is load-bearing: eerst de runtime-lock compileren én vergelijken,
# pas daarna de dev-lock. De dev-compile gebruikt de gecommitte
# requirements.txt als constraint, net als `make lock` — maar `make lock` heeft
# die op dat moment al herschreven. Staat de runtime-lock uit de pas, dan botst
# de dev-resolve op de verouderde constraint en zou de gate een resolve-fout
# melden voor een probleem dat in werkelijkheid een runtime-desync is.
compileer requirements.in "$tmp/req.check" "$tmp/req.err"

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

compileer requirements-dev.in "$tmp/req-dev.check" "$tmp/req-dev.err" -c requirements.txt
vergelijk requirements-dev.txt "$tmp/req-dev.check" requirements-dev.in

echo "OK: requirements-locks in sync met .in-bronnen."
exit "$EXIT_OK"
