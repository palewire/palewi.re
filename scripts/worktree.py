import subprocess
from pathlib import Path

import click

from project.worktree import available_port

ROOT = Path(__file__).resolve().parent.parent
PORT_IN_USE_MESSAGE = "That port is already in use."


def run_server(port: int) -> tuple[int, bool]:
    address = f"127.0.0.1:{port}"
    click.echo(f"Starting development server at http://{address}/", err=True)
    process = subprocess.Popen(
        ["python", "manage.py", "runserver", address],
        cwd=ROOT,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stderr is not None
    port_in_use = False
    try:
        for line in process.stderr:
            click.echo(line, nl=False, err=True)
            port_in_use = port_in_use or PORT_IN_USE_MESSAGE in line
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise
    return process.wait(), port_in_use


@click.group()
def cli() -> None:
    """Manage resources that must be isolated between worktrees."""


@cli.command()
def serve() -> None:
    """Run Django on an available, worktree-specific port."""
    attempted_ports: set[int] = set()
    while True:
        try:
            port = available_port(ROOT, attempted_ports)
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc

        return_code, port_in_use = run_server(port)
        if not port_in_use:
            raise SystemExit(return_code)

        attempted_ports.add(port)
        click.echo(f"Port {port} was claimed during startup; retrying.", err=True)


if __name__ == "__main__":
    cli()
