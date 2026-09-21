"""DEF-766 correctieronde 2, punt C — deterministische transportproef (geen modelcall).

Reproduceert en toetst de verbindingsfout bij hergebruik van de gedeelde
providerclient over opeenvolgende UI-eventloops, met de échte stack
(`anthropic.AsyncAnthropic` → httpx-verbindingspool) tegen een lokale fake
Anthropic-server op loopback (keep-alive). Geen netwerk buiten de machine,
geen echte sleutel, geen betaalde aanroep.

Waarom een script en geen pytest: de verplichte offline-testgate (DEF-519,
`tests/offline_bootstrap.py`) blokkeert álle `socket.connect`, ook loopback.
De pytest-regressietests (`tests/unit/services/test_def766_ess03_eventloop_
transport.py`) toetsen dezelfde correctie op de SDK-grens met een fake SDK
die aan de loop van het eerste gebruik gebonden is.

Drie proeven, elk over drie opeenvolgende `asyncio.run()`-loops zoals
`ui.helpers.async_bridge.run_async` die maakt:
1. kale `AsyncAnthropic` (max_retries=0): loop 2 faalt met
   `APIConnectionError` ← `RuntimeError: Event loop is closed`; loop 3 slaagt;
2. `AnthropicClient(rebind_on_new_loop=False)` → `AIServiceV2` →
   `Ess03AssessmentService` via `run_async`: aanroep 2 is `error/connection`;
3. `AnthropicClient()` (correctie) → dezelfde keten: 3× `assessed`,
   `attempts_observed` 1, server ontvangt 3 requests.

Gebruik:
    python scripts/ess03/proef_eventloop_transport.py [--uit pad.json]
Exitcode 0 = alle drie proeven leverden het verwachte gedrag; anders 1.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ.setdefault("AI_SDK_MAX_RETRIES", "0")

ANTWOORD = {
    "verdict": "not_applicable",
    "applicability": "not_applicable",
    "unit": None,
    "reason": "Stoflezing zonder gekozen telbare eenheid (synthetische proef).",
    "evidence": [{"location": "definition", "quote": "Vloeistof bestaande uit H2O."}],
    "missing_information": None,
    "question": None,
    "uncertainty": None,
}


class _FakeAnthropic(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    requests: list[float] = []

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _FakeAnthropic.requests.append(time.time())
        body = json.dumps(
            {
                "id": "msg_fake",
                "type": "message",
                "role": "assistant",
                "model": "claude-fake",
                "content": [
                    {"type": "text", "text": json.dumps(ANTWOORD, ensure_ascii=False)}
                ],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 10, "output_tokens": 20},
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        return


class _Router:
    def get_model(self, task_type: str) -> tuple[str, str]:
        return "anthropic", "claude-fake"

    def accepts_temperature(self, model: str, provider: str | None = None) -> bool:
        return False


def _keten(**clientopties: Any) -> Any:
    from services.ai.anthropic_client import AnthropicClient
    from services.ai_service_v2 import AIServiceV2
    from services.validation.ess03_assessment_service import Ess03AssessmentService
    from utils.async_api import RateLimitConfig

    client = AnthropicClient(
        api_key="sk-ant-proef", timeout=5, max_retries=0, **clientopties
    )
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=1, backoff_factor=1.0),
        use_cache=False,
        ai_client=client,
        model_router=_Router(),
    )
    return Ess03AssessmentService(ai, model_router=_Router(), cache_size=0)


def _beoordeel(dienst: Any) -> dict[str, Any]:
    from ui.helpers.async_bridge import run_async

    start = time.perf_counter()
    d = run_async(
        dienst.assess(
            "water",
            "Vloeistof bestaande uit H2O.",
            {"organisatorische_context": ["Synthetisch Lab"]},
            [],
            correlation_id="def766-c-proef",
        )
    ).als_dict()
    return {
        "status": d["status"],
        "error": d.get("error"),
        "verdict": (d.get("judgment") or {}).get("verdict"),
        "attempts_observed": d["attribution"].get("attempts_observed"),
        "duur_s": round(time.perf_counter() - start, 3),
    }


def proef_1_kale_sdk() -> dict[str, Any]:
    import anthropic
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key="sk-ant-proef", max_retries=0, timeout=5)

    async def _call() -> str:
        r = await client.messages.create(
            model="claude-fake",
            max_tokens=5,
            messages=[{"role": "user", "content": "x"}],
        )
        return r.content[0].text

    uit: list[dict[str, Any]] = []
    for _ in range(3):
        try:
            asyncio.run(_call())
            uit.append({"ok": True})
        except anthropic.APIConnectionError as e:
            uit.append(
                {
                    "ok": False,
                    "fout": f"{type(e).__name__}: {e}",
                    "oorzaak": f"{type(e.__cause__).__name__}: {e.__cause__}",
                }
            )
    verwacht = (
        uit[0]["ok"]
        and not uit[1]["ok"]
        and "Event loop is closed" in uit[1]["oorzaak"]
        and uit[2]["ok"]
    )
    return {
        "naam": "kale AsyncAnthropic over 3 loops",
        "aanroepen": uit,
        "conform": verwacht,
    }


def proef_2_zonder_correctie() -> dict[str, Any]:
    dienst = _keten(rebind_on_new_loop=False)
    uit = [_beoordeel(dienst) for _ in range(3)]
    conform = (
        uit[0]["status"] == "assessed"
        and uit[1]["status"] == "error"
        and (uit[1]["error"] or {}).get("type") == "connection"
        and uit[2]["status"] == "assessed"
    )
    return {
        "naam": "keten zonder correctie (rebind_on_new_loop=False)",
        "aanroepen": uit,
        "conform": conform,
    }


def proef_3_met_correctie() -> dict[str, Any]:
    voor = len(_FakeAnthropic.requests)
    dienst = _keten()
    uit = [_beoordeel(dienst) for _ in range(3)]
    conform = (
        all(u["status"] == "assessed" and u["attempts_observed"] == 1 for u in uit)
        and len(_FakeAnthropic.requests) - voor == 3
    )
    return {
        "naam": "keten met correctie (standaard)",
        "aanroepen": uit,
        "conform": conform,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uit", type=Path, default=None)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeAnthropic)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        proeven = [
            proef_1_kale_sdk(),
            proef_2_zonder_correctie(),
            proef_3_met_correctie(),
        ]
    finally:
        server.shutdown()
        server.server_close()
    rapport = {
        "schema": "def766-eventloop-transportproef/1",
        "gestart": datetime.now(UTC).isoformat(),
        "server": "lokale fake /v1/messages op loopback, keep-alive; geen netwerk, geen sleutel",
        "requests_ontvangen": len(_FakeAnthropic.requests),
        "proeven": proeven,
        "alle_conform": all(p["conform"] for p in proeven),
    }
    tekst = json.dumps(rapport, ensure_ascii=False, indent=2)
    if args.uit:
        args.uit.write_text(tekst, encoding="utf-8")
    print(tekst)
    return 0 if rapport["alle_conform"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
