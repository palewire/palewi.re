"""Behavioral regression tests for developer Makefile setup targets."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MAKE_EXECUTABLE = shutil.which("make")
NODE_RUNTIME = shutil.which("node")


class CommandCall(TypedDict):
    """Shape of one invocation recorded by a fake command."""

    command: str
    args: list[str]
    cwd: str
    uv_env_file: str | None


def _require_node_runtime() -> str:
    """Return Node.js for executing the Makefile's inline version check.

    Args:
        None.

    Returns:
        str: Path to the installed Node.js runtime.

    Examples:
        `_require_node_runtime()` returns the runtime path or skips Node
        version cases when Node.js is unavailable.
    """
    if NODE_RUNTIME is None:
        pytest.skip("Node.js is needed to execute the Makefile's inline check")
    return NODE_RUNTIME


def _write_fake_command(directory: Path, name: str) -> Path:
    """Write a deterministic command stub that records its invocation.

    Args:
        directory: Directory in which to place the executable.
        name: Command name and recorded command label.

    Returns:
        Path: Path to the executable stub.

    Examples:
        `_write_fake_command(tmp_path, "npm")`
        creates an npm stub that records arguments and working directory.
    """
    directory.mkdir(parents=True, exist_ok=True)
    executable = directory / name
    executable.write_text(
        "\n".join(
            (
                f"#!{sys.executable}",
                "import json",
                "import os",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                f"name = {name!r}",
                "record = {",
                "    'command': name,",
                "    'args': sys.argv[1:],",
                "    'cwd': os.getcwd(),",
                "    'uv_env_file': os.environ.get('UV_ENV_FILE'),",
                "}",
                "log_path = Path(os.environ['MAKE_TEST_LOG'])",
                "with log_path.open('a', encoding='utf-8') as log_file:",
                "    log_file.write(json.dumps(record) + '\\n')",
                "if name == 'node' and sys.argv[1:2] == ['-e']:",
                "    source = sys.argv[2]",
                "    version = json.dumps(os.environ['FAKE_NODE_VERSION'])",
                "    wrapped_source = (",
                "        f'const source = {json.dumps(source)};\\n'",
                "        f'const version = {version};\\n'",
                "        'const processStub = { versions: { node: version }, '",
                "        'exit(code = 0) { process.exitCode = code; } };\\n'",
                "        \"new Function('process', source)(processStub);\\n\"",
                "    )",
                "    result = subprocess.run(",
                "        [os.environ['MAKE_TEST_REAL_NODE'], '-e', wrapped_source],",
                "        check=False,",
                "    )",
                "    raise SystemExit(result.returncode)",
                "raise SystemExit(0)",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def _test_environment(tmp_path: Path, log_path: Path) -> dict[str, str]:
    """Create an isolated PATH and environment for Make subprocesses.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        log_path: JSON-lines file for fake command records.

    Returns:
        dict[str, str]: Environment with isolated fake-command PATH and
            dotenv loading disabled.

    Examples:
        `env = _test_environment(tmp_path, tmp_path / "calls.jsonl")`
        returns an environment safe for offline Make target tests.
    """
    fake_bin = tmp_path / "fake bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    return {
        **os.environ,
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "UV_NO_ENV_FILE": "1",
        "MAKE_TEST_LOG": str(log_path),
        "MAKE_TEST_REAL_NODE": NODE_RUNTIME or "",
    }


def _read_calls(log_path: Path) -> list[CommandCall]:
    """Read fake-command invocations from a JSON-lines log.

    Args:
        log_path: JSON-lines file written by fake commands.

    Returns:
        list[CommandCall]: Recorded command, arguments, and directory.

    Examples:
        `_read_calls(tmp_path / "calls.jsonl")` returns an empty list when
        no fake command has run.
    """
    if not log_path.exists():
        return []
    return [cast(CommandCall, json.loads(line)) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _run_make(
    target: str,
    *,
    env: dict[str, str],
    makefile: Path | None = None,
    variables: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one Make target from the repository root.

    Args:
        target: Make target to run.
        env: Environment for the subprocess.
        makefile: Optional Makefile path; defaults to the repository Makefile.
        variables: Optional Make variable overrides.

    Returns:
        subprocess.CompletedProcess[str]: Captured Make result.

    Examples:
        `_run_make("check-tools", env=test_env)` runs the real target while
        resolving developer commands from the test's fake PATH.
    """
    assert MAKE_EXECUTABLE is not None, "make must be installed to run Makefile tests"
    command = [MAKE_EXECUTABLE]
    if makefile is not None:
        command.extend(("-f", str(makefile)))
    command.extend(f"{name}={value}" for name, value in (variables or {}).items())
    command.append(f"PATH={env['PATH']}")
    command.append(target)
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_bootstrap_installs_locked_worker_dependencies_without_global_wrangler(tmp_path: Path) -> None:
    """Install each Worker dependency tree through bootstrap using npm stubs.

    Args:
        tmp_path: Temporary directory supplied by pytest.

    Returns:
        None.

    Examples:
        Pytest runs `make bootstrap` with fake uv, npm, and Node commands so
        the test performs no dependency installation or network access.
    """
    _require_node_runtime()
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    for name in ("uv", "npm", "node"):
        _write_fake_command(fake_bin, name)
    env["FAKE_NODE_VERSION"] = "24.22.0"

    talk_assets = tmp_path / "talk assets"
    worker_directories = [
        tmp_path / "mastodon worker",
        tmp_path / "legacy worker",
        tmp_path / "static worker",
    ]
    env_file = tmp_path / "local environment.env"
    env_file.touch()
    result = _run_make(
        "bootstrap",
        env=env,
        variables={
            "TALK_ASSET_DIR": str(talk_assets),
            "WORKER_DIR": str(worker_directories[0]),
            "LEGACY_WORKER_DIR": str(worker_directories[1]),
            "STATIC_WORKER_DIR": str(worker_directories[2]),
            "LOCAL_ENV_FILE": str(env_file),
            "HOMEBREW_BIN": "",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    calls = _read_calls(log_path)
    npm_calls = [call["args"] for call in calls if call["command"] == "npm"]
    assert npm_calls == [
        ["--prefix", str(talk_assets), "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        *[
            ["--prefix", str(directory), "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
            for directory in worker_directories
        ],
    ]
    uv_calls = [call["args"] for call in calls if call["command"] == "uv"]
    assert ["sync", "--locked", "--group", "dev"] in uv_calls
    assert ["run", "pre-commit", "install"] in uv_calls
    assert not any(call["command"] == "wrangler" for call in calls)


@pytest.mark.parametrize(
    ("node_version", "expected_success"),
    [("24.22.0", True), ("24.21.9", False), ("25.0.0", False)],
)
def test_check_tools_enforces_node_24_22_without_requiring_wrangler(
    tmp_path: Path,
    node_version: str,
    expected_success: bool,
) -> None:
    """Accept supported Node 24 versions and reject older or other majors.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        node_version: Version exposed by the fake Node executable.
        expected_success: Whether `make check-tools` should succeed.

    Returns:
        None.

    Examples:
        `24.22.0` succeeds, while `24.21.9` and `25.0.0` fail.
    """
    _require_node_runtime()
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    for name in ("uv", "npm", "node"):
        _write_fake_command(fake_bin, name)
    env["FAKE_NODE_VERSION"] = node_version

    result = _run_make("check-tools", env=env, variables={"HOMEBREW_BIN": ""})

    assert (result.returncode == 0) is expected_success
    assert "wrangler" not in result.stdout.lower() + result.stderr.lower()
    node_calls = [call for call in _read_calls(log_path) if call["command"] == "node"]
    assert len(node_calls) == 1
    assert node_calls[0]["args"][0] == "-e"
    assert "process.versions.node" in node_calls[0]["args"][1]


def test_check_cf_uses_only_the_static_worker_installation(tmp_path: Path) -> None:
    """Require and execute cf from the static-site Worker dependencies.

    Args:
        tmp_path: Temporary directory supplied by pytest.

    Returns:
        None.

    Examples:
        A global cf stub cannot satisfy the target when the project's
        `node_modules/.bin/cf` is absent.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    global_cf = _write_fake_command(fake_bin, "cf")
    global_cf.write_text(
        global_cf.read_text(encoding="utf-8").replace("raise SystemExit(0)", "print('global cf')\nraise SystemExit(0)"),
        encoding="utf-8",
    )
    worker_directory = tmp_path / "static worker"
    local_cf = _write_fake_command(worker_directory / "node_modules" / ".bin", "cf")
    local_cf.write_text(
        local_cf.read_text(encoding="utf-8").replace("raise SystemExit(0)", "print('local cf')\nraise SystemExit(0)"),
        encoding="utf-8",
    )

    result = _run_make(
        "check-cf",
        env=env,
        variables={"STATIC_WORKER_DIR": str(worker_directory), "HOMEBREW_BIN": ""},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "local cf" in result.stdout
    assert "global cf" not in result.stdout
    calls = _read_calls(log_path)
    assert [(call["command"], call["args"]) for call in calls] == [("cf", ["--version"])]

    local_cf.unlink()
    missing_result = _run_make(
        "check-cf",
        env=env,
        variables={"STATIC_WORKER_DIR": str(worker_directory), "HOMEBREW_BIN": ""},
    )
    assert missing_result.returncode != 0
    assert "Run make bootstrap" in missing_result.stderr
    assert len(_read_calls(log_path)) == 1


@pytest.mark.parametrize(
    ("identity", "exit_code", "expected_success", "expected_message"),
    [
        ({"authenticated": True, "tokenValid": True, "token": "do-not-print"}, 0, True, "authentication verified"),
        ({"authenticated": False}, 0, False, "not logged in"),
        ({"authenticated": True, "tokenValid": False}, 0, False, "could not validate the Cloudflare token"),
        ({"authenticated": True, "tokenValid": True}, 1, False, "exited unsuccessfully"),
    ],
)
def test_cloudflare_check_requires_authenticated_valid_cf_identity(
    tmp_path: Path,
    identity: dict[str, object],
    exit_code: int,
    expected_success: bool,
    expected_message: str,
) -> None:
    """Require cf whoami JSON to report an authenticated, valid token.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        identity: JSON identity response emitted by the fake cf command.
        exit_code: Exit status returned by the fake cf whoami command.
        expected_success: Whether the identity should pass validation.
        expected_message: Safe status text expected from the verification.

    Returns:
        None. Asserts authentication status, safe output, and command scope.

    Examples:
        A valid identity passes, while unauthenticated or invalid-token
        responses or a failed command exit fail without printing response secrets.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    env["PATH"] = f"{env['PATH']}:{Path(_require_node_runtime()).parent}"
    fake_npm = _write_fake_command(fake_bin, "npm")
    fake_npm.write_text(
        fake_npm.read_text(encoding="utf-8").replace(
            "raise SystemExit(0)",
            "if name == 'npm' and sys.argv[1:] == ['exec', '--', 'cf', 'auth', 'whoami']:\n"
            "    print(os.environ['FAKE_CF_WHOAMI_JSON'])\n"
            "    raise SystemExit(int(os.environ['FAKE_CF_WHOAMI_EXIT_CODE']))\n"
            "raise SystemExit(0)",
        ),
        encoding="utf-8",
    )
    worker_directory = tmp_path / "static worker"
    _write_fake_command(worker_directory / "node_modules" / ".bin", "cf")
    env["FAKE_CF_WHOAMI_JSON"] = json.dumps(identity)
    env["FAKE_CF_WHOAMI_EXIT_CODE"] = str(exit_code)

    result = _run_make(
        "cloudflare-check",
        env=env,
        variables={"STATIC_WORKER_DIR": str(worker_directory), "HOMEBREW_BIN": ""},
    )

    assert (result.returncode == 0) is expected_success, result.stdout + result.stderr
    assert "do-not-print" not in result.stdout + result.stderr
    assert expected_message in result.stdout + result.stderr
    calls = _read_calls(log_path)
    assert [(call["command"], call["args"]) for call in calls] == [
        ("cf", ["--version"]),
        ("npm", ["exec", "--", "cf", "auth", "whoami"]),
    ]
    assert calls[1]["cwd"] == str(worker_directory)


def test_static_worker_test_bakes_the_site_before_running(tmp_path: Path) -> None:
    """Bake the site before installing and testing the static Worker.

    Args:
        tmp_path: Temporary directory supplied by pytest.

    Returns:
        None. Asserts bake runs before the Worker dependency and test commands.

    Examples:
        `make static-worker-test` invokes bake first so the Worker test can
        serve the generated HTML and assets.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    _write_fake_command(fake_bin, "bake")
    _write_fake_command(fake_bin, "npm")
    worker_directory = tmp_path / "static worker"
    makefile = tmp_path / "Makefile"
    makefile.write_text(f"include {REPOSITORY_ROOT / 'Makefile'}\nbake:\n\t@bake\n", encoding="utf-8")

    result = _run_make(
        "static-worker-test",
        env=env,
        makefile=makefile,
        variables={"STATIC_WORKER_DIR": str(worker_directory), "HOMEBREW_BIN": ""},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    calls = _read_calls(log_path)
    assert [(call["command"], call["args"]) for call in calls] == [
        ("bake", []),
        (
            "npm",
            ["--prefix", str(worker_directory), "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        ),
        ("npm", ["--prefix", str(worker_directory), "run", "test"]),
    ]


@pytest.mark.parametrize("env_file_kind", ["relative", "absolute"])
def test_run_with_dotenv_passes_env_file_path_unchanged_and_rooted_at_invocation(
    tmp_path: Path,
    env_file_kind: str,
) -> None:
    """Resolve a relative dotenv path from the repo root, preserving spaces.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        env_file_kind: Whether the test uses a relative or absolute path.

    Returns:
        None.

    Examples:
        A relative `settings/local env.env` stays rooted at the Make
        invocation directory even after the target changes into a Worker.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    _write_fake_command(fake_bin, "uv")
    probe = _write_fake_command(fake_bin, "probe")
    worker_directory = tmp_path / "worker directory"
    worker_directory.mkdir()
    if env_file_kind == "relative":
        env_file = "settings/local env.env"
        expected_path = str(REPOSITORY_ROOT / env_file)
    else:
        env_file = str(tmp_path / "external environment.env")
        expected_path = env_file
    env["UV_ENV_FILE"] = env_file
    env.pop("UV_NO_ENV_FILE")
    wrapper_makefile = tmp_path / "dotenv wrapper.mk"
    wrapper_makefile.write_text(
        "\n".join(
            (
                f"include {REPOSITORY_ROOT / 'Makefile'}",
                ".PHONY: invoke-probe",
                "invoke-probe:",
                "\tcd "
                + shlex.quote(str(worker_directory))
                + " && $(call run-with-dotenv,"
                + shlex.quote(str(probe))
                + ")",
                "",
            )
        ),
        encoding="utf-8",
    )

    result = _run_make("invoke-probe", env=env, makefile=wrapper_makefile)

    assert result.returncode == 0, result.stdout + result.stderr
    calls = _read_calls(log_path)
    assert len(calls) == 1
    assert calls[0]["command"] == "uv"
    assert calls[0]["args"] == ["run", "--env-file", expected_path, "--", str(probe)]
    assert calls[0]["cwd"] == str(worker_directory)
    assert calls[0]["uv_env_file"] == env_file


@pytest.mark.parametrize("bypass_value", ["1", "true"])
def test_run_with_dotenv_bypasses_uv_for_supported_no_env_values(
    tmp_path: Path,
    bypass_value: str,
) -> None:
    """Run the wrapped command directly when dotenv loading is disabled.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        bypass_value: Supported `UV_NO_ENV_FILE` value.

    Returns:
        None.

    Examples:
        Both `UV_NO_ENV_FILE=1` and `UV_NO_ENV_FILE=true` skip `uv run`.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    fake_bin = Path(env["PATH"].split(os.pathsep)[0])
    probe = _write_fake_command(fake_bin, "probe")
    worker_directory = tmp_path / "worker directory"
    worker_directory.mkdir()
    env["UV_ENV_FILE"] = "settings/local env.env"
    env["UV_NO_ENV_FILE"] = bypass_value
    wrapper_makefile = tmp_path / "dotenv wrapper.mk"
    wrapper_makefile.write_text(
        "\n".join(
            (
                f"include {REPOSITORY_ROOT / 'Makefile'}",
                ".PHONY: invoke-probe",
                "invoke-probe:",
                "\tcd "
                + shlex.quote(str(worker_directory))
                + " && $(call run-with-dotenv,"
                + shlex.quote(str(probe))
                + ")",
                "",
            )
        ),
        encoding="utf-8",
    )

    result = _run_make("invoke-probe", env=env, makefile=wrapper_makefile)

    assert result.returncode == 0, result.stdout + result.stderr
    calls = _read_calls(log_path)
    assert len(calls) == 1
    assert calls[0]["command"] == "probe"
    assert calls[0]["args"] == []
    assert calls[0]["cwd"] == str(worker_directory)


@pytest.mark.parametrize(
    ("target", "confirmation", "arguments"),
    [
        (
            "legacy-worker-canary-deploy",
            "CONFIRM_LEGACY_WORKER_CANARY_DEPLOY",
            ["deploy", "--mode", "startup-canary", "--no-provision"],
        ),
        (
            "legacy-worker-delete-canary",
            "CONFIRM_LEGACY_WORKER_DELETE_CANARY",
            ["workers", "delete", "palewire-legacy-redirects-canary", "--force"],
        ),
        (
            "legacy-worker-same-zone-canary-deploy",
            "CONFIRM_LEGACY_WORKER_SAME_ZONE_CANARY_DEPLOY",
            ["deploy", "--mode", "same-zone-canary", "--no-provision"],
        ),
        (
            "legacy-worker-attach-same-zone-canary",
            "CONFIRM_LEGACY_WORKER_ATTACH_SAME_ZONE_CANARY",
            ["deploy", "--mode", "same-zone-canary-route", "--no-provision"],
        ),
        (
            "legacy-worker-delete-same-zone-canary",
            "CONFIRM_LEGACY_WORKER_DELETE_SAME_ZONE_CANARY",
            ["workers", "delete", "palewire-legacy-redirects-same-zone-canary", "--force"],
        ),
        (
            "legacy-worker-attach-routes",
            "CONFIRM_LEGACY_WORKER_ATTACH_ROUTES",
            ["deploy", "--mode", "production-routes", "--no-provision"],
        ),
        (
            "legacy-worker-detach-routes",
            "CONFIRM_LEGACY_WORKER_DETACH_ROUTES",
            ["workers", "delete", "palewire-legacy-redirects", "--force"],
        ),
        (
            "legacy-worker-delete",
            "CONFIRM_LEGACY_WORKER_DELETE",
            ["workers", "delete", "palewire-legacy-redirects", "--force"],
        ),
    ],
)
def test_legacy_worker_commands_require_confirmation(
    tmp_path: Path, target: str, confirmation: str, arguments: list[str]
) -> None:
    """Run each guarded legacy command with an offline npm stub.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        target: Deployment or deletion Make target.
        confirmation: Required environment variable for the target.
        arguments: Expected cf arguments after confirmation.

    Returns:
        None. Asserts refusal before npm and the selected mode or identity.

    Examples:
        The production attachment target refuses an unset confirmation,
        then selects production-routes when its confirmation is set to 1.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    for name in list(env):
        if name.startswith("CONFIRM_LEGACY_WORKER_"):
            del env[name]
    _write_fake_command(tmp_path / "fake bin", "npm")
    refused = _run_make(target, env=env)
    assert refused.returncode != 0
    assert confirmation in refused.stderr
    assert _read_calls(log_path) == []

    env[confirmation] = "1"
    allowed = _run_make(target, env=env)
    assert allowed.returncode == 0, allowed.stderr
    calls = _read_calls(log_path)
    assert len(calls) == 2
    assert calls[0]["args"] == [
        "--prefix",
        "workers/legacy-redirects",
        "ci",
        "--ignore-scripts",
        "--no-audit",
        "--no-fund",
    ]
    assert calls[1]["args"] == ["exec", "--", "cf", *arguments]
    assert calls[1]["cwd"] == str(REPOSITORY_ROOT / "workers/legacy-redirects")


@pytest.mark.parametrize(
    ("target", "confirmation", "mode"),
    [
        ("static-worker-preview-deploy", "CONFIRM_STATIC_WORKER_PREVIEW_DEPLOY", "preview"),
        ("static-worker-deploy", "CONFIRM_STATIC_WORKER_DEPLOY", "production"),
    ],
)
def test_static_worker_deploy_requires_confirmation(tmp_path: Path, target: str, confirmation: str, mode: str) -> None:
    """Check static deployment selection without baking or deploying.

    Args:
        tmp_path: Temporary directory supplied by pytest.
        target: Static deployment Make target.
        confirmation: Required confirmation environment variable.
        mode: Expected named cf mode.

    Returns:
        None. Asserts refusal before npm and correct deployment arguments.

    Examples:
        The preview target selects preview only after its confirmation is set.
    """
    log_path = tmp_path / "calls.jsonl"
    env = _test_environment(tmp_path, log_path)
    env.pop(confirmation, None)
    _write_fake_command(tmp_path / "fake bin", "npm")
    makefile = tmp_path / "Makefile"
    makefile.write_text(f"include {REPOSITORY_ROOT / 'Makefile'}\nbake:\n\t@:\n")
    refused = _run_make(target, env=env, makefile=makefile)
    assert refused.returncode != 0
    assert confirmation in refused.stderr
    assert _read_calls(log_path) == []
    env[confirmation] = "1"
    allowed = _run_make(target, env=env, makefile=makefile)
    assert allowed.returncode == 0, allowed.stderr
    calls = _read_calls(log_path)
    assert len(calls) == 2
    assert calls[1]["args"] == ["exec", "--", "cf", "deploy", "--mode", mode, "--no-provision"]
    assert calls[1]["cwd"] == str(REPOSITORY_ROOT / "workers/static-site")
