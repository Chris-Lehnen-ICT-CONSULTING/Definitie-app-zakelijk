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

# --write genereert de locks (wat `make lock` doet); zonder vlag verifieert het
# script alleen. Eén implementatie voor beide, zodat de vlaggenset en de
# versievoorkeur niet uiteen kunnen lopen — die drift maakte de gate eerder
# structureel rood op iets wat `make lock` niet oploste.
MODUS="check"
if [ "$#" -gt 1 ]; then
    echo "FOUT: te veel argumenten (verwacht: --write of niets)." >&2
    exit "$EXIT_PRECONDITIE"
fi
case "${1:-}" in
    --write) MODUS="write" ;;
    "") ;;
    *)
        echo "FOUT: onbekend argument $1 (verwacht: --write of niets)." >&2
        exit "$EXIT_PRECONDITIE"
        ;;
esac

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

# De .in-bronnen zijn altijd vereist. De locks alleen in check-modus: in
# write-modus zijn ze de uitvoer, en moet een ontbrekende lock juist opgebouwd
# kunnen worden. De oude `uv pip compile -o requirements.txt` kon dat ook.
vereist="requirements.in requirements-dev.in"
if [ "$MODUS" = check ]; then
    vereist="$vereist requirements.txt requirements-dev.txt"
fi

for bestand in $vereist; do
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

# De lock gaat als versievoorkeur naar het compile-doel, maar ZONDER hashes.
#
# uv neemt uit een bestaand -o-bestand niet alleen de versies over maar ook de
# hashes: het herberekent ze niet. Een lock met gemanipuleerde of verouderde
# hashes zou daardoor zijn eigen corruptie erven, waarna de diff die corruptie
# met zichzelf vergelijkt en de gate groen meldt. Geverifieerd met uv 0.12.9:
# een lock met alle hashes op nul gaf exit 0, terwijl
# `uv pip install --require-hashes` op diezelfde lock afbrak op een mismatch.
#
# Met alleen de versieregels als voorkeur houdt uv de pins vast — dus geen valse
# desync bij een upstream-release — en berekent hij de hashes opnieuw, zodat de
# vergelijking ze echt toetst.
versie_voorkeur() {
    local lock=$1 doel=$2
    local status=0

    # In write-modus mag de lock ontbreken: dan is er geen voorkeur en resolvet
    # uv vrij, wat precies is wat je wilt bij een eerste opbouw.
    if [ ! -f "$lock" ]; then
        : > "$doel"
        return
    fi

    # Hash-regels eruit, en de line-continuation die bij de pinregel hoorde.
    # grep-status: 0 = regels over, 1 = niets over (een lege lock is geldig,
    # dan is er simpelweg geen voorkeur), >1 = echte fout.
    grep -vE '^[[:space:]]+--hash=' "$lock" > "$tmp/zonder-hash" || status=$?
    if [ "$status" -gt 1 ]; then
        echo "FOUT: kan $lock niet uitlezen voor de versievoorkeur." >&2
        exit "$EXIT_PRECONDITIE"
    fi

    if ! sed 's/ \\$//' "$tmp/zonder-hash" > "$doel"; then
        echo "FOUT: kan de versievoorkeur voor $lock niet schrijven." >&2
        exit "$EXIT_PRECONDITIE"
    fi
}

versie_voorkeur requirements.txt "$tmp/req.check"
versie_voorkeur requirements-dev.txt "$tmp/req-dev.check"

