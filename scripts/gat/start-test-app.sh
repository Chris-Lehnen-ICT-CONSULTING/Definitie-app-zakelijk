#!/usr/bin/env bash
# GAT-testapp starten/stoppen vanuit een git-worktree van de Definitie-app.
#
# Doel:
#   Een vast, voorspelbaar startscript waarmee een headless job (zonder iemand
#   achter de Mac) de Streamlit-testapp kan starten, controleren en stoppen.
#
# Gebruik:
#   scripts/gat/start-test-app.sh [start|stop|status|check] [--port N]
#     start   (standaard) start de app op de achtergrond en wacht max. 60 s
#     stop    stopt de app uit reports/gat-app-N.pid (alleen een streamlit-proces)
#     status  meldt of de app draait (PID + poort); exit 0 = draait, 1 = niet
#     check   alleen de controles, zonder iets te starten of te kopiëren
#   --port N  8502 t/m 8509 (standaard 8502); andere waarden geven exit 2.
#
# Veiligheidsgaranties:
#   - Draait alleen in een worktree; in de hoofdcheckout weigert het (exit 3),
#     zodat een test nooit de echte data/definities.db van de hoofdrepo raakt.
#   - De database van de hoofdrepo wordt alleen read-only geopend (mode=ro) om
#     eenmalig een consistente kopie te maken via de sqlite-backup-API. Een
#     bestaande kopie in de worktree blijft ongemoeid. Wijst de worktree-DB
#     (via symlink of hardlink) naar de hoofd-DB, dan weigert het (exit 3).
#   - <hoofdrepo>/.env wordt alleen geladen in de subshell die de app start:
#     geen kopie, geen symlink, en waarden worden nooit getoond of gelogd
#     (geen set -x, foutmeldingen van het inlezen worden onderdrukt).
#   - De app luistert alleen op 127.0.0.1. Een bezette poort wordt gemeld,
#     er wordt dan niets gestopt.
#   - stop beëindigt alleen een proces met "streamlit" én "--server.port N"
#     in de opdrachtregel.
#
# Exitcodes: 0 = ok, 1 = fout/poort bezet/draait niet, 2 = ongeldige invoer,
#            3 = veiligheidsweigering (hoofdcheckout, of DB wijst naar hoofd-DB).

set -euo pipefail

MIN_PORT=8502
MAX_PORT=8509
START_TIMEOUT=60
STOP_TIMEOUT=10

usage() {
  echo "Gebruik: $0 [start|stop|status|check] [--port N]  (N = ${MIN_PORT}..${MAX_PORT})" >&2
}

fout() {
  echo "FOUT: $*" >&2
}

