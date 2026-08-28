"""Tests for the file-backed legacy redirect source of truth."""

from pathlib import Path

import pytest

from project.redirect_manifest import (
    ROUTE_HOST,
    RULES,
    RedirectManifestError,
    cloudflare_route_plan,
    load_redirect_manifest,
)


def write_manifest(path: Path, contents: str) -> Path:
    path.write_text(contents)
    return path


def test_manifest_has_every_legacy_rule_and_a_narrow_route_plan():
    exact_rules = [rule for rule in RULES if not rule.is_dynamic]
    dynamic_rules = [rule for rule in RULES if rule.is_dynamic]

    assert len(exact_rules) == 21
    assert len(dynamic_rules) == 8
    route_plan = cloudflare_route_plan(RULES)
    assert len(route_plan) == 36
    assert all(route.startswith(f"{ROUTE_HOST}/") for route in route_plan)
    assert all(route != f"{ROUTE_HOST}/*" for route in route_plan)
    assert all(route.endswith("*") and "*" not in route[:-1] for route in route_plan)


@pytest.mark.parametrize(
    "path,destination",
    [
        ("/tag/caf%C3%A9/", "/who-is-ben-welsh/"),
        ("/happyhours/nested/path/", "/"),
        ("/images/space%20name.jpg", "https://palewire.s3.amazonaws.com/img/space%20name.jpg"),
        ("/applications/legacy/page/", "/apps/legacy/page/"),
        ("/0000/00/00/a/", "/posts/0000/00/00/a/"),
    ],
)
def test_manifest_dynamic_examples_preserve_encoded_captures(path, destination):
    assert next(rule.destination_for(path) for rule in RULES if rule.destination_for(path) is not None) == destination


@pytest.mark.parametrize(
    "contents,match",
    [
        (
            "redirects:\n  - source: feed/\n    destination: javascript:alert(1)\n",
            "HTTP\\(S\\)",
        ),
        (
            "redirects:\n  - source: feed/\n    destination: /\n  - source: feed/\n    destination: /work/\n",
            "overlaps",
        ),
        (
            "redirects:\n  - source: tag/{name}/\n    destination: /{missing}/\n    captures:\n      name: segment\n    examples: [/tag/example/]\n",
            "unknown capture",
        ),
        (
            "redirects:\n  - source: ../feed/\n    destination: /\n",
            "unsafe",
        ),
        (
            "redirects:\n  - source: loop/\n    destination: /loop/\n",
            "loops",
        ),
        (
            "redirects:\n  - source: apps/page/{page}/\n    destination: /apps/page/{page}/\n    captures:\n      page: digits\n    routes: [apps/page/]\n    examples: [/apps/page/1/]\n",
            "loops",
        ),
    ],
)
def test_manifest_rejects_unsafe_or_ambiguous_rules(tmp_path, contents, match):
    with pytest.raises(RedirectManifestError, match=match):
        load_redirect_manifest(write_manifest(tmp_path / "redirects.yaml", contents))
