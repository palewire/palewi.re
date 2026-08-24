#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}

case "$base_url" in
  http://*|https://*) ;;
  *) echo "BASE_URL must start with http:// or https://." >&2; exit 1 ;;
esac
case "$timeout" in
  *[!0-9]*|"") echo "CURL_MAX_TIME must be a positive integer." >&2; exit 1 ;;
esac

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-legacy-canary-headers.XXXXXX")
cleanup() {
  rm -f "$headers_file"
}
trap cleanup EXIT HUP INT TERM

status=$(curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output /dev/null --write-out '%{http_code}' "${base_url%/}/legacy-redirects-canary")
headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')

if [ "$status" != "204" ] || ! printf '%s\n' "$headers" | grep -Fqx "x-palewire-legacy-redirect: cloudflare-worker-v1"; then
  echo "same-zone legacy redirect canary did not return its marker." >&2
  sed -n '1,12p' "$headers_file" >&2
  exit 1
fi

echo "same-zone legacy redirect canary: HTTP 204"