# --- Argumenten -------------------------------------------------------------
ACTION=""
PORT="$MIN_PORT"
while [[ $# -gt 0 ]]; do
  case "$1" in
    start | stop | status | check)
      if [[ -n "$ACTION" ]]; then
        fout "meer dan één actie opgegeven."
        usage
        exit 2
      fi
      ACTION="$1"
      ;;
    --port)
      if [[ $# -lt 2 ]]; then
        fout "--port verwacht een waarde."
        usage
        exit 2
      fi
      PORT="$2"
      shift
      ;;
    --port=*)
      PORT="${1#--port=}"
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      fout "onbekend argument: $1"
      usage
      exit 2
      ;;
  esac
  shift
done
ACTION="${ACTION:-start}"

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || ((10#$PORT < MIN_PORT || 10#$PORT > MAX_PORT)); then
  fout "poort '$PORT' is niet toegestaan; alleen ${MIN_PORT} t/m ${MAX_PORT}."
  exit 2
fi
PORT=$((10#$PORT))

# --- Worktree-guard ---------------------------------------------------------
if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  fout "de werkmap ligt niet in een git-repository."
  exit 1
fi
GIT_DIR_ABS="$(cd "$(git rev-parse --absolute-git-dir)" && pwd -P)"
GIT_COMMON_ABS="$(cd "$(git rev-parse --path-format=absolute --git-common-dir)" && pwd -P)"
if [[ "$GIT_DIR_ABS" == "$GIT_COMMON_ABS" ]]; then
  fout "dit is de hoofdcheckout ($ROOT). Het script draait alleen in een git-worktree," \
    "zodat de echte data/definities.db nooit geraakt wordt. Maak een worktree" \
    "(git worktree add .worktrees/<naam> ...) en draai het script daar."
  exit 3
fi

MAIN_REPO="$(dirname "$GIT_COMMON_ABS")"
PY="$MAIN_REPO/.venv/bin/python"
ENV_FILE="$MAIN_REPO/.env"
SRC_DB="$MAIN_REPO/data/definities.db"
DB="$ROOT/data/definities.db"
REPORTS="$ROOT/reports"
LOG_FILE="$REPORTS/gat-app-$PORT.log"
PID_FILE="$REPORTS/gat-app-$PORT.pid"

cd "$ROOT"

# --- Hulpfuncties -----------------------------------------------------------
vereis_python() {
  if [[ ! -x "$PY" ]]; then
    fout "Python ontbreekt of is niet uitvoerbaar: $PY"
    exit 1
  fi
}

vereis_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    fout ".env ontbreekt in de hoofdrepo: $ENV_FILE"
    exit 1
  fi
}

# 0 = er luistert iets op 127.0.0.1:PORT, 1 = vrij.
poort_luistert() {
  "$PY" -c '
import socket, sys
s = socket.socket()
s.settimeout(0.5)
sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
' "$PORT"
}

# 0 = PID leeft en is de streamlit-app op deze poort (beschermt tegen
# PID-hergebruik door bijvoorbeeld de hoofdapp op een andere poort).
is_streamlit_proces() {
  local pid="$1" cmd
  cmd="$(ps -o command= -p "$pid" 2>/dev/null)" || return 1
  [[ "$cmd" == *streamlit* && "$cmd" == *"--server.port $PORT"* ]]
}

lees_pid() {
  local pid
  pid="$(tr -d '[:space:]' <"$PID_FILE")"
  if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
    fout "ongeldige inhoud in $PID_FILE"
    return 1
  fi
  echo "$pid"
}

# Weiger als de worktree-DB via een symlink of hardlink de hoofd-DB is: dan
# zou de testapp alsnog in de echte database schrijven.
vereis_eigen_database() {
  if [[ -L "$ROOT/data" || -L "$DB" ]] || [[ -e "$DB" && "$DB" -ef "$SRC_DB" ]]; then
    fout "data/ of data/definities.db in de worktree is een link (naar de hoofd-DB?)." \
      "Verwijder de link; het script maakt zelf een kopie."
    exit 3
  fi
}

controleer_database() {
  vereis_eigen_database
  if [[ -f "$DB" ]]; then
    echo "OK  database aanwezig in worktree: $DB"
  elif [[ -r "$SRC_DB" ]]; then
    echo "OK  database ontbreekt in worktree; kopie kan gemaakt worden uit: $SRC_DB"
  else
    fout "database ontbreekt in worktree én bron is niet leesbaar: $SRC_DB"
    exit 1
  fi
}

kopieer_database() {
  vereis_eigen_database
  if [[ -f "$DB" ]]; then
    echo "Database-kopie bestaat al, blijft ongemoeid: $DB"
    return 0
  fi
  if [[ ! -r "$SRC_DB" ]]; then
    fout "bron-database niet leesbaar: $SRC_DB"
    exit 1
  fi
  mkdir -p "$(dirname "$DB")"
  local tmp="$DB.tmp.$$"
  # Bron alleen read-only openen; eerst naar een tijdelijk bestand, daarna
  # atomair hernoemen zodat er nooit een halve kopie achterblijft.
  "$PY" -c '
import pathlib, sqlite3, sys
tmp = pathlib.Path(sys.argv[2])
try:
    src = sqlite3.connect(pathlib.Path(sys.argv[1]).resolve().as_uri() + "?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
except BaseException:
    tmp.unlink(missing_ok=True)
    raise
' "$SRC_DB" "$tmp"
  mv "$tmp" "$DB"
  echo "Database gekopieerd (sqlite-backup, bron read-only): $DB"
}

# Start de app losgekoppeld op de achtergrond, met .env alleen in deze subshell.
# Alle scriptwaarden komen binnen als positionele parameters: .env kan die niet
# overschrijven (een PORT= of PY= in .env verandert dus niets aan de start).
# Argumenten: <env-bestand> <python> <poort> <logbestand> <pid-bestand>
start_achtergrond() (
  set +u
  set -a
  # .env is dotenv-syntax; stderr weg zodat een parsefout geen waarde lekt.
  # shellcheck disable=SC1090
  . "$1" 2>/dev/null
  set +a
  nohup bash scripts/deployment/run_app.sh "$2" -m streamlit run src/main.py \
    --server.port "$3" --server.address 127.0.0.1 --server.headless true \
    --browser.gatherUsageStats false </dev/null >"$4" 2>&1 &
  echo "$!" >"$5"
)

# --- Acties -----------------------------------------------------------------
actie_check() {
  echo "OK  worktree: $ROOT"
  vereis_python
  echo "OK  python: $PY"
  vereis_env
  echo "OK  .env aanwezig in hoofdrepo (niet geladen, niet getoond)"
  controleer_database
  if poort_luistert; then
    fout "poort $PORT is bezet."
    exit 1
  fi
  echo "OK  poort $PORT is vrij"
  echo "Alle controles geslaagd."
}

actie_start() {
  vereis_python
  vereis_env
  if poort_luistert; then
    fout "poort $PORT is al bezet; er wordt niets gestart of gestopt."
    exit 1
  fi
  kopieer_database
  mkdir -p "$REPORTS"

  if ! start_achtergrond "$ENV_FILE" "$PY" "$PORT" "$LOG_FILE" "$PID_FILE"; then
    fout "de app kon niet op de achtergrond gestart worden."
    exit 1
  fi
  local pid
  pid="$(lees_pid)" || exit 1

  local i
  for ((i = 0; i < START_TIMEOUT; i++)); do
    # Eerst: leeft ons eigen proces nog? Anders geen vals succes als een
    # ander proces intussen de poort pakt.
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    if poort_luistert; then
      echo "GAT-testapp draait: http://127.0.0.1:$PORT (PID $pid)"
      exit 0
    fi
    sleep 1
  done

  fout "de app luistert niet binnen ${START_TIMEOUT} s op poort $PORT. Laatste 20 logregels ($LOG_FILE):"
  tail -n 20 "$LOG_FILE" >&2 || true
  # Een eigen, half-gestart proces niet laten rondzweven.
  if is_streamlit_proces "$pid"; then
    kill -TERM "$pid" 2>/dev/null || true
  fi
  rm -- "$PID_FILE"
  exit 1
}

actie_stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "Geen pid-bestand ($PID_FILE); er is niets te stoppen."
    exit 0
  fi
  local pid
  pid="$(lees_pid)" || exit 1
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "Proces $pid draait niet meer; verouderd pid-bestand opgeruimd."
    rm -- "$PID_FILE"
    exit 0
  fi
  if ! is_streamlit_proces "$pid"; then
    fout "PID $pid is geen streamlit-proces; niet gestopt. Verouderd pid-bestand opgeruimd."
    rm -- "$PID_FILE"
    exit 1
  fi

  # Kan intussen al gestopt zijn; dat vangt de wachtlus hieronder op.
  kill -TERM "$pid" 2>/dev/null || true
  local i
  for ((i = 0; i < STOP_TIMEOUT; i++)); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -- "$PID_FILE"
      echo "GAT-testapp gestopt (PID $pid, poort $PORT)."
      exit 0
    fi
    sleep 1
  done
  fout "PID $pid stopt niet binnen ${STOP_TIMEOUT} s na SIGTERM; pid-bestand blijft staan."
  exit 1
}

actie_status() {
  vereis_python
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(lees_pid)" || exit 1
    if is_streamlit_proces "$pid"; then
      if poort_luistert; then
        echo "GAT-testapp draait: http://127.0.0.1:$PORT (PID $pid)"
        exit 0
      fi
      echo "GAT-testapp-proces leeft (PID $pid), maar poort $PORT luistert (nog) niet."
      exit 1
    fi
    echo "GAT-testapp draait niet (verouderd pid-bestand: PID $pid)."
    exit 1
  fi
  if poort_luistert; then
    echo "GAT-testapp draait niet via dit script, maar poort $PORT is bezet door een ander proces."
  else
    echo "GAT-testapp draait niet (poort $PORT vrij)."
  fi
  exit 1
}

case "$ACTION" in
  check) actie_check ;;
  start) actie_start ;;
  stop) actie_stop ;;
  status) actie_status ;;
esac
