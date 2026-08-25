# Private R2 media archive replica

`palewire-media-archive` is a private, Standard-class R2 bucket for an
offsite copy of the existing external media archive. It is not a public media
host, a Worker binding, or a replacement for the local archive. Keep the
media, `manifest.json`, and extractor sidecars outside this repository.

## Credentials

Use the Cloudflare dashboard: **R2 Object Storage** > **Manage** > **API
Tokens**. Create an R2 S3-compatible API token with **Object Read and Write**,
scoped only to `palewire-media-archive`. Store its Access Key ID and Secret
Access Key in a shell environment or private configuration outside Git. In a
Bash session, enter the values interactively so they are never saved in shell
history:

```sh
read -r -p "R2 account ID: " R2_ACCOUNT_ID
read -r -s -p "R2 access key ID: " R2_ACCESS_KEY_ID; printf "\n"
read -r -s -p "R2 secret access key: " R2_SECRET_ACCESS_KEY; printf "\n"
export R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY
```

Never add these values to Git, `.env`, shell history, or command arguments.
The CLI uses `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com` and region
`auto`. Set `R2_ENDPOINT_URL` only when a jurisdiction-specific endpoint is
needed.

## Sync and verify

First run the existing offline check. It protects the local source before any
transfer:

```sh
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-verify
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-r2-sync
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-r2-verify
```

The sync uploads each successful media file, its yt-dlp `.info.json` sidecar
when present, `manifest.json`, and a generated `checksums.sha256` listing.
Each R2 object receives its SHA-256 in private object metadata. A later sync
uses the object size and that metadata to skip byte-identical files, so an
interrupted pass resumes safely without re-uploading verified objects.

Remote verification uses `HeadObject` requests only. It reports every missing
or mismatched object but does not retrieve media, which avoids unnecessary
retrieval and transfer. Run it after each sync and periodically thereafter.

## Recovery

To restore one media file recorded in the local manifest, use its
`output_filename` and an external destination:

```sh
ARCHIVE_ROOT=/absolute/path/outside/the/repo \
OUTPUT_FILENAME=direct/example.mp4 \
DESTINATION=/absolute/path/outside/the/repo/recovered/example.mp4 \
make media-archive-r2-recover
```

The command refuses repository destinations, will not replace an existing
file without an explicit CLI `--force`, and hashes the downloaded file before
keeping it. A checksum failure leaves no partial restored file.

## Cost-aware operation

Sync only after a successful local backup or checksum check. The normal
remote verification is metadata-only; avoid bulk downloads and full remote
rehashes. R2 Standard storage has no minimum duration, while Infrequent
Access has a 30-day minimum and retrieval fees, so Standard remains the
default for this preservation copy until actual access patterns justify a
change. Review current pricing before changing storage class or running large
replication batches.

## Deferred bucket lock

Do not enable a bucket lock until the first real replica and recovery drill
are complete. The proposed policy is one R2 bucket-lock rule with no prefix,
named `media-archive-retain-30d`, using the `Age` condition with
`maxAgeSeconds: 2592000` (30 days). It applies to the entire bucket, including
existing and future media, manifests, metadata, and checksum files, preventing
deletion and overwriting during the retention window.

Cloudflare allows bucket-lock rules to be removed, but a bucket cannot be
emptied while any rule exists. Do not enable this policy until a maintainer
explicitly approves the 30-day window after the pilot and recovery drill. The
current pinned Wrangler command that would apply it is:

```sh
wrangler r2 bucket lock add palewire-media-archive media-archive-retain-30d "" --retention-days 30
```
