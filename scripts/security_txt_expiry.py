"""Check whether the site's security.txt record needs renewal."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import click

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "coltrane" / "templates" / "security.txt"
RENEWAL_WINDOW = timedelta(days=90)


class SecurityTxtError(RuntimeError):
    """Raised when security.txt expiration metadata cannot be used."""


def parse_timestamp(value: str, label: str) -> datetime:
    """Parse an ISO 8601 timestamp and return it in UTC."""
    try:
        timestamp = datetime.fromisoformat(value.strip())
    except ValueError as error:
        raise SecurityTxtError(f"{label} must be a valid ISO 8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise SecurityTxtError(f"{label} must include a UTC offset")
    return timestamp.astimezone(UTC)


def parse_expires_timestamp(content: str) -> datetime:
    """Return the one required Expires field from security.txt."""
    values = [line.partition(":")[2] for line in content.splitlines() if line.partition(":")[0] == "Expires"]
    if not values:
        raise SecurityTxtError("security.txt is missing its required Expires field")
    if len(values) > 1:
        raise SecurityTxtError("security.txt must contain only one Expires field")
    if not values[0].strip():
        raise SecurityTxtError("security.txt Expires field must not be empty")
    return parse_timestamp(values[0], "security.txt Expires field")


def renewal_needed(expires_at: datetime, now: datetime) -> bool:
    """Return whether an unexpired expiration falls within the renewal window."""
    if now.tzinfo is None:
        raise SecurityTxtError("current time must include a UTC offset")
    expires_at = expires_at.astimezone(UTC)
    now = now.astimezone(UTC)
    if expires_at <= now:
        raise SecurityTxtError(f"security.txt expired at {expires_at.isoformat()}")
    return expires_at - now <= RENEWAL_WINDOW


@click.command()
@click.option(
    "--path", type=click.Path(path_type=Path, exists=True, dir_okay=False), default=DEFAULT_PATH, show_default=True
)
@click.option(
    "--github-output",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Write the renewal_needed value to a GitHub Actions output file.",
)
@click.option("--now", help="ISO 8601 current time, for a reproducible manual check.")
def cli(path: Path, github_output: Path | None, now: str | None) -> None:
    """Check security.txt expiration and report whether renewal is needed."""
    try:
        expires_at = parse_expires_timestamp(path.read_text(encoding="utf-8"))
        current_time = parse_timestamp(now, "--now") if now else datetime.now(UTC)
        needs_renewal = renewal_needed(expires_at, current_time)
        if github_output:
            with github_output.open("a", encoding="utf-8") as output_file:
                output_file.write(f"renewal_needed={str(needs_renewal).lower()}\n")
    except (OSError, SecurityTxtError) as error:
        raise click.ClickException(str(error)) from error

    click.echo(f"security.txt expires at {expires_at.isoformat()}")
    click.echo(f"Renewal needed: {str(needs_renewal).lower()}")


if __name__ == "__main__":
    cli()
