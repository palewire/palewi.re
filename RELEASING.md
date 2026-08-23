# Releases

Deployments and releases serve different purposes for this site:

- Every merge to `main` deploys automatically after CI passes.
- A GitHub release records a meaningful batch of changes for readers and
  maintainers.

GitHub Releases are the canonical changelog. The repository does not maintain a
separate `CHANGELOG.md`.

## Pull requests

Before merging, apply exactly one changelog label to each pull request:

| Label | Use for |
| --- | --- |
| `feature` | New site features or content capabilities |
| `improvement` | Meaningful improvements to existing behavior or presentation |
| `fix` | User-facing or operational bug fixes |
| `maintenance` | Tooling, dependencies, tests, and internal upkeep |
| `skip-changelog` | Changes that should not appear in release notes |

Dependabot's existing `dependencies` and `github_actions` labels are grouped
under Maintenance automatically. The existing `enhancement` label is grouped
under Improvements.

## When to release

Publish a release after a meaningful batch of changes, roughly monthly when
there are changes worth announcing. A release is not required for every
deployment.

## Version numbers

Use semantic version numbers:

- Increment the minor number for features or meaningful improvements, such as
  `v2.1.0`.
- Increment the patch number for fixes and maintenance, such as `v2.1.1`.
- Increment the major number for a major redesign or operational change, such
  as `v3.0.0`.

The first recorded release is tagged `v2`. Treat it as `v2.0.0` when choosing
the next version. Do not update the version in `pyproject.toml`; that describes
the local Python project, not the deployed website.

## Release checklist

1. Confirm all intended pull requests are merged and have a changelog label.
2. Confirm CI passed on the latest `main` commit.
3. Confirm the production smoke test passed for that deployment.
4. Record the exact deployed commit:

   ```bash
   git fetch origin main
   SHA=$(git rev-parse origin/main)
   ```

5. Create a draft release with generated notes:

   ```bash
   VERSION=v2.1.0
   gh release create "$VERSION" \
     --target "$SHA" \
     --title "$VERSION" \
     --generate-notes \
     --draft
   ```

6. Edit the draft on GitHub. Add a short **Highlights** section above the
   generated changelog that explains the most important changes in plain
   language.
7. Check that every expected pull request appears in the generated notes, then
   publish the draft.

The tag must point to the deployed commit. If the release reveals a production
problem, roll back Heroku first; do not move or replace a published tag.
