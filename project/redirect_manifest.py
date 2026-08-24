"""Validated source of truth for legacy redirects and their Worker route plan."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from django.urls import path, re_path
from django.views.generic import RedirectView

MANIFEST_PATH = Path(__file__).with_name("redirects.yaml")
ROUTE_HOST = "palewi.re"
ROUTE_LIMIT = 100
CAPTURE_PATTERNS = {
    "digits": r"\d+",
    "digits2": r"\d{2}",
    "digits4": r"\d{4}",
    "path": r".+",
    "segment": r"[^/]+",
    "slug": r"[-\w]+",
}
_CAPTURE = re.compile(r"{([a-z][a-z0-9_]*)}")


class RedirectManifestError(ValueError):
    """Raised when the redirect manifest cannot be deployed safely."""


@dataclass(frozen=True)
class RedirectRule:
    source: str
    destination: str
    captures: dict[str, str]
    routes: tuple[str, ...]
    examples: tuple[str, ...]

    @property
    def is_dynamic(self) -> bool:
        return bool(self.captures)

    @property
    def django_pattern(self) -> str:
        parts: list[str] = []
        position = 0
        for match in _CAPTURE.finditer(self.source):
            parts.append(re.escape(self.source[position : match.start()]))
            name = match.group(1)
            parts.append(f"(?P<{name}>{CAPTURE_PATTERNS[self.captures[name]]})")
            position = match.end()
        parts.append(re.escape(self.source[position:]))
        return f"^{''.join(parts)}$"

    @property
    def django_destination(self) -> str:
        return _CAPTURE.sub(lambda match: f"%({match.group(1)})s", self.destination)

    def destination_for(self, path_value: str) -> str | None:
        match = re.fullmatch(self.django_pattern, path_value.lstrip("/"))
        if match is None:
            return None
        return self.destination.format(**match.groupdict())


def _require_string(value: Any, field: str, index: int) -> str:
    if not isinstance(value, str) or not value:
        raise RedirectManifestError(f"redirect {index}: '{field}' must be a non-empty string")
    return value


def _validate_source(source: str, index: int) -> None:
    if source.startswith("/") or "*" in source or "?" in source or "#" in source:
        raise RedirectManifestError(
            f"redirect {index}: source must be a relative path without query strings or fragments"
        )
    if source.startswith("../") or "/../" in source or "//" in source:
        raise RedirectManifestError(f"redirect {index}: source contains an unsafe or malformed path segment")
    if "{" in _CAPTURE.sub("", source) or "}" in _CAPTURE.sub("", source):
        raise RedirectManifestError(f"redirect {index}: source has an invalid capture template")


def _validate_destination(destination: str, index: int) -> None:
    if destination.startswith("/"):
        if destination.startswith("//") or "?" in destination or "#" in destination:
            raise RedirectManifestError(
                f"redirect {index}: relative destination must be a path without query strings or fragments"
            )
        return
    parsed = urlparse(destination)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RedirectManifestError(
            f"redirect {index}: destination must be an absolute HTTP(S) URL or an absolute path"
        )


def _template_names(value: str) -> set[str]:
    return set(_CAPTURE.findall(value))


def _sources_overlap(left: RedirectRule, right: RedirectRule) -> bool:
    """Conservatively reject rules that could match the same source path."""
    left_parts = left.source.strip("/").split("/")
    right_parts = right.source.strip("/").split("/")
    if len(left_parts) != len(right_parts):
        return False
    for left_part, right_part in zip(left_parts, right_parts, strict=True):
        left_dynamic = bool(_CAPTURE.fullmatch(left_part))
        right_dynamic = bool(_CAPTURE.fullmatch(right_part))
        if not left_dynamic and not right_dynamic and left_part != right_part:
            return False
    return True


def _route_matches(path_value: str, route_prefix: str) -> bool:
    return path_value.startswith(f"/{route_prefix}")


def _validate_rule(record: Any, index: int) -> RedirectRule:
    if not isinstance(record, dict):
        raise RedirectManifestError(f"redirect {index}: record must be a mapping")
    allowed = {"source", "destination", "captures", "routes", "examples"}
    unknown = set(record) - allowed
    if unknown:
        raise RedirectManifestError(f"redirect {index}: unknown fields: {', '.join(sorted(unknown))}")

    source = _require_string(record.get("source"), "source", index)
    destination = _require_string(record.get("destination"), "destination", index)
    _validate_source(source, index)
    _validate_destination(destination, index)
    names = _template_names(source)
    captures = record.get("captures", {})
    if not isinstance(captures, dict) or set(captures) != names:
        raise RedirectManifestError(f"redirect {index}: captures must name every source template exactly once")
    if any(kind not in CAPTURE_PATTERNS for kind in captures.values()):
        raise RedirectManifestError(f"redirect {index}: captures must use only {', '.join(sorted(CAPTURE_PATTERNS))}")
    if not _template_names(destination).issubset(names):
        raise RedirectManifestError(f"redirect {index}: destination references an unknown capture")
    route_prefixes = record.get("routes", [])
    if not isinstance(route_prefixes, list) or any(
        not isinstance(prefix, str) or not prefix for prefix in route_prefixes
    ):
        raise RedirectManifestError(f"redirect {index}: routes must be a list of non-empty path prefixes")
    if any(prefix.startswith("/") or "*" in prefix or "?" in prefix or "#" in prefix for prefix in route_prefixes):
        raise RedirectManifestError(f"redirect {index}: routes must be literal relative path prefixes")
    if names and not route_prefixes:
        raise RedirectManifestError(f"redirect {index}: dynamic redirects require explicit Cloudflare route prefixes")
    if not names and route_prefixes:
        raise RedirectManifestError(f"redirect {index}: exact redirects derive their Cloudflare route automatically")
    if names:
        static_prefix = source.split("{", maxsplit=1)[0]
        expected_prefixes = (
            {str(value) for value in range(10)}
            if source.startswith("{year}") and captures.get("year") == "digits4"
            else {static_prefix}
        )
        if set(route_prefixes) != expected_prefixes:
            raise RedirectManifestError(f"redirect {index}: routes do not safely cover the dynamic source")
    examples = record.get("examples", [])
    if not isinstance(examples, list) or any(not isinstance(example, str) for example in examples):
        raise RedirectManifestError(f"redirect {index}: examples must be a list of paths")
    if names and not examples:
        raise RedirectManifestError(f"redirect {index}: dynamic redirects require boundary examples")
    rule = RedirectRule(source, destination, dict(captures), tuple(route_prefixes), tuple(examples))
    for example in rule.examples:
        if not example.startswith("/") or rule.destination_for(example) is None:
            raise RedirectManifestError(f"redirect {index}: example {example!r} is not covered by its source")
        if not any(_route_matches(example, prefix) for prefix in rule.routes):
            raise RedirectManifestError(f"redirect {index}: route coverage gap for {example!r}")
    if rule.destination_for(f"/{source}") == f"/{source}":
        raise RedirectManifestError(f"redirect {index}: redirect loops to itself")
    return rule


def load_redirect_manifest(path_value: Path = MANIFEST_PATH) -> tuple[RedirectRule, ...]:
    """Load and validate the YAML manifest before Django or Workers consume it."""
    try:
        raw = yaml.safe_load(path_value.read_text())
    except yaml.YAMLError as error:
        raise RedirectManifestError(f"{path_value}: invalid YAML: {error}") from error
    if not isinstance(raw, dict) or set(raw) != {"redirects"} or not isinstance(raw["redirects"], list):
        raise RedirectManifestError(f"{path_value}: expected a single 'redirects' list")
    rules = tuple(_validate_rule(record, index) for index, record in enumerate(raw["redirects"], start=1))
    for index, rule in enumerate(rules):
        for prior in rules[:index]:
            if _sources_overlap(prior, rule):
                raise RedirectManifestError(f"redirect {index + 1}: source overlaps {prior.source!r}")
    route_plan = cloudflare_route_plan(rules)
    if len(route_plan) > ROUTE_LIMIT:
        raise RedirectManifestError(f"redirect route plan exceeds the {ROUTE_LIMIT}-route safety limit")
    if f"{ROUTE_HOST}/*" in route_plan:
        raise RedirectManifestError("redirect route plan must not use a broad site-wide route")
    return rules


def cloudflare_route_plan(rules: tuple[RedirectRule, ...]) -> tuple[str, ...]:
    """Return the deduplicated, ordered route plan used by deployment commands."""
    routes = [
        *(f"{ROUTE_HOST}/{rule.source}*" for rule in rules if not rule.is_dynamic),
        *(f"{ROUTE_HOST}/{prefix}*" for rule in rules if rule.is_dynamic for prefix in rule.routes),
    ]
    return tuple(dict.fromkeys(routes))


RULES = load_redirect_manifest()
STATIC_REDIRECTS = {rule.source: rule.destination for rule in RULES if not rule.is_dynamic}


patterns = [
    *(
        path(rule.source, RedirectView.as_view(url=rule.destination))
        if not rule.is_dynamic
        else re_path(rule.django_pattern, RedirectView.as_view(url=rule.django_destination))
        for rule in RULES
    ),
]


def main() -> None:
    """Print production verification cases as tab-separated source and Location values."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-cases", action="store_true")
    args = parser.parse_args()
    if not args.production_cases:
        parser.error("use --production-cases")
    for rule in RULES:
        examples = (f"/{rule.source}",) if not rule.is_dynamic else rule.examples
        for example in examples:
            destination = rule.destination_for(example)
            if destination is None:
                raise RedirectManifestError(f"route coverage gap for {example!r}")
            print(f"{example}\t{destination}")


if __name__ == "__main__":
    main()