compileer() {
    local bron=$1 doel=$2 err=$3
    shift 3
    local kop=()
    # In check-modus vergelijken we alleen de body, dus zonder header. In
    # write-modus hoort de header er wel in: die documenteert het commando
    # waarmee de lock gereproduceerd wordt.
    #
    # --custom-compile-command is daarbij essentieel. Zonder die vlag schrijft
    # uv het letterlijke commando in de header, inclusief het willekeurige
    # mktemp-pad waar we naartoe compileren. Dat lekt een lokaal pad naar de
    # repo en levert bij elke `make lock` een andere header, dus altijd een diff.
    if [ "$MODUS" = check ]; then
        kop=(--no-header)
    else
        kop=(--custom-compile-command "make lock")
    fi
    # ${1+"$@"} in plaats van "$@": onder `set -u` klapt een lege "$@" in
    # bash < 4.4 (macOS levert 3.2) op "unbound variable".
    # ${kop[@]+...} en ${1+...}: een lege array of lege argumentenlijst klapt
    # onder `set -u` op bash 3.2, dat macOS nog levert.
    if ! uv pip compile "$bron" --universal --generate-hashes \
        ${kop[@]+"${kop[@]}"} ${1+"$@"} -o "$doel" >/dev/null 2>"$err"; then
        echo "FOUT: uv kan $bron niet resolven — is een lock handmatig bewerkt?" >&2
        echo "      (uv $(uv --version 2>/dev/null | head -1))" >&2
        # Redactie: uv noemt index-URL's en tokens in resolve-fouten. Zowel
        # userinfo vóór @ als query-parameters kunnen credentials dragen, en
        # deze uitvoer landt in CI-joblogs.
        # Alle query-waarden maskeren, niet een lijst van bekende sleutelnamen:
        # zo een allowlist mist er altijd een (access_token, refresh_token, ...)
        # en groeit alleen maar. Sleutelnamen zelf blijven zichtbaar, zodat de
        # melding diagnosticeerbaar blijft.
        sed -n '1,20p' "$err" \
            | sed -E -e 's#(://)[^/@[:space:]]+@#\1***@#g' \
                     -e 's#([?&][A-Za-z0-9_.-]+=)[^&[:space:]]+#\1***#g' >&2
        exit "$EXIT_RESOLVE"
    fi
}

# Vervang een lock atomair: eerst naast het doel neerzetten, dan hernoemen.
# Een rechtstreekse `cp` kan bij een fout halverwege een afgekapt bestand
# achterlaten — waargenomen: 341 bytes werd 17 bytes bij een geïnjecteerde
# kopieerfout. Een `mv` binnen hetzelfde filesystem is wel atomair.
schrijf() {
    local vers=$1 doel=$2
    local tijdelijk="$doel.nieuw.$$"

    if ! cp "$vers" "$tijdelijk"; then
        rm -f "$tijdelijk"
        echo "FOUT: kan $doel niet voorbereiden." >&2
        exit "$EXIT_PRECONDITIE"
    fi
    if ! mv "$tijdelijk" "$doel"; then
        rm -f "$tijdelijk"
        echo "FOUT: kan $doel niet vervangen." >&2
        exit "$EXIT_PRECONDITIE"
    fi
    echo "  geschreven: $doel"
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

if [ "$MODUS" = check ]; then
    vergelijk requirements.txt "$tmp/req.check" requirements.in
else
    # De runtime-lock moet er staan vóór de dev-resolve, want die gebruikt hem
    # als constraint — en dat pad belandt in de `# via`-annotaties van de
    # dev-lock. Een tijdelijk pad meegeven zou daar een willekeurige
    # /var/folders-locatie inschrijven, waardoor elke run een andere lock geeft.
    # Daarom schrijven we hier al, met een backup voor rollback als de
    # dev-resolve alsnog faalt.
    if [ -f requirements.txt ]; then
        cp requirements.txt "$tmp/req.backup" || {
            echo "FOUT: kan geen backup van requirements.txt maken." >&2
            exit "$EXIT_PRECONDITIE"
        }
        HERSTEL_RUNTIME=1
    fi
    schrijf "$tmp/req.check" requirements.txt
fi

# De dev-resolve gebruikt de runtime-lock als constraint, met een relatief pad
# zodat de annotatie in de dev-lock reproduceerbaar blijft.
if [ "$MODUS" = write ]; then
    # Rollback bij een falende dev-resolve: anders blijft een bijgewerkte
    # runtime-lock naast een ongewijzigde dev-lock achter.
    trap 'status=$?; if [ "$status" -ne 0 ] && [ "${HERSTEL_RUNTIME:-0}" = 1 ]; then
            cp "$tmp/req.backup" requirements.txt 2>/dev/null || true
            echo "  requirements.txt teruggedraaid" >&2
          fi
          rm -rf "$tmp"' EXIT
fi

compileer requirements-dev.in "$tmp/req-dev.check" "$tmp/req-dev.err" -c requirements.txt

if [ "$MODUS" = write ]; then
    schrijf "$tmp/req-dev.check" requirements-dev.txt
    HERSTEL_RUNTIME=0
    echo "OK: requirements-locks gegenereerd uit de .in-bronnen."
else
    vergelijk requirements-dev.txt "$tmp/req-dev.check" requirements-dev.in
    echo "OK: requirements-locks in sync met .in-bronnen."
fi
exit "$EXIT_OK"
