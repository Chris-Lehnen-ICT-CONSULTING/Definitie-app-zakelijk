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

repo_root=${LOCK_SYNC_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}
cd "$repo_root"

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
trap 'rm -r "$tmp"' EXIT INT TERM

# De lock dient als versievoorkeur én als vergelijkingsbasis: uv overschrijft
# het bestand, waarna de diff toont of de resolutie afwijkt van wat er gecommit
# staat.
cp requirements.txt "$tmp/req.check"
cp requirements-dev.txt "$tmp/req-dev.check"

compileer() {
    local bron=$1 doel=$2 err=$3
    shift 3
    if ! uv pip compile "$bron" --universal --generate-hashes --no-header \
        "$@" -o "$doel" >/dev/null 2>"$err"; then
        echo "FOUT: uv kan $bron niet resolven — is een lock handmatig bewerkt?" >&2
        sed -n '1,20p' "$err" >&2
        exit "$EXIT_RESOLVE"
    fi
}

compileer requirements.in "$tmp/req.check" "$tmp/req.err"
compileer requirements-dev.in "$tmp/req-dev.check" "$tmp/req-dev.err" -c requirements.txt

# --no-header op de compile, dus de eerste twee regels van de gecommitte lock
# (de uv-header) horen niet in de vergelijking.
vergelijk() {
    local lock=$1 vers=$2 bron=$3
    if ! sed '1,2d' "$lock" | diff - "$vers" > "$tmp/diff.out" 2>&1; then
        echo "FOUT: $lock niet in sync met $bron — draai 'make lock'" >&2
        sed -n '1,20p' "$tmp/diff.out" >&2
        exit "$EXIT_DESYNC"
    fi
}

vergelijk requirements.txt "$tmp/req.check" requirements.in
vergelijk requirements-dev.txt "$tmp/req-dev.check" requirements-dev.in

echo "OK: requirements-locks in sync met .in-bronnen."
exit "$EXIT_OK"
