"""CLI voor performance metrics en baseline management.

Usage:
    python -m src.cli.performance_cli status
    python -m src.cli.performance_cli baselines
    python -m src.cli.performance_cli history app_startup_ms
"""

import sys
from pathlib import Path

# Add src to path for proper imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from datetime import datetime

import click

from monitoring.performance_tracker import get_tracker


@click.group()
def performance():
    """Performance baseline management commands."""


@performance.command()
def status():
    """Show overall performance status met baseline vergelijkingen."""
    tracker = get_tracker()
    baselines = tracker.get_all_baselines()

    if not baselines:
        click.echo("Geen performance baselines beschikbaar.")
        click.echo("Draai de applicatie enkele keren om baselines te genereren.")
        return

    click.echo("\n=== Performance Status ===\n")

    for baseline in baselines:
        # Haal meest recente metric op
        recent_metrics = tracker.get_recent_metrics(baseline.metric_name, limit=1)

        if recent_metrics:
            recent = recent_metrics[0]
            ratio = recent.value / baseline.baseline_value
            deviation_pct = (ratio - 1.0) * 100

            # Status indicator
            if ratio >= 1.20:
                status = "CRITICAL"
                icon = "🔴"
            elif ratio >= 1.10:
                status = "WARNING"
                icon = "🟡"
            else:
                status = "OK"
                icon = "🟢"

            click.echo(f"{icon} {baseline.metric_name}")
            click.echo(f"   Huidig:   {recent.value:.1f}")
            click.echo(f"   Baseline: {baseline.baseline_value:.1f}")
            click.echo(f"   Afwijking: {deviation_pct:+.1f}%")
            click.echo(f"   Status:   {status}")
            click.echo(
                f"   Confidence: {baseline.confidence:.0%} ({baseline.sample_count} samples)"
            )
        else:
            click.echo(f"⚪ {baseline.metric_name}")
            click.echo(f"   Baseline: {baseline.baseline_value:.1f}")
            click.echo("   Geen recente metingen")

        click.echo()


@performance.command()
def baselines():
    """Toon alle performance baselines."""
    tracker = get_tracker()
    baselines = tracker.get_all_baselines()

    if not baselines:
        click.echo("Geen baselines beschikbaar.")
        return

    click.echo("\n=== Performance Baselines ===\n")
    click.echo(
        f"{'Metric':<30} {'Baseline':<12} {'Confidence':<12} {'Samples':<10} {'Last Updated':<20}"
    )
    click.echo("-" * 90)

    for baseline in baselines:
        last_updated = datetime.fromtimestamp(baseline.last_updated).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        click.echo(
            f"{baseline.metric_name:<30} "
            f"{baseline.baseline_value:<12.1f} "
            f"{baseline.confidence:<12.1%} "
            f"{baseline.sample_count:<10} "
            f"{last_updated:<20}"
        )

    click.echo()


