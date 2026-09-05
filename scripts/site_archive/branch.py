"""Persist the site archive manifest on a dedicated Git branch."""

from __future__ import annotations

import base64
import binascii
import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import click

from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore

DEFAULT_REPOSITORY = "palewire/palewi.re"
DEFAULT_BRANCH = "site-archive-data"
REMOTE_MANIFEST = "manifest.json"
COAUTHOR = "Copilot App <223556219+Copilot@users.noreply.github.com>"
GH_TIMEOUT_SECONDS = 60
_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class BranchPersistenceError(RuntimeError):
    """Raised when GitHub cannot safely read or update archive state."""


@dataclass(frozen=True)
class BranchToken:
    """The immutable branch head observed by a fetch."""

    repository: str
    branch: str
    head: str | None

    @property
    def missing(self) -> bool:
        """Return whether the branch did not exist at fetch time.

        Returns:
            True for a token representing an absent branch.

        Examples:
            ``BranchToken("owner/repo", DEFAULT_BRANCH, None).missing`` is True.
        """
        return self.head is None


@dataclass(frozen=True)
class ApiResponse:
    """The decoded JSON response and HTTP status returned by ``gh``."""

    value: Any
    status: int | None


Runner = Callable[..., subprocess.CompletedProcess[str]]


class GitHubClient:
    """Small GitHub REST client backed by the installed ``gh`` executable."""

    def __init__(self, repository: str, runner: Runner | None = None):
        """Create a client for one repository.

        Args:
            repository: ``owner/name`` repository identifier.
            runner: Injectable subprocess runner used by tests.

        Returns:
            None.

        Raises:
            BranchPersistenceError: If the repository name is unsafe.

        Examples:
            ``GitHubClient(DEFAULT_REPOSITORY)`` uses the authenticated ``gh`` CLI.
        """
        validate_repository(repository)
        self.repository = repository
        self.runner = runner or subprocess.run

    def request(self, endpoint: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> ApiResponse:
        """Call a GitHub REST endpoint without interpolating JSON in a shell.

        Args:
            endpoint: Repository-relative API endpoint.
            method: HTTP method.
            payload: Optional JSON request body sent over standard input.

        Returns:
            Decoded response and the HTTP status when ``gh`` reported one.

        Raises:
            BranchPersistenceError: If ``gh`` is unavailable or the API rejects the request.

        Examples:
            ``client.request("git/ref/heads/site-archive-data")`` gets a ref.
        """
        if endpoint.startswith(("/", "-")) or any(part in endpoint for part in ("\x00", "\n", "\r")):
            raise BranchPersistenceError("unsafe GitHub API endpoint")
        api_endpoint = f"repos/{self.repository}" if not endpoint else f"repos/{self.repository}/{endpoint}"
        command = ["gh", "api", api_endpoint, "--method", method]
        stdin = None if payload is None else json.dumps(payload, separators=(",", ":"))
        if payload is not None:
            command.extend(["--input", "-"])
        try:
            result = self.runner(
                command,
                input=stdin,
                text=True,
                capture_output=True,
                check=False,
                timeout=GH_TIMEOUT_SECONDS,
            )
        except OSError as error:
            raise BranchPersistenceError(f"unable to run gh: {error}") from error
        except subprocess.TimeoutExpired as error:
            raise BranchPersistenceError(f"gh timed out after {GH_TIMEOUT_SECONDS} seconds") from error
        if result.returncode != 0:
            status = _response_status(result.stderr)
            detail = _safe_error(result.stderr or result.stdout)
            raise GitHubRequestError(detail, status)
        try:
            value = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError as error:
            raise BranchPersistenceError("GitHub returned invalid JSON") from error
        return ApiResponse(value, _response_status(result.stderr))

    def repository_exists(self) -> None:
        """Confirm that the repository is reachable before interpreting a missing ref.

        Returns:
            None.

        Raises:
            BranchPersistenceError: If the repository cannot be read.

        Examples:
            ``client.repository_exists()`` distinguishes a missing branch from a missing repository.
        """
        try:
            self.request("")
        except GitHubRequestError as error:
            raise BranchPersistenceError(f"cannot access repository {self.repository}: {error}") from error

    def ref(self, branch: str) -> str | None:
        """Read a branch head, returning ``None`` only for a genuine absent ref.

        Args:
            branch: Validated branch name.

        Returns:
            Forty-character commit SHA, or ``None`` when the ref is absent.

        Raises:
            BranchPersistenceError: If the ref request fails for another reason.

        Examples:
            ``client.ref(DEFAULT_BRANCH)`` returns the current immutable head.
        """
        try:
            response = self.request(f"git/ref/heads/{quote(branch, safe='')}")
        except GitHubRequestError as error:
            if error.status == 404:
                return None
            raise BranchPersistenceError(f"cannot read branch {branch}: {error}") from error
        try:
            sha = response.value["object"]["sha"]
        except (KeyError, TypeError) as error:
            raise BranchPersistenceError("GitHub returned a malformed branch ref") from error
        if not isinstance(sha, str) or not _SHA.fullmatch(sha):
            raise BranchPersistenceError("GitHub returned an invalid branch head")
        return sha

    def manifest(self, head: str) -> bytes:
        """Read the manifest through an immutable commit ref.

        Args:
            head: Commit SHA to read.

        Returns:
            UTF-8 manifest bytes.

        Raises:
            BranchPersistenceError: If the file is absent, malformed, or unreadable.

        Examples:
            ``client.manifest(head)`` reads exactly the file at that commit.
        """
        try:
            response = self.request(f"contents/{REMOTE_MANIFEST}?ref={quote(head, safe='')}")
        except GitHubRequestError as error:
            raise BranchPersistenceError(f"cannot read {REMOTE_MANIFEST} at {head}: {error}") from error
        value = response.value
        if not isinstance(value, dict):
            raise BranchPersistenceError(f"GitHub returned no usable {REMOTE_MANIFEST}")
        if value.get("encoding") == "none" and isinstance(value.get("sha"), str):
            return self.blob(value["sha"])
        if value.get("encoding") != "base64" or not isinstance(value.get("content"), str):
            raise BranchPersistenceError(f"GitHub returned no usable {REMOTE_MANIFEST}")
        try:
            encoded = "".join(value["content"].split())
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise BranchPersistenceError(f"GitHub returned invalid {REMOTE_MANIFEST} content") from error

    def blob(self, sha: str) -> bytes:
        """Read an immutable Git blob by SHA.

        Args:
            sha: Blob SHA returned by the contents endpoint.

        Returns:
            Decoded blob bytes.

        Raises:
            BranchPersistenceError: If the blob response is malformed or unreadable.

        Examples:
            ``client.blob("a" * 40)`` reads a large manifest without a contents-size limit.
        """
        if not _SHA.fullmatch(sha):
            raise BranchPersistenceError("GitHub returned an invalid manifest blob SHA")
        try:
            response = self.request(f"git/blobs/{quote(sha, safe='')}")
        except GitHubRequestError as error:
            raise BranchPersistenceError(f"cannot read manifest blob {sha}: {error}") from error
        value = response.value
        if (
            not isinstance(value, dict)
            or value.get("encoding") != "base64"
            or not isinstance(value.get("content"), str)
        ):
            raise BranchPersistenceError("GitHub returned no usable manifest blob")
        try:
            return base64.b64decode("".join(value["content"].split()), validate=True)
        except (binascii.Error, ValueError) as error:
            raise BranchPersistenceError("GitHub returned invalid manifest blob content") from error

    def commit_tree(self, head: str) -> str:
        """Read the tree SHA used as the base for an existing-branch update.

        Args:
            head: Parent commit SHA.

        Returns:
            Tree SHA.

        Raises:
            BranchPersistenceError: If the commit response is malformed.

        Examples:
            ``client.commit_tree(head)`` supplies ``base_tree`` for a child commit.
        """
        try:
            response = self.request(f"git/commits/{quote(head, safe='')}")
            tree = response.value["tree"]["sha"]
        except (GitHubRequestError, KeyError, TypeError) as error:
            raise BranchPersistenceError(f"cannot read commit tree for {head}") from error
        if not isinstance(tree, str) or not _SHA.fullmatch(tree):
            raise BranchPersistenceError("GitHub returned an invalid commit tree")
        return tree

    def create_blob(self, content: bytes) -> str:
        """Create a UTF-8 blob through the Git database API.

        Args:
            content: Manifest bytes.

        Returns:
            New blob SHA.

        Raises:
            BranchPersistenceError: If GitHub rejects the blob.

        Examples:
            ``client.create_blob(b"{}")`` returns a blob identifier.
        """
        try:
            response = self.request(
                "git/blobs",
                method="POST",
                payload={"content": content.decode("utf-8"), "encoding": "utf-8"},
            )
            sha = response.value["sha"]
        except (UnicodeDecodeError, GitHubRequestError, KeyError, TypeError) as error:
            raise BranchPersistenceError("cannot create manifest blob") from error
        return _require_sha(sha, "blob")

    def create_tree(self, blob: str, base_tree: str | None) -> str:
        """Create a tree containing only the manifest file.

        Args:
            blob: Manifest blob SHA.
            base_tree: Existing tree SHA, or ``None`` for an orphan commit.

        Returns:
            New tree SHA.

        Raises:
            BranchPersistenceError: If GitHub rejects the tree.

        Examples:
            ``client.create_tree(blob, None)`` creates an orphan single-file tree.
        """
        payload: dict[str, Any] = {"tree": [{"path": REMOTE_MANIFEST, "mode": "100644", "type": "blob", "sha": blob}]}
        if base_tree is not None:
            payload["base_tree"] = base_tree
        try:
            response = self.request("git/trees", method="POST", payload=payload)
            sha = response.value["sha"]
        except (GitHubRequestError, KeyError, TypeError) as error:
            raise BranchPersistenceError("cannot create manifest tree") from error
        return _require_sha(sha, "tree")

    def create_commit(self, tree: str, parent: str | None) -> str:
        """Create a commit with the required co-author trailer.

        Args:
            tree: New tree SHA.
            parent: Parent commit SHA, or ``None`` for an orphan.

        Returns:
            New commit SHA.

        Raises:
            BranchPersistenceError: If GitHub rejects the commit.

        Examples:
            ``client.create_commit(tree, None)`` creates the initial data commit.
        """
        payload: dict[str, Any] = {
            "message": f"Update site archive manifest\n\nCo-authored-by: {COAUTHOR}",
            "tree": tree,
            "parents": [] if parent is None else [parent],
        }
        try:
            response = self.request("git/commits", method="POST", payload=payload)
            sha = response.value["sha"]
        except (GitHubRequestError, KeyError, TypeError) as error:
            raise BranchPersistenceError("cannot create manifest commit") from error
        return _require_sha(sha, "commit")

    def update_ref(self, branch: str, commit: str, *, create: bool) -> None:
        """Create or update the data ref without force pushing.

        Args:
            branch: Validated data branch.
            commit: New commit SHA.
            create: Whether this is the initial ref creation.

        Returns:
            None.

        Raises:
            BranchPersistenceError: If GitHub rejects the ref update.

        Examples:
            ``client.update_ref(DEFAULT_BRANCH, commit, create=True)`` creates a new ref.
        """
        method = "POST" if create else "PATCH"
        endpoint = "git/refs" if create else f"git/refs/heads/{quote(branch, safe='')}"
        payload: dict[str, Any] = {"sha": commit}
        if create:
            payload["ref"] = f"refs/heads/{branch}"
        else:
            payload["force"] = False
        try:
            self.request(endpoint, method=method, payload=payload)
        except GitHubRequestError as error:
            raise BranchPersistenceError(
                f"cannot {'create' if create else 'update'} branch {branch}: {error}"
            ) from error


class GitHubRequestError(BranchPersistenceError):
    """A GitHub API failure with an optional HTTP status."""

    def __init__(self, detail: str, status: int | None):
        """Create an API error.

        Args:
            detail: Sanitized command error text.
            status: Parsed HTTP status, if available.

        Returns:
            None.

        Examples:
            ``GitHubRequestError("forbidden", 403)`` describes a permission failure.
        """
        super().__init__(detail)
        self.status = status


def validate_repository(repository: str) -> str:
    """Validate an owner/name repository identifier.

    Args:
        repository: Candidate repository identifier.

    Returns:
        The unchanged validated identifier.

    Raises:
        BranchPersistenceError: If the value could inject an API path.

    Examples:
        ``validate_repository(DEFAULT_REPOSITORY)`` returns the default repository.
    """
    if not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository):
        raise BranchPersistenceError("repository must be an owner/name identifier")
    return repository


