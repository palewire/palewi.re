#!/usr/bin/env python
import os
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

import click
import psycopg
from psycopg import sql

from project.worktree import DEFAULT_DATABASE_NAME, available_port, database_name

ROOT = Path(__file__).resolve().parent.parent


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
    port = available_port(ROOT)
    address = f"127.0.0.1:{port}"
    click.echo(f"Using database {target_database()} and http://{address}/", err=True)
    raise SystemExit(subprocess.call(["python", "manage.py", "runserver", address], cwd=ROOT))


if __name__ == "__main__":
    cli()