@performance.command()
@click.argument("metric_name")
@click.option("--limit", default=10, help="Aantal metingen om te tonen")
def history(metric_name: str, limit: int):
    """Toon geschiedenis van een specifieke metric.

    \b
    Examples:
        performance_cli.py history app_startup_ms
        performance_cli.py history app_startup_ms --limit 20
    """
    tracker = get_tracker()

    # Haal baseline op
    baseline = tracker.get_baseline(metric_name)
    if not baseline:
        click.echo(f"Geen baseline beschikbaar voor '{metric_name}'")
        click.echo()

    # Haal geschiedenis op
    metrics = tracker.get_recent_metrics(metric_name, limit=limit)

    if not metrics:
        click.echo(f"Geen metingen gevonden voor '{metric_name}'")
        return

    click.echo(f"\n=== Geschiedenis: {metric_name} ===\n")

    if baseline:
        click.echo(
            f"Baseline: {baseline.baseline_value:.1f} (confidence: {baseline.confidence:.0%})\n"
        )

    click.echo(f"{'Timestamp':<20} {'Value':<12} {'vs Baseline':<15} {'Metadata':<30}")
    click.echo("-" * 80)

    for metric in metrics:
        timestamp = datetime.fromtimestamp(metric.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Bereken afwijking vs baseline
        if baseline:
            ratio = metric.value / baseline.baseline_value
            deviation = f"{(ratio - 1.0) * 100:+.1f}%"
        else:
            deviation = "N/A"

        # Metadata als string
        metadata_str = str(metric.metadata) if metric.metadata else ""
        if len(metadata_str) > 28:
            metadata_str = metadata_str[:25] + "..."

        click.echo(
            f"{timestamp:<20} "
            f"{metric.value:<12.1f} "
            f"{deviation:<15} "
            f"{metadata_str:<30}"
        )

    click.echo()


@performance.command()
@click.argument("metric_name")
def delete_baseline(metric_name: str):
    """Verwijder baseline voor een metric (voor testing/reset).

    WAARSCHUWING: Dit verwijdert de baseline en alle metingen!
    """
    import sqlite3

    if not click.confirm(
        f"Weet je zeker dat je baseline voor '{metric_name}' wilt verwijderen?"
    ):
        click.echo("Geannuleerd.")
        return

    tracker = get_tracker()

    try:
        with sqlite3.connect(tracker.db_path) as conn:
            # Verwijder baseline
            conn.execute(
                "DELETE FROM performance_baselines WHERE metric_name = ?",
                (metric_name,),
            )

            # Verwijder alle metrics
            conn.execute(
                "DELETE FROM performance_metrics WHERE metric_name = ?", (metric_name,)
            )

            conn.commit()

        click.echo(f"Baseline en metingen voor '{metric_name}' verwijderd.")
    except Exception as e:
        click.echo(f"Fout bij verwijderen: {e}", err=True)
        sys.exit(1)


@performance.command()
def reset_all():
    """Reset ALLE performance data (voor testing).

    WAARSCHUWING: Dit verwijdert alle baselines en metingen!
    """
    if not click.confirm(
        "Weet je ZEKER dat je alle performance data wilt verwijderen?"
    ):
        click.echo("Geannuleerd.")
        return

    import sqlite3

    tracker = get_tracker()

    try:
        with sqlite3.connect(tracker.db_path) as conn:
            conn.execute("DELETE FROM performance_baselines")
            conn.execute("DELETE FROM performance_metrics")
            conn.commit()

        click.echo("Alle performance data verwijderd.")
    except Exception as e:
        click.echo(f"Fout bij reset: {e}", err=True)
        sys.exit(1)


@performance.command()
@click.argument("old_name")
@click.argument("new_name")
def rename_metric(old_name: str, new_name: str):
    """Rename een performance metric (voor migrations).

    Dit hernoemt de metric in BOTH metrics en baselines tables.

    \b
    Example:
        python -m src.cli.performance_cli rename-metric app_startup_ms streamlit_rerun_ms
    """
    tracker = get_tracker()

    click.echo(f"Renaming metric '{old_name}' -> '{new_name}'...")

    success = tracker.rename_metric(old_name, new_name)

    if success:
        click.echo("✅ Metric succesvol hernoemd.")

        # Toon nieuwe baseline
        baseline = tracker.get_baseline(new_name)
        if baseline:
            click.echo(
                f"\nNieuwe baseline: {new_name} = {baseline.baseline_value:.1f} "
                f"(confidence={baseline.confidence:.0%}, n={baseline.sample_count})"
            )
    else:
        click.echo("❌ Fout bij renaming metric.", err=True)
        sys.exit(1)


@performance.command()
def migrate_startup_metric():
    """Migrate oude 'app_startup_ms' metric naar nieuwe 'streamlit_rerun_ms'.

    Deze command is safe om meerdere keren te runnen - het checkt eerst of migratie nodig is.

    Context:
        De oude app_startup_ms metric mat cumulative tijd door een module-level timer.
        De nieuwe streamlit_rerun_ms metric meet correcte per-rerun tijd.
    """
    tracker = get_tracker()

    # Check of oude metric bestaat
    old_baseline = tracker.get_baseline("app_startup_ms")

    if not old_baseline:
        click.echo("✅ Geen oude 'app_startup_ms' data gevonden - migratie niet nodig.")
        return

    click.echo(
        f"Gevonden oude metric 'app_startup_ms': "
        f"baseline={old_baseline.baseline_value:.1f}ms, "
        f"samples={old_baseline.sample_count}"
    )

    # BELANGRIJK: We VERWIJDEREN oude data in plaats van renamen
    # Reden: Oude data is incorrect (cumulative tijd), niet bruikbaar voor nieuwe metric
    if click.confirm(
        "\nOude data is INCORRECT (cumulative tijd).\n"
        "Wil je oude data VERWIJDEREN en opnieuw beginnen met schone baseline?",
        default=True,
    ):
        success = tracker.delete_metric("app_startup_ms")

        if success:
            click.echo("✅ Oude incorrecte data verwijderd.")
            click.echo(
                "\nNieuwe 'streamlit_rerun_ms' baseline wordt automatisch opgebouwd "
                "na enkele app runs."
            )
        else:
            click.echo("❌ Fout bij verwijderen oude data.", err=True)
            sys.exit(1)
    else:
        click.echo("Migratie geannuleerd.")


if __name__ == "__main__":
    performance()
