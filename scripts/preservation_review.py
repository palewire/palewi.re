"""Compare a preservation inventory with its reviewed baseline.

The command deliberately consumes JSON emitted by ``preservation_inventory``.
It makes no network requests and never needs an archive root, so it can run
in pull requests while still requiring a review for newly referenced sources.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from scripts.preservation_inventory import INVENTORY_VERSION

BASELINE_VERSION = 1
BASELINE_PATH = Path(__file__).resolve().parents[1] / "preservation-review-baseline.json"
WAYBACK_MISSING = "wayback-missing"


class ReviewError(RuntimeError):
    """Raised when a preservation review input is invalid."""


@dataclass(frozen=True, order=True)
class GapKey:
    """A source-specific preservation gap."""

    source_url: str
    code: str


def load_json(path: Path, label: str) -> dict[str, Any]:
    """Load a JSON object, making malformed review inputs clear."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReviewError(f"{path}: invalid {label} JSON") from error
    if not isinstance(value, dict):
        raise ReviewError(f"{path}: {label} must be a JSON object")
    return value


def require_string(record: dict[str, Any], field: str, label: str) -> str:
    """Return one required non-empty string field."""
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{label} field {field!r} must be a non-empty string")
    return value


def load_inventory(path: Path) -> tuple[dict[str, dict[str, Any]], set[GapKey]]:
    """Load the public inventory contract and extract current-source gaps."""
    inventory = load_json(path, "preservation inventory")
    if inventory.get("version") != INVENTORY_VERSION:
        raise ReviewError(
            f"{path}: preservation inventory version must be {INVENTORY_VERSION}; "
            "regenerate it with make preservation-inventory"
        )
    sources = inventory.get("sources")
    if not isinstance(sources, list):
        raise ReviewError(f"{path}: preservation inventory field 'sources' must be a JSON array")

    sources_by_url: dict[str, dict[str, Any]] = {}
    gaps: set[GapKey] = set()
    for index, source in enumerate(sources):
        label = f"{path}: preservation inventory source {index}"
        if not isinstance(source, dict):
            raise ReviewError(f"{label} must be a JSON object")
        source_url = require_string(source, "source_url", label)
        if source_url in sources_by_url:
            raise ReviewError(f"{path}: preservation inventory duplicates source {source_url!r}")
        sources_by_url[source_url] = source

        if source.get("current_reference") is not True:
            continue
        source_gaps = source.get("gaps")
        if not isinstance(source_gaps, list):
            raise ReviewError(f"{label} field 'gaps' must be a JSON array")
        for gap_index, gap in enumerate(source_gaps):
            gap_label = f"{label} gap {gap_index}"
            if not isinstance(gap, dict):
                raise ReviewError(f"{gap_label} must be a JSON object")
            gaps.add(GapKey(source_url, require_string(gap, "code", gap_label)))
    return sources_by_url, gaps


def load_baseline(path: Path) -> dict[GapKey, str]:
    """Load reviewed historical gaps and explicit access-control exemptions."""
    baseline = load_json(path, "preservation review baseline")
    if baseline.get("version") != BASELINE_VERSION:
        raise ReviewError(f"{path}: preservation review baseline version must be {BASELINE_VERSION}")
    records = baseline.get("known_gaps")
    if not isinstance(records, list):
        raise ReviewError(f"{path}: preservation review baseline field 'known_gaps' must be a JSON array")

    known_gaps: dict[GapKey, str] = {}
    for index, record in enumerate(records):
        label = f"{path}: preservation review baseline record {index}"
        if not isinstance(record, dict):
            raise ReviewError(f"{label} must be a JSON object")
        key = GapKey(
            require_string(record, "source_url", label),
            require_string(record, "code", label),
        )
        if key.code == WAYBACK_MISSING:
            raise ReviewError(
                f"{label}: Wayback gaps cannot be accepted; add a snapshot or archive_exemption to the clip instead"
            )
        if key in known_gaps:
            raise ReviewError(f"{path}: preservation review baseline duplicates {key.source_url} ({key.code})")
        known_gaps[key] = require_string(record, "reason", label)
    return known_gaps


def origin_locations(source: dict[str, Any]) -> str:
    """Format inventory origins as exact, concise source locations."""
    origins = source.get("origins")
    if not isinstance(origins, list):
        return "source location unavailable"
    locations: list[str] = []
    for origin in origins:
        if not isinstance(origin, dict):
            continue
        origin_type = origin.get("origin_type")
        origin_id = origin.get("origin_id")
        location = origin.get("location")
        if all(isinstance(value, str) and value for value in (origin_type, origin_id, location)):
            locations.append(f"{origin_type} {origin_id!r} ({location})")
    return "; ".join(sorted(set(locations))) or "source location unavailable"


def next_action(code: str) -> str:
    """Return the next manual preservation action for an uncovered gap."""
    if code == WAYBACK_MISSING:
        return "Run make archive-clips, then make check-clip-archives; record a specific archive_exemption only if capture is impossible."
    if code == "local-media-not-verified":
        return (
            "Run ARCHIVE_ROOT=/path/outside/repo make media-archive-verify, then replicate verified media with "
            "make media-archive-r2-sync and confirm it with make media-archive-r2-verify."
        )
    return (
        "Back up permitted public media with ARCHIVE_ROOT=/path/outside/repo make media-archive-backup, "
        "verify it with make media-archive-verify, then replicate it with make media-archive-r2-sync and "
        "confirm it with make media-archive-r2-verify. For DRM, private, login-required, or inaccessible media, "
        "add this exact gap to preservation-review-baseline.json with the specific reason access cannot be used."
    )


def print_gap(kind: str, key: GapKey, source: dict[str, Any], detail: str) -> None:
    """Print a review result with its source and clear follow-up."""
    click.echo(f"{kind}  {key.code}  {key.source_url}")
    click.echo(f"  Source: {origin_locations(source)}")
    click.echo(f"  {detail}")


@click.command()
@click.option(
    "--inventory",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    required=True,
    help="JSON written by scripts.preservation_inventory.",
)
@click.option(
    "--baseline",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    default=BASELINE_PATH,
    show_default=True,
    help="Reviewed historical gaps and explicit media exemptions.",
)
def cli(inventory: Path, baseline: Path) -> None:
    """Fail when current content introduces an unreviewed preservation gap."""
    try:
        sources, current_gaps = load_inventory(inventory)
        known_gaps = load_baseline(baseline)
    except ReviewError as error:
        raise click.ClickException(str(error)) from error

    new_gaps = sorted(current_gaps - known_gaps.keys())
    stale_gaps = sorted(known_gaps.keys() - current_gaps)
    accepted_gaps = sorted(current_gaps & known_gaps.keys())

    click.echo(
        f"Preservation review: {len(current_gaps)} current gap(s), {len(accepted_gaps)} reviewed, {len(new_gaps)} new."
    )
    for key in new_gaps:
        print_gap("NEW", key, sources[key.source_url], f"Next: {next_action(key.code)}")
    for key in stale_gaps:
        click.echo(f"STALE  {key.code}  {key.source_url}")
        click.echo("  Remove this resolved or no-longer-current entry from preservation-review-baseline.json.")

    if new_gaps or stale_gaps:
        raise click.ClickException("Preservation review needs an explicit update before merge.")


if __name__ == "__main__":
    cli()
