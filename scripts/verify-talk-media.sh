#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
case "$base_url" in http://*|https://*) ;; *) echo "BASE_URL must start with http:// or https://." >&2; exit 1 ;; esac
case "$timeout" in *[!0-9]*|"") echo "CURL_MAX_TIME must be a positive integer." >&2; exit 1 ;; esac
test "$timeout" -gt 0 || { echo "CURL_MAX_TIME must be positive." >&2; exit 1; }
headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-media-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-media-body.XXXXXX")
trap 'rm -f "$headers_file" "$body_file"' EXIT HUP INT TERM

for path in \
  /media/talks/reuters-climate-monitor/video.mp4 \
  /media/talks/local-data-journalism-podcast/audio.m4a
do
  status=$(curl --silent --show-error --max-time "$timeout" --max-filesize 32 \
    --range 0-31 --dump-header "$headers_file" --output "$body_file" \
    --write-out '%{http_code}' "${base_url%/}${path}")
  range=$(awk 'tolower($1) == "content-range:" { sub(/\r$/, ""); print substr($0, 16); exit }' "$headers_file")
  size=$(wc -c < "$body_file" | tr -d ' ')
  if [ "$status" != "206" ] || [ "$size" != "32" ] || \
    ! printf '%s\n' "$range" | grep -Eq '^bytes 0-31/[0-9]+$'; then
    echo "$path: expected 32 bytes and valid Content-Range; received HTTP $status, $size bytes, $range." >&2
    exit 1
  fi
  echo "$path: HTTP 206, 32 bytes, $range"
done

echo "talk media verification passed"
