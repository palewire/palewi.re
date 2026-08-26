---
name: republish-social-posts
description: Create standalone, backdated blog posts from user-nominated LinkedIn or X URLs. Use whenever adapting a social post for coltrane/content/posts/.
---

# Republish nominated social posts

Create a permanent, standalone blog version of a social post the user has
explicitly nominated. The blog post is the record; do not build an aggregation
page or direct readers back to a social platform.

## Intake and source access

- The user supplies one to three exact public LinkedIn or X URLs in a chat
  batch.
- Open only those exact URLs. Do not visit profiles, feeds, search results,
  related posts, or linked pages. Do not crawl or scrape either platform.
- Treat the source URL as private review material. Do not commit it, add it to
  post front matter, or link to it from the published post.
- If the nominated page is unavailable, blocked, or lacks necessary context,
  ask the user to provide the original text. Do not seek it elsewhere.

## Drafting rules

1. Preserve the user's original language as closely as possible. Begin with a
   faithful local transcription, then format it for the blog.
2. Remove emojis from titles and body text. Treat their removal as a mechanical
   formatting change; do not replace them with words unless the user asks.
3. Propose a concise title, a slug, and a publication timestamp based on the
   original social post. Use the original time when it is available and convert
   it to Los Angeles time. If only a date is available, ask the user to choose
   the time.
4. Make only necessary edits for readability or context. Identify every
   substantive addition, omission, or rewrite in the chat review.
5. Do not add source notes, outbound social links, embeds, social-media assets,
   or a provenance field. The finished post must stand on its own.
6. Reuse images only when the user owns them or confirms the right to reuse
   them. Never hotlink platform-hosted media.
7. Resolve shortened URLs found in the nominated post to their canonical
   destinations by following redirects only. Weave each result into the
   surrounding original language as a meaningful inline link. Do not retain
   bare shortened URLs or add a link back to the social post.
8. When the nominated post has lead art, preserve a local copy and use it as
   the blog post's `repr_image`. Access only that directly associated image;
   do not substitute unrelated art.
9. Convert a lead video no longer than 10 seconds into an optimized animated
   GIF and use it as the blog post's `repr_image`. For a longer video, ask the
   user whether to use a still image or omit lead art. Do not hotlink or embed
   a platform-hosted video.
10. If a lead GIF needs visual touch-ups, use a manually or AI-retouched GIF
    supplied by the user from an approved image editor. Do not apply automatic
    background edits that could damage the original artwork.

## Approval and publication

1. Present the title, date, body, and any substantive changes for the user's
   approval before editing repository content.
2. After approval, create an ordinary Markdown post under
   `coltrane/content/posts/`, following nearby posts and the current front
   matter schema. At minimum, use `title`, `slug`, and timezone-aware
   `published_at`.
3. Do not add draft, status, source URL, or unsupported metadata fields.
   Private drafts and nomination records stay in the chat.
4. Run `make check`.
5. Before opening a pull request, reuse a healthy local server or run
   `make serve`, then open the new post on localhost for the user to review.
   Wait for the user's response unless they explicitly waive this preview.
6. Prepare a focused pull request for the approved batch.

## Batch status

Track each item only in the chat as `nominated`, `drafted`, `approved`, or
`published`. Do not create a repository queue, a public checklist, or a
separate tracking system.
