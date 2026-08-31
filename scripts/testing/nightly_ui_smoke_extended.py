#!/usr/bin/env python3
"""Extended deterministic UI smoke runner: legacy 3 cases plus 11 new GAT cases."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from nightly_ui_smoke import run_once as run_legacy_once
from streamlit.testing.v1 import AppTest


def _case(case_id: str, name: str, passed: bool, observed: object) -> dict[str, object]:
    return {"id": case_id, "name": name, "pass": bool(passed), "observed": observed}


def _run_additional_cases(app: AppTest, timeout: float) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []

    def add(cid, name, ok, observed):
        return cases.append(_case(cid, name, ok, observed))

    rag = next(
        (item for item in app.multiselect if item.key == "rag_collection_multiselect"),
        None,
    )
    add(
        "DEF-699",
        "RAG Collections opent met bruikbare toestand",
        bool(rag and rag.options),
        {"options": list(rag.options) if rag else []},
    )

    app.text_input(key="begrip_input").set_value("nachtelijke smoke-test").run(
        timeout=timeout
    )
    app.button(key="main_generate_btn").click().run(timeout=timeout)
    add(
        "DEF-689",
        "Genereren zonder context wordt geblokkeerd (negatief)",
        any("Minstens één context" in str(item.value) for item in app.warning)
        and any("Ontologische categorie" in str(item.value) for item in app.error),
        {
            "warnings": [str(item.value) for item in app.warning],
            "errors": [str(item.value) for item in app.error],
        },
    )

    app.button(key="main_clear_btn").click().run(timeout=timeout)
    cleared = next(
        (item for item in app.text_input if item.key == "begrip_input"), None
    )
    add(
        "DEF-691",
        "Wis Velden verwijdert invoer en oude resultaten",
        bool(cleared and cleared.value == ""),
        {"begrip": cleared.value if cleared else None},
    )
    app.button(key="main_check_btn").click().run(timeout=timeout)
    add(
        "DEF-690",
        "Duplicatencontrole zonder begrip toont validatiemelding",
        any("Voer eerst een begrip in" in str(item.value) for item in app.error),
        {"errors": [str(item.value) for item in app.error]},
    )

    app.radio[0].set_value("expert").run(timeout=timeout)
    expert_header = any(
        "👨‍💼 👨‍💼 Expert Review" in str(item.value) for item in app.markdown
    )
    app.radio[0].set_value("edit").run(timeout=timeout)
    edit_header = any("✏️ ✏️ Bewerk" in str(item.value) for item in app.markdown)
    add(
        "DEF-692",
        "Navigatietabs zijn wederzijds exclusief",
        expert_header
        and edit_header
        and not any(
            "🚀 🚀 Definitie Generatie" in str(item.value) for item in app.markdown
        ),
        {"expert_header": expert_header, "edit_header": edit_header},
    )

    app.radio[0].set_value("expert").run(timeout=timeout)
    app.selectbox(key="review_status_filter").set_value("Gearchiveerd").run(
        timeout=timeout
    )
    queue = [
        str(item.value)
        for item in app.markdown
        if "wachten op review" in str(item.value)
    ]
    add(
        "DEF-695",
        "Statusfilter van Review Wachtrij filtert de resultaten",
        not app.error
        and any("0 definities wachten op review" in item for item in queue),
        {"queue": queue, "errors": [str(item.value) for item in app.error]},
    )
    app.selectbox(key="review_status_filter").set_value("In review").run(
        timeout=timeout
    )
    app.checkbox(key="show_history").set_value(True).run(timeout=timeout)
    add(
        "DEF-696",
        "Reviewgeschiedenis tonen en verbergen",
        any("Recente Reviews" in str(item.value) for item in app.markdown),
        {
            "history_visible": any(
                "Recente Reviews" in str(item.value) for item in app.markdown
            )
        },
    )

    app.radio[0].set_value("edit").run(timeout=timeout)
    app.selectbox(key="edit_status_filter").set_value("Alle").run(timeout=timeout)
    if app.dataframe:
        definition_id = int(app.dataframe[0].value.iloc[0]["ID"])
        app.session_state["edit_selected_id"] = definition_id
        app.button(key="edit_btn_selected_table").click().run(timeout=timeout)
    auto_save = next(
        (item for item in app.checkbox if item.key == "auto_save_enabled"), None
    )
    add(
        "DEF-693",
        "Automatisch opslaan bewaart een bewerking",
        auto_save is not None,
        {"auto_save_control": bool(auto_save)},
    )

    definition_area = next(
        (
            item
            for item in app.text_area
            if item.key and item.key.endswith("_definitie")
        ),
        None,
    )
    if definition_area:
        definition_area.set_value("")
        for suffix in ("_org_multiselect", "_jur_multiselect", "_wet_multiselect"):
            field = next(
                (
                    item
                    for item in app.multiselect
                    if item.key and item.key.endswith(suffix)
                ),
                None,
            )
            if field:
                field.set_value([])
        app.run(timeout=timeout)
    save_button = next((item for item in app.button if item.key == "save_btn"), None)
    add(
        "DEF-694",
        "Lege definitie kan niet worden opgeslagen",
        bool(save_button and save_button.proto.disabled),
        {"save_disabled": bool(save_button and save_button.proto.disabled)},
    )

    app.radio[0].set_value("import_export_beheer").run(timeout=timeout)
    csv_uploader = next(
        (item for item in app.file_uploader if item.label == "Selecteer CSV bestand"),
        None,
    )
    if csv_uploader:
        csv_uploader.upload("invalid.csv", b"foo,bar\n1,2\n", "text/csv").run(
            timeout=timeout
        )
    add(
        "DEF-697",
        "Ongeldige CSV wordt atomair geweigerd",
        any("Missende verplichte kolommen" in str(item.value) for item in app.error),
        {"errors": [str(item.value) for item in app.error]},
    )

    export_results: list[str] = []
    for export_format in ("CSV", "Excel", "JSON", "TXT"):
        app.selectbox(key="bulk_format").set_value(export_format).run(timeout=timeout)
        app.button(key="bulk_export_btn").click().run(timeout=timeout)
        export_results.append(
            "ok"
            if any("Export gegenereerd" in str(item.value) for item in app.success)
            else "error"
        )
    add(
        "DEF-698",
        "Alle beschikbare exportformaten leveren leesbare bestanden",
        export_results == ["ok"] * 4,
        {"formats": export_results},
    )
    return cases


def run_once(app_path: str, timeout: float) -> dict[str, object]:
    result = run_legacy_once(app_path, timeout)
    try:
        app = AppTest.from_file(app_path).run(timeout=timeout)
        result["cases"].extend(_run_additional_cases(app, timeout))  # type: ignore[union-attr]
        result["pass"] = all(bool(case["pass"]) for case in result["cases"])  # type: ignore[index]
    except Exception as exc:
        result["pass"] = False
        result["error"] = repr(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="src/main.py")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_once(args.app, args.timeout)
    except Exception as exc:
        result = {
            "timestamp": datetime.now(UTC).isoformat(),
            "pass": False,
            "error": repr(exc),
        }
    result.setdefault("timestamp", datetime.now(UTC).isoformat())
    line = json.dumps(result, ensure_ascii=False)
    print(line)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
