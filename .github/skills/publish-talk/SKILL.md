---
name: publish-talk
description: Create or update a permanent talk page or archived external talk link. Use whenever adding a talk detail page, locally hosting a talk deck, publishing a talk transcript or captions, or preserving an external talk page.
---

# Publish a talk page

Use this workflow to make a selected `talks.yaml` entry into a permanent page
at `/talks/<slug>/`. It builds on the reusable talk-detail support already in
the site. Keep the work focused on one talk at a time.

## Before publishing

- Treat a user request to publish talk assets as confirmation that they have
  permission to republish the deck and recording. Ask only if they say the
  permission status is uncertain or restricted.
- Keep the original `slides_url` and `video_url` in `talks.yaml` for source
  reference.
- Use `short_title` when the full title is too long for the page heading.
  The page displays the remaining title as its subtitle.
- Do not deploy the Worker or alter Cloudflare routes as part of this
  workflow.

## Link an external-only talk

When no approved deck, recording, or other local asset is available, keep the
talk as a catalog entry rather than creating an empty detail page:

1. Keep the external event or materials URL in `slides_url` or `video_url`.
2. Find or create a Wayback Machine snapshot and add it as `archive_url`.
3. Do not set `slug` or add local talk assets.

The talks list will link to both the external source and its archived copy.

## Link a related guide

When a first-party guide is the useful companion to a talk, add its URL as
`guide_url`. Do not add `slug`, local assets, or a Wayback snapshot unless
other talk materials also require them. The talks list labels this link
“Guide.”

## Create the page assets

Create a directory named for the talk slug:

```text
coltrane/static/talks/<slug>/
```

Commit these source assets to the repository:

- `slides/slide-01.png`, etc. — presentation pages rendered at 150 DPI.
- `index.html` and `deck.js` — a local Reveal.js deck. Match the deck frame
  to the presentation's actual aspect ratio.
- A compact presentation PDF, kept below the repository's 5 MB file limit.
- `notes.txt` — extracted slide text.
- `transcript.txt` — the spoken transcript, when a recording is available.
- `captions.vtt` — WebVTT captions, when a recording is available.

Use `.github/skills/archive-media/SKILL.md` before downloading media for
preservation. Do not commit the recording itself; it belongs in the private
`palewire-talk-media` R2 bucket.

## Build text readers

Do not use iframes for slide text or transcripts, and do not show hundreds of
lines by default. Instead:

1. Create committed template fragments at
   `coltrane/templates/coltrane/talks/<slug>-notes.html` and
   `coltrane/templates/coltrane/talks/<slug>-transcript.html`.
2. Render those fragments inside the detail template's native `<details>`
   readers.
3. Put extracted slide text immediately below the deck.
4. Put the timestamped transcript immediately below the recording.
5. Round displayed transcript timestamps to whole seconds. Use a uniform
   fixed-width time column and 500 weight for timecodes.

The raw `notes.txt`, `transcript.txt`, and `captions.vtt` files are the
committed source artifacts. The HTML fragments are their readable page
presentation.

## Add talk metadata

Add the optional fields that apply to the matching record in
`coltrane/content/talks.yaml`:

```yaml
slug: example-talk
short_title: Example talk
deck_url: /static/talks/example-talk/
pdf_url: /static/talks/example-talk/example-talk.pdf
notes_template: coltrane/talks/example-talk-notes.html
notes_text_url: /static/talks/example-talk/notes.txt
transcript_template: coltrane/talks/example-talk-transcript.html
transcript_text_url: /static/talks/example-talk/transcript.txt
local_video_url: /media/talks/example-talk/video.mp4
captions_url: /static/talks/example-talk/captions.vtt
poster_url: /media/talks/example-talk/poster.jpg
```

Only add URLs for assets that exist. The Downloads section should use the
same labels as the page: `Slides PDF`, `Recording video`, `Extracted slide
text`, and `Timestamped transcript`.

For an external-only talk, use only the source and Wayback URLs:

```yaml
slides_url: https://example.org/event
archive_url: https://web.archive.org/web/20260101000000/https://example.org/event
```

## Upload recording media

Load the `wrangler` skill before using Wrangler. Verify the pinned version:

```bash
make check-wrangler
```

Upload the approved MP4 and optional poster to the private R2 bucket:

```bash
cd workers/static-site
npm exec -- wrangler r2 object put \
  palewire-talk-media/talks/<slug>/video.mp4 \
  --remote --file /absolute/path/to/video.mp4 \
  --content-type video/mp4
```

The static-site Worker serves video from
`/media/talks/<slug>/video.mp4`, with byte-range support. Keep captions in
the repository's static assets so they are committed and baked with the site.

## Preview and validate

`make serve` cannot serve R2 media. For a complete local page with video,
build the site and run the Worker preview:

```bash
make bake
cd workers/static-site
npm exec -- wrangler dev --port 8798
```

Open:

```text
http://127.0.0.1:8798/talks/<slug>/
```

Check that the deck fills its frame, the video plays, captions load, text
readers expand without clipping, and Downloads includes every available
source asset. Then run:

```bash
make check
make static-worker-validate
```
