import hashlib
import socket
from collections.abc import Collection, Iterator
from pathlib import Path

DEFAULT_PORT = 8000
PORT_RANGE = 1000


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
