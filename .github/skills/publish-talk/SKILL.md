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
- Keep the original `slides_url`, `video_url`, or `audio_url` in `talks.yaml`
  for source reference.
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

The talk title will link to the archived copy. Any separate source-material
link remains in the parenthetical links.

## Link a related guide

When a first-party guide is the useful companion to a talk, add its URL as
`guide_url`. Do not add `slug`, local assets, or a Wayback snapshot unless
other talk materials also require them. The talks list labels this link
with the talk title.

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
audio_url: https://podcasts.example.com/episode
audio_download_url: https://cdn.example.com/episode.m4a
local_audio_url: /media/talks/example-talk/audio.mp3
captions_url: /static/talks/example-talk/captions.vtt
poster_url: /media/talks/example-talk/poster.jpg
```

Only add URLs for assets that exist. The Downloads section should use the
same labels as the page: `Slides PDF`, `Recording video`, `Recording audio`,
`Extracted slide text`, and `Timestamped transcript`. A locally hosted audio
recording uses the same folded transcript reader as a video recording and
links to `audio_url` as the original podcast source. When the episode page
and public enclosure differ, record the stable episode page in `audio_url`
and the publicly downloadable enclosure in `audio_download_url`.

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

Upload the approved local video file and optional poster to the private R2 bucket.
Keep the source file's browser-compatible extension in `local_video_url`; the
detail page selects `video/mp4` or `video/webm` from that extension. Upload
the matching content type:

```bash
cd workers/static-site
npm exec -- wrangler r2 object put \
  palewire-talk-media/talks/<slug>/video.webm \
  --remote --file /absolute/path/to/video.webm \
  --content-type video/webm
```

Wrangler only accepts files up to 300 MiB. For a larger recording, use
`boto3`'s multipart upload support with the repository's configured R2
credentials, then verify the stored size and content type:

```bash
uv run --env-file .env python - <<'PY'
import os
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig

path = Path("/absolute/path/to/video.mp4")
bucket = "palewire-talk-media"
key = "talks/<slug>/video.mp4"
client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("R2_ENDPOINT_URL")
    or f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
)
client.upload_file(
    str(path),
    bucket,
    key,
    ExtraArgs={"ContentType": "video/mp4"},
    Config=TransferConfig(
        multipart_threshold=8 * 1024 * 1024,
        multipart_chunksize=16 * 1024 * 1024,
    ),
)
metadata = client.head_object(Bucket=bucket, Key=key)
assert metadata["ContentLength"] == path.stat().st_size
assert metadata["ContentType"] == "video/mp4"
PY
```

The static-site Worker serves media from `/media/talks/<slug>/`, including
`video.mp4`, `video.webm`, `audio.mp3`, and `audio.m4a`, with byte-range
support. Keep captions in the repository's static assets so they are
committed and baked with the site.

For a podcast, run the preservation backup first with an archive root outside
the repository, verify it, then upload the approved MP3 to the talk-media
bucket:

```bash
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-backup
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-verify
cd workers/static-site
npm exec -- wrangler r2 object put \
  palewire-talk-media/talks/<slug>/audio.m4a \
  --remote --file /absolute/path/to/audio.m4a \
  --content-type audio/mp4
```

Do not commit the MP3. Commit `transcript.txt`, `captions.vtt`, and the
readable transcript fragment instead.

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
