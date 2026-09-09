#!/usr/bin/env bash
# Grep Gate launcher (DEF-665).
#
# Het bestaande aanroeppad blijft ongewijzigd; de gate zelf staat in
# grep_gate.py, omdat de scope- en statuscontroles daar veilig te schrijven
# zijn. Deze wrapper voegt geen logica toe: de exitcode van de gate gaat
# ongewijzigd terug (0 = schoon, 1 = blokkerende bevinding, 2 = ongeldige scan).
#
# Gebruik: ENFORCE_GREP_GATE=true scripts/maintenance/grep_gate.sh
set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PY:-python3}" "$HIER/grep_gate.py" "$@"
