# Cloudflare recovery

Production is served by the `palewire-static-site` Cloudflare Worker. Its
routes cover `palewi.re`, `www.palewi.re`, `palewire.com`, and
`www.palewire.com`. The Mastodon discovery and legacy redirect Workers have
more-specific routes and must remain in place.

## Detect a problem

The **CI** workflow verifies the deployment after it publishes the Worker.
The **Production smoke test** workflow repeats the same focused checks daily
and can be started from **Actions → Production smoke test → Run workflow**.
The manual `base_url` input is useful for testing another endpoint with the
same production routes.

The checks cover the canonical pages, `/health/`, CSS and image assets, the
feed, sitemap, robots file, 404 page, Mastodon discovery endpoints, legacy
redirect paths, and both `palewire.com` redirect hosts.

## Roll back a Worker release

1. Open the failed CI or smoke run and note the first bad deployment. From a
   checkout of this repository, identify the last known-good commit with
   `git log --oneline`.
2. List deployed Worker versions and roll back the bad version:

   ```bash
   cd workers/static-site
   npm ci --ignore-scripts --no-audit --no-fund
   npm exec -- wrangler versions list
   npm exec -- wrangler rollback <version-id>
   ```

3. Verify the public service from the repository root:

   ```bash
   BASE_URL=https://palewi.re scripts/verify-static-site.sh
   BASE_URL=https://palewi.re scripts/verify-worker-endpoints.sh
   BASE_URL=https://palewi.re scripts/verify-legacy-redirects.sh
   scripts/verify-legacy-domains.sh
   ```

4. If the version list does not contain the known-good release, check out its
   commit and redeploy the static Worker:

   ```bash
   git switch --detach <known-good-commit>
   make bake
   npm --prefix workers/static-site ci --ignore-scripts --no-audit --no-fund
   (cd workers/static-site && npm exec -- wrangler deploy --env="" --strict)
   ```

   Re-run all four verification commands after the redeploy. Return to the
   normal branch when the recovery is complete.

## Check Cloudflare DNS and routes

In the Cloudflare dashboard, confirm that both `palewi.re` and
`palewire.com` are active zones, and that the four production hostnames have
proxied DNS records. Under **Workers & Pages → Overview → Routes**, confirm
that `palewire-static-site` owns the four `/*` routes in
`workers/static-site/wrangler.jsonc`. Confirm that the more-specific
Mastodon and legacy redirect routes still point to their respective Workers.

Use `curl -sS -D - -o /dev/null` against each hostname while checking; do not
follow redirects. The canonical host should serve the site, the two legacy
hosts should return `301` to `https://palewi.re/`, and `www.palewi.re` should
return a `301` to the equivalent canonical path.

## Locate and validate the private database archive

The final Heroku PostgreSQL dump is preserved privately in
`palewire/palewi.re-archive`; it is not part of this repository. The retirement
notes identify `database/production-postgres-b1232.dump`, with its SHA-256
entry in `checksums.sha256`. Heroku credentials and connection strings are
intentionally absent.

With GitHub authentication already configured, clone or open that private
repository outside this checkout. Then validate it without connecting to a
database:

```bash
cd /path/to/palewi.re-archive
sha256sum -c checksums.sha256
pg_restore --version
pg_restore --list database/production-postgres-b1232.dump > /dev/null
```

The recorded validation used `pg_restore 18.2`. Keep the archive outside this
repository and never add credentials, connection strings, or the dump to a
commit.