def validate_branch(branch: str) -> str:
    """Require the one branch reserved for archive persistence.

    Args:
        branch: Candidate branch name.

    Returns:
        The unchanged validated branch.

    Raises:
        BranchPersistenceError: If a different branch is requested.

    Examples:
        ``validate_branch(DEFAULT_BRANCH)`` returns ``site-archive-data``.
    """
    if branch != DEFAULT_BRANCH:
        raise BranchPersistenceError(f"branch must be {DEFAULT_BRANCH}")
    return branch


def _require_sha(value: Any, label: str) -> str:
    """Validate a Git object identifier returned by the API.

    Args:
        value: API value to inspect.
        label: Object type used in the error.

    Returns:
        The validated SHA.

    Raises:
        BranchPersistenceError: If the value is not a full SHA.

    Examples:
        ``_require_sha("a" * 40, "blob")`` returns the blob SHA.
    """
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise BranchPersistenceError(f"GitHub returned an invalid {label} SHA")
    return value


def _response_status(text: str) -> int | None:
    """Extract an HTTP status from a diagnostic emitted by ``gh``.

    Args:
        text: ``gh`` diagnostic text.

    Returns:
        Parsed status code, or ``None`` when no status is present.

    Examples:
        ``_response_status("HTTP 404")`` returns ``404``.
    """
    match = re.search(r"\bHTTP(?:/[\d.]+)?\s+(\d{3})\b|\bHTTP\s+(\d{3})\b", text or "", re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _safe_error(text: str) -> str:
    """Keep ``gh`` diagnostics concise and avoid accidentally echoing credentials.

    Args:
        text: Standard error or output from ``gh``.

    Returns:
        A single-line diagnostic.

    Examples:
        ``_safe_error("gh: Not Found\\n")`` returns ``"gh: Not Found"``.
    """
    value = " ".join(text.split())
    return value[:500] or "GitHub API request failed"


def _write_token(path: Path, token: BranchToken) -> None:
    """Atomically save a fetch token.

    Args:
        path: Token file destination.
        token: Observed branch state.

    Returns:
        None.

    Raises:
        BranchPersistenceError: If the token cannot be written.

    Examples:
        ``_write_token(Path("state-token.json"), token)`` checkpoints a head.
    """
    value = {"repository": token.repository, "branch": token.branch, "missing": token.missing, "head": token.head}
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        raise BranchPersistenceError(f"cannot write state token {path}: {error}") from error


def _read_token(path: Path) -> BranchToken:
    """Load and validate a state token before writing any remote objects.

    Args:
        path: Token file path.

    Returns:
        Validated token.

    Raises:
        BranchPersistenceError: If the token is missing or malformed.

    Examples:
        ``_read_token(Path("state-token.json"))`` returns the fetched branch head.
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BranchPersistenceError(f"{path}: malformed state token") from error
    if not isinstance(value, dict) or set(value) != {"repository", "branch", "missing", "head"}:
        raise BranchPersistenceError(f"{path}: malformed state token")
    repository = value["repository"]
    branch = value["branch"]
    missing = value["missing"]
    head = value["head"]
    try:
        validate_repository(repository)
        validate_branch(branch)
    except (BranchPersistenceError, TypeError) as error:
        raise BranchPersistenceError(f"{path}: malformed state token") from error
    if type(missing) is not bool or missing != (head is None):
        raise BranchPersistenceError(f"{path}: malformed state token")
    if head is not None and (not isinstance(head, str) or not _SHA.fullmatch(head)):
        raise BranchPersistenceError(f"{path}: malformed state token")
    return BranchToken(repository, branch, head)


def _validate_manifest(path: Path) -> bytes:
    """Validate and read a local manifest without changing it.

    Args:
        path: Manifest path.

    Returns:
        Exact UTF-8 bytes to persist.

    Raises:
        BranchPersistenceError: If local state is absent, unreadable, or invalid.

    Examples:
        ``_validate_manifest(Path(".site-archive/manifest.json"))`` returns its bytes.
    """
    try:
        ManifestStore(path).load()
        return path.read_bytes()
    except (ArchiveError, OSError) as error:
        raise BranchPersistenceError(f"{path}: invalid local manifest: {error}") from error


def _ensure_distinct_paths(path: Path, state_token: Path) -> None:
    """Reject overlapping manifest and optimistic-lock state paths.

    Args:
        path: Manifest path.
        state_token: State-token path.

    Returns:
        None.

    Raises:
        BranchPersistenceError: If both paths identify the same file.

    Examples:
        ``_ensure_distinct_paths(Path("manifest.json"), Path("state.json"))`` succeeds.
    """
    try:
        same_path = path.resolve(strict=False) == state_token.resolve(strict=False)
    except OSError as error:
        raise BranchPersistenceError(f"cannot resolve local state paths: {error}") from error
    if same_path:
        raise BranchPersistenceError("manifest and state-token paths must be different")


def fetch(path: Path, state_token: Path, repository: str = DEFAULT_REPOSITORY, branch: str = DEFAULT_BRANCH) -> None:
    """Fetch the immutable branch state into local files.

    Args:
        path: Local manifest destination.
        state_token: State-token destination.
        repository: GitHub ``owner/name`` repository.
        branch: Reserved data branch.

    Returns:
        None.

    Raises:
        BranchPersistenceError: If the branch or manifest is not safely readable.

    Examples:
        ``fetch(Path("manifest.json"), Path("state-token.json"))`` fetches current data.
    """
    validate_repository(repository)
    validate_branch(branch)
    _ensure_distinct_paths(path, state_token)
    client = GitHubClient(repository)
    client.repository_exists()
    head = client.ref(branch)
    token = BranchToken(repository, branch, head)
    if head is None:
        if path.exists():
            raise BranchPersistenceError(
                f"{path}: branch is absent but a local manifest exists; refusing to discard it"
            )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            ManifestStore(path).save(Manifest())
        except (ArchiveError, OSError) as error:
            raise BranchPersistenceError(f"{path}: unable to initialize empty manifest: {error}") from error
        _write_token(state_token, token)
        click.echo(f"Branch {branch} is absent; starting with no remote manifest.")
        return
    content = client.manifest(head)
    if path.exists():
        try:
            local_content = path.read_bytes()
        except OSError as error:
            raise BranchPersistenceError(f"{path}: unable to inspect local manifest: {error}") from error
        if local_content != content:
            raise BranchPersistenceError(
                f"{path}: local manifest differs from branch; fetch into a fresh path for reconciliation"
            )
    temporary = path.with_name(f".{path.name}.fetch.tmp")
    try:
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(content)
        ManifestStore(temporary).load()
        temporary.replace(path)
    except (ArchiveError, OSError) as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as cleanup_error:
            raise BranchPersistenceError(
                f"remote manifest at {head} is invalid and temporary cleanup failed: {cleanup_error}"
            ) from cleanup_error
        raise BranchPersistenceError(f"remote manifest at {head} is invalid: {error}") from error
    _write_token(state_token, token)
    click.echo(f"Fetched {REMOTE_MANIFEST} at {head}.")


def push(path: Path, state_token: Path, repository: str = DEFAULT_REPOSITORY, branch: str = DEFAULT_BRANCH) -> None:
    """Publish local state with an optimistic, non-forced ref update.

    Args:
        path: Local manifest path.
        state_token: Token produced by :func:`fetch`.
        repository: GitHub ``owner/name`` repository.
        branch: Reserved data branch.

    Returns:
        None. Identical bytes produce no commit.

    Raises:
        BranchPersistenceError: If state is stale, malformed, or GitHub rejects a write.

    Examples:
        ``push(Path("manifest.json"), Path("state-token.json"))`` persists one checkpoint.
    """
    validate_repository(repository)
    validate_branch(branch)
    _ensure_distinct_paths(path, state_token)
    token = _read_token(state_token)
    if token.repository != repository or token.branch != branch:
        raise BranchPersistenceError("state token does not match repository or branch")
    content = _validate_manifest(path)
    client = GitHubClient(repository)
    client.repository_exists()
    current = client.ref(branch)
    if current != token.head:
        raise BranchPersistenceError("branch changed since fetch; refusing stale write")
    if current is not None and client.manifest(current) == content:
        click.echo(f"{REMOTE_MANIFEST} is unchanged at {current}; no commit created.")
        return
    parent = current
    base_tree = None if parent is None else client.commit_tree(parent)
    blob = client.create_blob(content)
    tree = client.create_tree(blob, base_tree)
    commit = client.create_commit(tree, parent)
    client.update_ref(branch, commit, create=parent is None)
    _write_token(state_token, BranchToken(repository, branch, commit))
    click.echo(f"Persisted {REMOTE_MANIFEST} at {commit}.")


def _branch_option(value: str) -> str:
    """Validate the Click branch option.

    Args:
        value: User-supplied branch name.

    Returns:
        The validated branch name.

    Raises:
        click.BadParameter: If the user selected another branch.

    Examples:
        ``_branch_option(DEFAULT_BRANCH)`` returns the reserved branch.
    """
    try:
        return validate_branch(value)
    except BranchPersistenceError as error:
        raise click.BadParameter(str(error)) from error


@click.group()
def cli() -> None:
    """Fetch and persist the site archive data branch.

    Returns:
        None.

    Examples:
        ``uv run python -m scripts.site_archive.branch fetch --help`` lists options.
    """


@cli.command(name="fetch")
@click.option("--path", type=click.Path(path_type=Path), required=True)
@click.option("--state-token", type=click.Path(path_type=Path), required=True)
@click.option("--repo", "repository", default=DEFAULT_REPOSITORY, show_default=True)
@click.option(
    "--branch", default=DEFAULT_BRANCH, show_default=True, callback=lambda _ctx, _param, value: _branch_option(value)
)
def fetch_command(path: Path, state_token: Path, repository: str, branch: str) -> None:
    """Fetch the branch manifest and checkpoint its exact head.

    Args:
        path: Local manifest destination.
        state_token: State-token destination.
        repository: GitHub repository.
        branch: Reserved persistence branch.

    Returns:
        None.

    Examples:
        ``... branch fetch --path manifest.json --state-token state.json``.
    """
    try:
        fetch(path, state_token, repository, branch)
    except BranchPersistenceError as error:
        raise click.ClickException(str(error)) from error


@cli.command(name="push")
@click.option("--path", type=click.Path(path_type=Path), required=True)
@click.option("--state-token", type=click.Path(path_type=Path), required=True)
@click.option("--repo", "repository", default=DEFAULT_REPOSITORY, show_default=True)
@click.option(
    "--branch", default=DEFAULT_BRANCH, show_default=True, callback=lambda _ctx, _param, value: _branch_option(value)
)
def push_command(path: Path, state_token: Path, repository: str, branch: str) -> None:
    """Persist the local manifest with a non-forced optimistic update.

    Args:
        path: Local manifest path.
        state_token: Token created by ``fetch``.
        repository: GitHub repository.
        branch: Reserved persistence branch.

    Returns:
        None.

    Examples:
        ``... branch push --path manifest.json --state-token state.json``.
    """
    try:
        push(path, state_token, repository, branch)
    except BranchPersistenceError as error:
        raise click.ClickException(str(error)) from error


if __name__ == "__main__":
    cli()
