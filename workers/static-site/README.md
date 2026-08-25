# Static-site security headers

The Worker applies a CSP that keeps the published site's required resource
origins explicit:

- Google Fonts for styles and fonts.
- Google Slides, Vimeo, SoundCloud, and the archived S3 Leaflet examples for
  historical iframes.
- The canonical `palewi.re`, Google Charts, and the legacy `www.palewire.com`
  hosts for historical images.

Inline styles remain enabled because published post HTML uses them. Executable
scripts are limited to the site itself. The Permissions Policy disables only
camera, geolocation, microphone, payment, and USB; it does not restrict the
autoplay or fullscreen capabilities used by existing embeds.

Cross-origin isolation headers are intentionally deferred: COEP and related
headers would require every existing third-party embed and asset to opt in.
`/.well-known/security.txt` is also deferred until the site has a maintained,
public security contact and policy URL.
