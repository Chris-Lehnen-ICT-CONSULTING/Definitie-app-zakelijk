#!/usr/bin/env python3
"""
Web Lookup Debug CLI

Doel: Snel een provider-lookup draaien en bij geen (of matige) resultaten
duidelijk zien waarom: statuscodes, strategies, attempts, errors.

Gebruik:
  PYTHONPATH=src python scripts/web_lookup_debug.py \
      --term "inverzekeringstelling" \
      --context "Sv" \
      --provider wetgeving \
      --timeout 12

Providers: wikipedia, wetgeving, overheid, rechtspraak, overheid_zoek
"""

import argparse
import asyncio
import json
import os
from typing import Any


async def main() -> int:
    from services.modern_web_lookup_service import ModernWebLookupService
    from services.interfaces import LookupRequest

    parser = argparse.ArgumentParser(description="Web Lookup Debug CLI")
    parser.add_argument("--term", required=True, help="Zoekterm")
    parser.add_argument(
        "--context",
        default="",
        help="Context string (bijv. 'Sv' of 'Wetboek van Strafvordering')",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=[None, "wikipedia", "wetgeving", "overheid", "rechtspraak", "overheid_zoek"],
        help="Beperk lookup tot 1 provider",
    )
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=float(os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", 10)))
    parser.add_argument("--json", action="store_true", help="Print raw JSON output")

    args = parser.parse_args()

    svc = ModernWebLookupService()
    sources = [args.provider] if args.provider else None
    req = LookupRequest(
        term=args.term,
        context=args.context or None,
        sources=sources,
        max_results=args.max_results,
        timeout=int(args.timeout),
        include_examples=False,
    )

    results = await svc.lookup(req)
    debug: dict[str, Any] | None = getattr(svc, "_last_debug", None)

    if args.json:
        out = {
            "results": [
                {
                    "provider": getattr(r.source, "name", ""),
                    "url": getattr(r.source, "url", ""),
                    "confidence": getattr(r.source, "confidence", 0.0),
                    "title": (r.metadata or {}).get("dc_title") or (r.metadata or {}).get("wikipedia_title"),
                    "definition": r.definition,
                    "metadata": r.metadata,
                }
                for r in (results or [])
            ],
            "debug": debug,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"Term: {args.term}")
    if args.context:
        print(f"Context: {args.context}")
    if sources:
        print(f"Provider: {sources}")
    print(f"Timeout: {args.timeout}s\n")

    print(f"Results: {len(results or [])}")
    for i, r in enumerate(results or [], 1):
        title = (r.metadata or {}).get("dc_title") or (r.metadata or {}).get("wikipedia_title") or "(geen titel)"
        print(
            f"{i}. {r.source.name} [{r.source.confidence:.2f}] — {title}\n   URL: {getattr(r.source, 'url', '')}\n   DEF: {(r.definition or '')[:200]}{'…' if (r.definition and len(r.definition) > 200) else ''}"
        )

    # Toon attempts/strategies/status bij geen of magere resultaten
    print("\nAttempts (strategies/status):")
    attempts = (debug or {}).get("attempts") if isinstance(debug, dict) else None
    if not attempts:
        print("  (geen attempts beschikbaar; provider kan Wikipedia-only zijn of er trad een vroege fout op)")
    else:
        for a in attempts:
            prov = a.get("provider") or a.get("endpoint")
            stage = a.get("stage")
            strat = a.get("strategy")
            status = a.get("status")
            records = a.get("records")
            error = a.get("error")
            parked = a.get("parked")
            url = a.get("url", "")
            print(
                f"- {prov} | stage={stage} strategy={strat} status={status} records={records} parked={parked} error={error}\n  URL: {url}"
            )

    # Suggesties bij 0 resultaten
    if not results:
        print("\nSuggesties:")
        print("- Voeg 'Sv' of 'Wetboek van Strafvordering' toe in --context voor strafvorderingstermen")
        print("- Probeer alternatieve schrijfwijzen: 'inverzekeringstelling' / 'in verzekeringstelling' / koppeltekenvariant")
        print("- Vergroot --timeout als endpoints traag antwoorden of er rate-limits zijn")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

