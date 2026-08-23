import hashlib
import re
import socket
from pathlib import Path

DEFAULT_DATABASE_NAME = "palewire"
DEFAULT_PORT = 8000
PORT_RANGE = 1000
POSTGRES_IDENTIFIER_LIMIT = 63


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


def default_database_url(root: Path) -> str:
    return f"postgres://postgres@localhost/{database_name(root)}"


def available_port(root: Path) -> int:
    digest = hashlib.sha256(str(root.resolve()).encode()).digest()
    first_port = DEFAULT_PORT + int.from_bytes(digest[:2]) % PORT_RANGE

    for offset in range(PORT_RANGE):
        port = DEFAULT_PORT + (first_port - DEFAULT_PORT + offset) % PORT_RANGE
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
        return port

    raise RuntimeError(f"No available port found between {DEFAULT_PORT} and {DEFAULT_PORT + PORT_RANGE - 1}.")
