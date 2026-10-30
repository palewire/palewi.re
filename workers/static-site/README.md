# Static-site Worker

The package pins `cf` 1.0.0-beta.26 and Wrangler 4.156.0 as its bundler.
Use Node.js 24.22 or later in the Node 24 series. Run `make bootstrap` from
the repository root to install locked dependencies.

`cloudflare.config.ts` preserves the four production routes and the existing
R2 media bucket. Production workers.dev and preview URLs are disabled. The
named `preview` mode deploys `palewire-static-site-preview` with no routes;
unknown modes and automatic Worker Previews are rejected.

`wrangler.config.ts` points the bundler to the baked `../../dist` directory.
Both modes run the Worker before assets, preserve trailing-slash handling and
the custom 404 page, and use the `ASSETS` binding. `TALK_MEDIA` uses the existing
`palewire-talk-media` R2 bucket; remote access during local development remains
enabled. `--no-provision` prevents deployment from creating a replacement bucket.

From the repository root, run `make static-worker-test` and
`make static-worker-validate`. Validation bakes the site, generates binding
and runtime types, dry-runs both modes, and profiles startup. Generated
`.cloudflare/` output and types stay untracked.

Authenticate with `npm exec -- cf auth login` from this package or set
`CLOUDFLARE_API_TOKEN`. The read-only `make cloudflare-check` still uses
Wrangler's separate login. Deploy with the guarded Makefile targets:

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

- Google Fonts for styles and fonts.
- Google Slides, Vimeo, SoundCloud, and the archived S3 Leaflet examples for
  historical iframes.
- The canonical `palewi.re` and `palewire.s3.amazonaws.com` hosts for
  historical images and videos.

Inline styles remain enabled because published post HTML uses them. Executable
scripts are limited to the site itself. The Permissions Policy disables only
camera, geolocation, microphone, payment, and USB; it does not restrict the
autoplay or fullscreen capabilities used by existing embeds.

Cross-origin isolation headers are intentionally deferred: COEP and related
headers would require every existing third-party embed and asset to opt in.

`/.well-known/security.txt` is a baked plain-text asset. Renew its `Expires`
date in `coltrane/templates/security.txt` before 2027-08-01.
