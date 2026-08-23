#!/usr/bin/env python
import os
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import click
import psycopg
from psycopg import sql

from project.worktree import DEFAULT_DATABASE_NAME, available_port, database_name

ROOT = Path(__file__).resolve().parent.parent
PORT_IN_USE_MESSAGE = "That port is already in use."


def configured_database_url() -> str:
    return os.environ.get("DATABASE_URL", f"postgres://postgres@localhost/{database_name(ROOT)}")


def maintenance_database_url() -> str:
    parsed = urlparse(configured_database_url())
    return parsed._replace(path="/postgres").geturl()


def target_database() -> str:
    name = unquote(urlparse(configured_database_url()).path.lstrip("/"))
    if not name:
        raise click.ClickException("DATABASE_URL must include a database name.")
    return name


def validate_local_drop_target() -> None:
    parsed = urlparse(configured_database_url())
    query = parse_qs(parsed.query)
    remote_query_options = {"host", "hostaddr", "service"} & query.keys()
    local_hosts = {None, "localhost", "127.0.0.1", "::1"}
    if parsed.scheme not in {"postgres", "postgresql"} or parsed.hostname not in local_hosts or remote_query_options:
        raise click.ClickException("Refusing to drop a database outside the local PostgreSQL server.")


def run_server(port: int) -> tuple[int, bool]:
    address = f"127.0.0.1:{port}"
    click.echo(f"Using database {target_database()} and http://{address}/", err=True)
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
def create_database() -> None:
    """Create this worktree's PostgreSQL database when needed."""
    name = target_database()
    with psycopg.connect(maintenance_database_url(), autocommit=True) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if exists:
            click.echo(f"Database {name} already exists.")
            return
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    click.echo(f"Created database {name}.")


@cli.command()
def drop_database() -> None:
    """Drop only the database belonging to a linked worktree."""
    validate_local_drop_target()
    name = target_database()
    expected_name = database_name(ROOT)
    if expected_name == DEFAULT_DATABASE_NAME or name != expected_name:
        raise click.ClickException("Refusing to drop a database that is not owned by this linked worktree.")

    with psycopg.connect(maintenance_database_url(), autocommit=True) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            click.echo(f"Database {name} does not exist.")
            return
        connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
    click.echo(f"Dropped database {name}.")


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
