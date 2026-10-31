# Static-site Worker

The package pins `cf` 1.0.0-beta.26, Vite 8.3.5, and
`@cloudflare/vite-plugin` 2.0.0-beta.v.8. Use Node.js 24.22 or later in the
Node 24 series. Run `make bootstrap` from the repository root to install
locked dependencies.

`cloudflare.config.ts` preserves the four production routes and the existing
R2 media bucket. Production workers.dev and preview URLs are disabled. The
named `preview` mode deploys `palewire-static-site-preview` with no routes;
unknown modes and automatic Worker Previews are rejected.

`vite.config.ts` points Vite's `publicDir` to the baked `../../dist` directory.
The `development` mode runs as `palewire-static-site-development` with no
routes. Its Vite server listens on `127.0.0.1:5173`; set `STATIC_DEV_PORT` to
choose another port. The Worker runs before assets, preserves trailing-slash
handling and the custom 404 page, and uses the `ASSETS` binding.

From the repository root, run `make bake`, then start local development with
`npm --prefix workers/static-site run dev`. Builds reject missing baked assets.

`TALK_MEDIA` uses the existing `palewire-talk-media` R2 bucket, and remote R2
access stays enabled by default during local development. For offline `cf dev`
tests or local serving, set `STATIC_WORKER_LOCAL=1` to disable remote bindings
and use local bindings instead. `--no-provision` prevents deployment from
creating a replacement bucket.

From the repository root, run `make static-worker-test` and
`make static-worker-validate`. Neither check needs Cloudflare API access or a
deployed Worker. The test target first bakes the site, then exercises the
Worker with the actual generated HTML and assets in local workerd; its local
R2 regression covers byte-range responses.
Validation bakes the site, generates binding and runtime types, dry-runs the
production and preview modes, and profiles startup. Tests ensure those modes
retain the same asset and R2 settings. Generated `.cloudflare/` output and
types stay untracked.

Authenticate with `npm exec -- cf auth login` from this package or set
`CLOUDFLARE_API_TOKEN`. The read-only `make cloudflare-check` uses this same
`cf` authentication and validates the JSON from `cf auth whoami`. Deploy with
the guarded Makefile targets:

```bash
CONFIRM_STATIC_WORKER_PREVIEW_DEPLOY=1 make static-worker-preview-deploy
BASE_URL=https://the-preview-url make static-worker-verify
CONFIRM_STATIC_WORKER_DEPLOY=1 make static-worker-deploy
BASE_URL=https://palewi.re make static-worker-verify
```

The production workflow bakes the site and uses the same explicit production
mode. Post-deployment checks cover the main pages, feeds, security headers,
assets, Mastodon endpoints, and legacy redirects.

## Security headers

The Worker applies a CSP that keeps the published site's required resource
origins explicit:

- The Cloudflare Web Analytics beacon for its versioned script path and a
  same-origin connection for its RUM endpoint.
- Google Slides, Vimeo, SoundCloud, and the archived S3 Leaflet examples for
  historical iframes.
- The canonical `palewi.re` and `palewire.s3.amazonaws.com` hosts for
  historical images and videos.

Inline styles remain enabled because published post HTML uses them. Executable
scripts are limited to the site itself and the Cloudflare Web Analytics beacon.
Fonts and styles are served locally; Google Fonts is not allowed by the CSP.
The Permissions Policy disables only camera, geolocation, microphone, payment,
and USB; it does not restrict the autoplay or fullscreen capabilities used by
existing embeds.

Cross-origin isolation headers are intentionally deferred: COEP and related
headers would require every existing third-party embed and asset to opt in.

`/.well-known/security.txt` is a baked plain-text asset. Renew its `Expires`
date in `coltrane/templates/security.txt` before 2027-08-01.
