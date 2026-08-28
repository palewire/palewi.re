---
name: rollout-sphinx-theme
description: Release sphinx-palewire-theme and safely update its Sphinx satellite sites. Use when changing the shared theme, publishing a theme version, or rolling a released version out to palewire documentation sites.
---

# Roll out the Sphinx theme

Publish the shared theme first, then update each direct consumer in a focused
pull request. Never point sites at an unreleased commit.

## 1. Prepare and release the theme

1. Work in `palewire/sphinx-palewire-theme`, not a consumer repository.
2. Read its `AGENTS.md`, then make the theme change with matching rendered-page
   tests.
3. Run the documented checks: pre-commit, unit tests, Sphinx HTML build, link
   check, and `uv build`.
4. Open a focused pull request. Merge only after required checks and reviews
   pass.
5. Choose the next unused semantic patch tag. Check both existing tags and
   GitHub releases: previous tags may exist without a published release.
6. Push an annotated release tag from the merged `main` commit.
7. Confirm the tag workflow's PyPI job passed, then verify the exact version:

   ```bash
   curl --fail --silent --show-error \
     https://pypi.org/pypi/sphinx-palewire-theme/VERSION/json
   ```

The release workflow must match normal version tags with `tags: ["0.*"]`.
Do not use `workflow_dispatch` to publish a setuptools-scm version: a
non-tagged checkout produces a development version.

## 2. Inventory consumers

Search the `palewire` account for configured theme users:

```bash
gh api \
  'search/code?q=%22html_theme+%3D+%5C%22palewire%5C%22%22+user%3Apalewire&per_page=100'
```

Classify each result before editing:

- **Direct user:** `pyproject.toml` declares `sphinx-palewire-theme`.
- **Legacy user:** a `Pipfile`, requirements file, or another package source
  supplies the theme.
- **Not a user:** the theme line is commented or no dependency exists.

Check for open dependency pull requests before creating one. Do not duplicate
or overwrite another update. Report legacy and non-user sites separately; do
not guess how to modernize their package setup as part of a theme rollout.

## 3. Update direct users

For every direct user:

1. Change the dependency to `sphinx-palewire-theme>=VERSION`, or change an
   exact pin to `==VERSION` when that repository intentionally uses exact
   pins.
2. Refresh only the existing lockfile with the repository's package tool.
   Do not upgrade unrelated packages.
3. Run the narrowest existing documentation, test, or install check that
   covers the update.
4. Open one focused pull request per repository. State the theme version and
   validation result in the pull request body.

Run independent consumer updates in parallel. Keep an inventory of every pull
request, skipped repository, and validation issue.

## 4. Merge and report

Merge only pull requests that GitHub marks ready and whose required checks
pass. Update a branch that is behind `main`, then wait for its checks again.
Do not weaken repository protections to merge a routine dependency update.

If GitHub Actions fails because CodeQL upload is disabled or unavailable,
record that repository configuration issue. Do not enable paid GitHub
features or bypass a required check without the repository owner's explicit
instruction.

Finish with:

- the published theme version and release URL;
- all consumer pull request URLs and merge status;
- validation failures or pending checks;
- existing dependency PRs left untouched; and
- legacy users with their package source and a concrete next action.
