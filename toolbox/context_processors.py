import logging
import os
import re
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)
REPOSITORY_URL = "https://github.com/palewire/palewi.re"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def current_site(_request):
    """
    Add the current site to the template context.
    """
    return {"current_site": "palewi.re"}


def now(request):
    return {"now": datetime.now()}


@lru_cache(maxsize=1)
def _main_commit() -> str | None:
    commit = os.environ.get("HEROKU_SLUG_COMMIT") or os.environ.get("SOURCE_VERSION")
    if commit is None:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                cwd=REPOSITORY_ROOT,
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logger.warning("Unable to determine the main branch commit")
            return None

    commit = commit.lower()
    if not COMMIT_PATTERN.fullmatch(commit):
        logger.warning("Ignoring invalid main branch commit: %r", commit)
        return None
    return commit


def repository(_request):
    commit = _main_commit()
    return {
        "repository_url": REPOSITORY_URL,
        "repository_commit": commit,
        "repository_commit_short": commit[:7] if commit else None,
    }
