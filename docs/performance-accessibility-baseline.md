# Performance and accessibility baseline

This is the reference baseline for the static site. It records one production
Lighthouse run and a local pa11y run on 2026-08-25. Lab measurements vary with
the test machine, network, and third parties, so use them to find regressions
and guide investigation, not as merge-blocking thresholds.

## Scope and method

The core pages are the bio, posts, work, talks, docs, and the representative
post `/posts/2025/05/21/ire-podcast-transcript/`.

- **Accessibility:** pa11y 4.1.1 with WCAG 2 AA, served locally by Django.
- **Performance:** Lighthouse 12.8.2 against `https://palewi.re`, using its
  default mobile lab settings and the performance, accessibility, best
  practices, and SEO categories.
- **Page weight:** Lighthouse transfer size includes compressed responses and
  resources requested during the audit. HTML bytes are uncompressed production
  response bytes.

## Results

| Page | Performance | Accessibility | Best practices | SEO | LCP | Transfer / requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Bio | 85 | 100 | 100 | 100 | 3.1 s | 106 KiB / 8 |
| Posts | 85 | 100 | 100 | 100 | 3.3 s | 56 KiB / 7 |
| Work | 89 | 100 | 100 | 100 | 3.0 s | 80 KiB / 7 |
| Talks | 82 | 100 | 100 | 100 | 3.6 s | 59 KiB / 7 |
| Docs | 86 | 100 | 100 | 100 | 3.3 s | 55 KiB / 7 |
| Podcast transcript | 84 | 91 before fix | 79 before fix | 100 | 3.2 s | 1,454 KiB / 31 |

All pages reported 0 ms total blocking time and 0 cumulative layout shift.
The local pa11y run found no errors on the five listing pages. It found four
errors on the podcast transcript: an unnamed frame plus low-contrast
attribution text and links. The embed now has a descriptive title and
`#767676` attribution text; the representative post is included in pa11y CI
to retain the fix.

### Page weight and asset breakdown

The uncompressed HTML responses were 43 KiB (bio), 50 KiB (posts), 293 KiB
(work), 80 KiB (talks), 36 KiB (docs), and 26 KiB (podcast transcript).
Compression keeps the non-embed pages under 106 KiB transferred.

The largest regular-page resources were:

1. Bio image: 44 KiB WebP transferred.
2. Libre Franklin font: 29 KiB.
3. Cloudflare Insights beacon: 12 KiB.
4. Site stylesheet: 4 KiB.

The SoundCloud player is the outlier: its main script transferred 1,225 KiB,
with two embedded fonts adding 200 KiB and 31 total requests. The player also
sets third-party cookies and prevents back/forward-cache restoration. Those
are provider behavior, not a site error.

### Blocking resources and third parties

Lighthouse identified the Google Fonts stylesheet as the sole render-blocking
resource on every core page, with estimated savings of 0.8--1.6 seconds.
The stylesheet preconnects to Google Fonts and uses `display=swap`, so text is
not hidden, but its loading strategy remains the shared measured opportunity.

Regular pages use Google Fonts (about 31 KiB) and the Cloudflare Insights
beacon (12 KiB). The representative post additionally loads the SoundCloud
embed. No third-party code produced measurable main-thread blocking in this
run.

## Targets

These targets preserve the measured baseline rather than inventing a budget:

- pa11y reports zero WCAG 2 AA errors for all six pages.
- Lighthouse accessibility remains 100 for all six pages.
- Core pages without a third-party embed remain at or below 110 KiB transferred
  and 10 requests in the scheduled Lighthouse report.
- A regular core page scoring below 80 for Lighthouse performance, or with LCP
  above 4 seconds, needs investigation. These are review signals, not required
  checks, because scheduled production measurements are network-sensitive.
- Embed pages are measured separately. Any change to the SoundCloud player must
  document its before/after transfer size, request count, accessibility score,
  and user-visible loading behavior.

## Reproducing the baseline

Run the local accessibility audit in two terminals. `make serve` prints the
worktree-specific port; use that value for `PORT`.

```sh
make serve
make a11y PORT=8729
```

For a production Lighthouse report, use the same version and categories as the
baseline. Replace the URL to audit another core page.

```sh
npx --yes lighthouse@12.8.2 https://palewi.re/who-is-ben-welsh/ \
  --only-categories=performance,accessibility,best-practices,seo \
  --output=json \
  --output-path=/tmp/palewire-lighthouse.json \
  --chrome-flags='--headless=new --no-sandbox'
```

CI runs the pa11y configuration on pull requests and scheduled production
Lighthouse reports on Sundays. The Lighthouse job uploads reports as workflow
artifacts and remains non-blocking.

## Current behavior

SoundCloud players use their published iframes and load automatically, without
requiring JavaScript or an activation button. This intentionally restores the
normal player experience at the cost of the third-party requests and cookies
described above. The representative iframe retains its descriptive title and
published attribution.

Libre Franklin is now served from the site's own static assets. The normal and
italic Latin variable WOFF2 files are the same Google Fonts faces previously
requested by the stylesheet and are licensed under the SIL Open Font License
1.1, included beside the assets. This preserves the font family, weights,
`font-display: swap`, and fallback stack while eliminating requests to Google
Fonts and making the implementation compatible with a self-only future font
content policy.
