"""Regression coverage for the database-free runtime."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_django_check_runs_without_database_url():
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
