#!/bin/bash
# Herhaling van proef C1 met machinaal vastgelegde exitstatus (SC-17). Coördinator A (Cowork), 25-09-2026.
set -u
cd /Users/chrislehnen/Projecten/Definitie-app || exit 2
OUT=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/a-cowork/bewijs
[ -f "$OUT/proef-c1-uitkomsten-run1.json" ] || cp "$OUT/proef-c1-uitkomsten.json" "$OUT/proef-c1-uitkomsten-run1.json"
[ -f "$OUT/proef-c1-run1.log" ] || cp "$OUT/proef-c1-run.log" "$OUT/proef-c1-run1.log"
START=$(date -u +%FT%TZ)
PYTHONPATH=src .venv/bin/python "$OUT/proef-c1-run.py" > "$OUT/proef-c1-run2.log" 2>&1
EXIT=$?
END=$(date -u +%FT%TZ)
python3 - "$OUT" "$START" "$END" "$EXIT" "$(git rev-parse HEAD)" <<'PY'
import json,sys
out,start,end,ex,commit=sys.argv[1:6]
rec={"proef":"C1 run2 (herhaling voor machinaal vastgelegde exitstatus, SC-17)","command":f"cd /Users/chrislehnen/Projecten/Definitie-app && PYTHONPATH=src .venv/bin/python {out}/proef-c1-run.py","start_utc":start,"end_utc":end,"exit_status":int(ex),"commit":commit,"uitkomsten":"proef-c1-uitkomsten.json (run2); run1 bewaard als proef-c1-uitkomsten-run1.json","vastgelegd_door":"proef-c1-run2.sh op de Mac (bash), gestart door coördinator A (Cowork) via osascript"}
r1=json.load(open(f"{out}/proef-c1-uitkomsten-run1.json"))["toetsing"]; r2=json.load(open(f"{out}/proef-c1-uitkomsten.json"))["toetsing"]
rec["toetsing_run1_gelijk_run2"]=(json.dumps(r1,sort_keys=True)==json.dumps(r2,sort_keys=True))
json.dump(rec,open(f"{out}/proef-c1-uitvoering-run2.json","w"),ensure_ascii=False,indent=2)
print(json.dumps(rec,ensure_ascii=False))
PY
