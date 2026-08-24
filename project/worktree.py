import hashlib
import re
import socket
from collections.abc import Collection, Iterator
from pathlib import Path

DEFAULT_DATABASE_NAME = "palewire"
DEFAULT_PORT = 8000
PORT_RANGE = 1000
POSTGRES_IDENTIFIER_LIMIT = 63
TEST_DATABASE_PREFIX = "test_"


def is_linked_worktree(root: Path) -> bool:
    return (root / ".git").is_file()


def database_name(root: Path) -> str:
    if not is_linked_worktree(root):
        return DEFAULT_DATABASE_NAME

    slug = re.sub(r"[^a-z0-9]+", "_", root.name.lower()).strip("_") or "worktree"
    digest = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:8]
    suffix = f"_{digest}"
    available = POSTGRES_IDENTIFIER_LIMIT - len(DEFAULT_DATABASE_NAME) - len(suffix) - 1
    return f"{DEFAULT_DATABASE_NAME}_{slug[:available]}{suffix}"


def django_test_database_name(base_name: str | None) -> str:
    """Return a safe PostgreSQL name for Django's test database.

    The name is ``test_<base name>`` when it fits PostgreSQL's 63-character
    limit. Longer names are shortened and end with a deterministic hash so
    similarly named worktrees remain isolated.
    """
    raw_name = base_name or ""
    safe_base_name = re.sub(r"[^a-z0-9]+", "_", raw_name.lower()).strip("_") or "database"
    candidate = f"{TEST_DATABASE_PREFIX}{safe_base_name}"
    if len(candidate) <= POSTGRES_IDENTIFIER_LIMIT:
        return candidate

    digest = hashlib.sha256(raw_name.encode()).hexdigest()[:8]
    suffix = f"_{digest}"
    available = POSTGRES_IDENTIFIER_LIMIT - len(TEST_DATABASE_PREFIX) - len(suffix)
    return f"{TEST_DATABASE_PREFIX}{safe_base_name[:available]}{suffix}"


def default_database_url(root: Path) -> str:
    return f"postgres://postgres@localhost/{database_name(root)}"


def candidate_ports(root: Path) -> Iterator[int]:
    digest = hashlib.sha256(str(root.resolve()).encode()).digest()
    first_port = DEFAULT_PORT + int.from_bytes(digest[:2]) % PORT_RANGE

    for offset in range(PORT_RANGE):
        yield DEFAULT_PORT + (first_port - DEFAULT_PORT + offset) % PORT_RANGE


def port_is_available(port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def available_port(root: Path, excluded: Collection[int] = ()) -> int:
    for port in candidate_ports(root):
        if port not in excluded and port_is_available(port):
            return port

    raise RuntimeError(f"No available port found between {DEFAULT_PORT} and {DEFAULT_PORT + PORT_RANGE - 1}.")
