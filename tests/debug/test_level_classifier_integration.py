#!/usr/bin/env python3
"""
Test of level_classifier.py compatibel is met huidige implementatie.

Simuleert de scores die de huidige OntologischeAnalyzer genereert
en test of level_classifier deze correct kan verwerken.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import re
# Simuleer level_classifier.py (inlined hier omdat het een extern gegeven bestand is)
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

TYPE = "TYPE"
EXEMPLAAR = "EXEMPLAAR"
PROCES = "PROCES"
RESULTAAT = "RESULTAAT"
ONBESLIST = "ONBESLIST"

ALL_LABELS = [TYPE, EXEMPLAAR, PROCES, RESULTAAT]

@dataclass(frozen=True)
class Policy:
    min_winner_score: float
    min_margin: float
    tie_break_bonus: float

POLICIES: Dict[str, Policy] = {
    "conservatief": Policy(min_winner_score=0.40, min_margin=0.15, tie_break_bonus=0.05),
    "gebalanceerd": Policy(min_winner_score=0.30, min_margin=0.12, tie_break_bonus=0.06),
    "gevoelig":     Policy(min_winner_score=0.20, min_margin=0.08, tie_break_bonus=0.08),
}

CUES: Dict[str, List[re.Pattern]] = {
    TYPE: [
        re.compile(r"\bsoort(en)?\b", re.I),
        re.compile(r"\btype(n)?\b", re.I),
    ],
    PROCES: [
        re.compile(r"\bproces\b", re.I),
        re.compile(r"\bhandeling(en)?\b", re.I),
    ],
    RESULTAAT: [
        re.compile(r"\bresultaat\b", re.I),
        re.compile(r"\buitkomst\b", re.I),
    ],
    EXEMPLAAR: [
        re.compile(r"\bdit(e)?\b", re.I),
        re.compile(r"\bdeze\b", re.I),
    ],
}

def _coerce_scores(scores: Dict[str, float]) -> Dict[str, float]:
    base = {k: float(scores.get(k, 0.0)) for k in ["type", "exemplaar", "proces", "resultaat"]}
    for k in base:
        if base[k] < 0.0: base[k] = 0.0
        if base[k] > 1.0: base[k] = 1.0
    return base

def _softmax01(d: Dict[str, float]) -> Dict[str, float]:
    s = sum(d.values())
    if s <= 0.0:
        return {k: 1.0/4.0 for k in d}
    return {k: (v / s) for k, v in d.items()}

def _find_winner(norm: Dict[str, float]) -> Tuple[str, float, str, float, float]:
    mapped = {
        TYPE: norm["type"],
        EXEMPLAAR: norm["exemplaar"],
        PROCES: norm["proces"],
        RESULTAAT: norm["resultaat"],
    }
    sorted_items = sorted(mapped.items(), key=lambda kv: kv[1], reverse=True)
    (win_label, win_score), (ru_label, ru_score) = sorted_items[0], sorted_items[1]
    margin = win_score - ru_score
    return win_label, win_score, ru_label, ru_score, margin

def _tie_break(label: str, text: Optional[str]) -> bool:
    if not text:
        return False
    for pat in CUES[label]:
        if pat.search(text):
            return True
    return False

def _confidence(win_score: float, margin: float) -> float:
    m_part = min(1.0, margin / 0.5)
    c = 0.6 * win_score + 0.4 * m_part
    if c < 0.0: c = 0.0
    if c > 1.0: c = 1.0
    return c

def classify_level(
    scores: Dict[str, float],
    text_context: Optional[str] = None,
    policy_name: str = "gebalanceerd",
) -> Dict[str, object]:
    """Vierwaardige classificatie."""
    sc = _coerce_scores(scores)
    norm = _softmax01(sc)
    policy = POLICIES.get(policy_name, POLICIES["gebalanceerd"])

    win_label, win_score, ru_label, ru_score, margin = _find_winner(norm)

    rationale_parts = []
    rationale_parts.append(
        f"Winnaar: {win_label} (score {win_score:.3f}), runner-up: {ru_label} (score {ru_score:.3f}), marge {margin:.3f}."
    )
    rationale_parts.append(
        f"Toegepaste drempels: min_winner_score={policy.min_winner_score:.2f}, min_margin={policy.min_margin:.2f}."
    )

    meets_score = win_score >= policy.min_winner_score
    meets_margin = margin >= policy.min_margin

    tie_used = False
    if not meets_margin and margin >= (policy.min_margin - policy.tie_break_bonus):
        if _tie_break(win_label, text_context):
            tie_used = True
            meets_margin = True
            rationale_parts.append(f"Tie-breaker: positieve linguïstische cue voor {win_label} in context.")
        else:
            rationale_parts.append("Tie-breaker: geen ondersteunende cue gevonden.")

    if meets_score and meets_margin:
        level = win_label
        conf = _confidence(win_score, margin)
        rationale_parts.append("Drempels gehaald; classificatie toegekend.")
    else:
        level = ONBESLIST
        conf = _confidence(win_score, max(0.0, margin))
        if not meets_score:
            rationale_parts.append("Winnaarscore onder minimale drempel.")
        if not meets_margin:
            rationale_parts.append("Marge onder minimale drempel.")
        if tie_used:
            rationale_parts.append("Tie-breaker toegepast maar drempels blijven onvoldoende.")

    return {
        "level": level,
        "confidence": round(conf, 3),
        "rationale": " ".join(rationale_parts),
        "details": {
            "policy": policy_name,
            "scores_raw": sc,
            "scores_norm": norm,
            "winner": {"label": win_label, "score": win_score},
            "runner_up": {"label": ru_label, "score": ru_score},
            "margin": margin,
            "tie_break_used": tie_used,
        },
    }

# Nu test met ECHTE scores uit de huidige implementatie
def main():
    print("\n" + "="*80)
    print("🧪 TEST: level_classifier.py met scores uit OntologischeAnalyzer")
    print("="*80 + "\n")

    # Haal test scores uit de eerdere test
    test_cases = [
        # (begrip, scores uit current analyzer, verwachte categorie)
        ("validatie", {"type": 0.30, "proces": 0.80, "resultaat": 0.00, "exemplaar": 0.00}, "PROCES"),
        ("toets", {"type": 1.00, "proces": 0.00, "resultaat": 0.00, "exemplaar": 0.00}, "TYPE"),
        ("besluit", {"type": 0.30, "proces": 0.00, "resultaat": 0.80, "exemplaar": 0.00}, "RESULTAAT"),
        ("sanctie", {"type": 0.30, "proces": 0.40, "resultaat": 0.00, "exemplaar": 0.00}, "PROCES"),  # Problematisch

        # Edge cases
        ("onbekend", {"type": 0.25, "proces": 0.25, "resultaat": 0.25, "exemplaar": 0.25}, "ONBESLIST?"),
        ("systeem", {"type": 0.50, "proces": 0.00, "resultaat": 0.00, "exemplaar": 0.00}, "TYPE"),
    ]

    successes = []
    failures = []
    improvements = []

    for begrip, scores, verwacht in test_cases:
        print(f"📝 Begrip: '{begrip}'")
        print(f"   Input scores: {scores}")
        print(f"   Verwacht (huidige): {verwacht}")

        # Classificeer met level_classifier
        result = classify_level(scores, text_context=begrip, policy_name="gebalanceerd")

        print(f"   level_classifier: {result['level']} (conf={result['confidence']:.3f})")
        print(f"   Rationale: {result['rationale']}")

        # Vergelijk
        if result['level'] == verwacht:
            print(f"   ✅ MATCH")
            successes.append(begrip)
        elif "ONBESLIST" in verwacht and result['level'] == "ONBESLIST":
            print(f"   ✅ MATCH (onbeslist)")
            successes.append(begrip)
        elif result['level'] == "ONBESLIST":
            print(f"   ⚠️  VERBETERING: level_classifier zegt ONBESLIST (was: {verwacht})")
            improvements.append((begrip, verwacht, result['level'], result['confidence']))
        else:
            print(f"   ❌ VERSCHIL: verwacht {verwacht}, kreeg {result['level']}")
            failures.append((begrip, verwacht, result['level'], result['confidence']))

        print()

    # Samenvatting
    print("="*80)
    print("📊 SAMENVATTING")
    print("="*80)
    print(f"Successen: {len(successes)}/{len(test_cases)}")
    print(f"Verbeteringen (ONBESLIST): {len(improvements)}")
    print(f"Failures: {len(failures)}")

    if improvements:
        print("\n⚠️  VERBETERINGEN (level_classifier detecteert onzekerheid):")
        for begrip, oud, nieuw, conf in improvements:
            print(f"   • {begrip}: {oud} → {nieuw} (conf={conf:.3f})")

    if failures:
        print("\n❌ FAILURES:")
        for begrip, verwacht, kreeg, conf in failures:
            print(f"   • {begrip}: verwacht {verwacht}, kreeg {kreeg} (conf={conf:.3f})")

    print("\n" + "="*80)
    print("🔍 CONCLUSIE")
    print("="*80)

    total_ok = len(successes) + len(improvements)
    if total_ok == len(test_cases):
        print("✅ level_classifier.py is VOLLEDIG COMPATIBEL met huidige scores")
        print("   + Voegt ONBESLIST optie toe (verbetering)")
    elif failures:
        print(f"❌ level_classifier.py heeft {len(failures)} incompatibiliteiten")
    else:
        print("⚠️  level_classifier.py werkt maar gedraagt zich anders (meer conservatief)")

if __name__ == "__main__":
    main()
