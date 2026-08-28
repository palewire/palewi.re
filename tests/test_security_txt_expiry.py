"""Tests for the security.txt expiration monitor."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from scripts import security_txt_expiry


def test_parse_expires_timestamp_normalizes_to_utc() -> None:
    expires_at = security_txt_expiry.parse_expires_timestamp(
        "Contact: mailto:security@example.com\nExpires: 2027-08-01T02:00:00+02:00\n"
    )

    assert expires_at == datetime(2027, 8, 1, tzinfo=UTC)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("Contact: mailto:security@example.com\n", "missing"),
        ("Expires: \n", "must not be empty"),
        ("Expires: not-a-timestamp\n", "valid ISO 8601"),
        ("Expires: 2027-08-01T00:00:00\n", "include a UTC offset"),
        ("Expires: 2027-08-01T00:00:00Z\nExpires: 2027-09-01T00:00:00Z\n", "only one"),
    ],
)
def test_parse_expires_timestamp_rejects_invalid_metadata(content: str, message: str) -> None:
    with pytest.raises(security_txt_expiry.SecurityTxtError, match=message):
        security_txt_expiry.parse_expires_timestamp(content)


def test_renewal_needed_only_within_ninety_days() -> None:
    now = datetime(2027, 1, 1, tzinfo=UTC)

    assert security_txt_expiry.renewal_needed(now + timedelta(days=90), now)
    assert not security_txt_expiry.renewal_needed(now + timedelta(days=91), now)


def test_renewal_needed_rejects_expired_metadata() -> None:
    now = datetime(2027, 1, 1, tzinfo=UTC)

    with pytest.raises(security_txt_expiry.SecurityTxtError, match="expired"):
        security_txt_expiry.renewal_needed(now, now)


def test_cli_writes_github_output(tmp_path: Path) -> None:
    security_txt = tmp_path / "security.txt"
    output = tmp_path / "github-output"
    security_txt.write_text("Expires: 2027-01-02T00:00:00Z\n", encoding="utf-8")

    result = CliRunner().invoke(
        security_txt_expiry.cli,
        [
            "--path",
            str(security_txt),
            "--now",
            "2027-01-01T00:00:00Z",
            "--github-output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Renewal needed: true" in result.output
    assert output.read_text(encoding="utf-8") == "renewal_needed=true\n"
