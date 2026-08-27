---
name: lead-art-screenshot
description: Create consistent browser-framed lead art from a public URL for the top of a palewi.re blog post. Use whenever the user asks to screenshot a webpage for post artwork, make lead art from a URL, or refresh an existing browser-framed post image.
---

# Create browser-framed lead art

Turn a public webpage into a consistent 2000x1250 PNG for a blog post. The
finished image fills the site's 755-pixel desktop post width while remaining
sharp on high-density screens.

## Inputs

The user must provide a public HTTP or HTTPS URL. An output name is optional.

- If the user supplies a filename or post slug, use it.
- Otherwise, derive a short kebab-case filename from the page title.
- Save the finished PNG to `coltrane/static/img/<name>.png`.
- Keep raw captures in the gitignored `.lead-art/` directory; never commit
  them.

Do not capture authenticated, private, personalized, or access-controlled
pages. Do not expose browser profiles, cookies, account names, extensions, or
other real browser chrome in the image.

## Fixed design

Use these values for every capture:

| Item | Value |
|---|---:|
| Finished image | 2000x1250 pixels |
| Page viewport | 2000x1022 pixels |
| Browser frame | 2000x1110 pixels |
| Outer margin | 70 pixels above and below, transparent |
| Device scale | 1 |
| Format | PNG |

The browser frame is deliberately synthetic. It provides a stable neutral
frame without leaking details from the user's real browser. The canvas outside
the browser frame must have real PNG transparency, not a solid background.

## Capture workflow

1. Run the bundled command from the repository root:

   ```bash
   uv run python .github/skills/lead-art-screenshot/capture.py "https://example.com/"
   ```

   To choose the image name:

   ```bash
   uv run python .github/skills/lead-art-screenshot/capture.py \
     "https://example.com/" \
     --output post-slug
   ```

   The helper uses the pinned Chrome DevTools CLI through `npx`. It keeps a
   reusable headless Chrome instance across commands and does not open a visible
   browser window. On first use, `npx` may download the pinned package.

2. Inspect the finished image. Repeat the capture if the page is obscured by an
   error, loading state, consent panel, modal, or broken asset. Do not produce
   misleading or incomplete artwork.
3. Report the final path and include this ready-to-paste post markup:

    ```html
    <img src="/static/img/<name>.png" alt="<plain description of the visible page>">
    ```

The helper navigates only to the supplied URL and the bundled local frame. It
freezes animation, returns to the top of the page, verifies the final dimensions,
removes the raw capture, and closes its temporary tab.

If the page cannot be captured cleanly, delete the finished image and explain
what blocked it.
