#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
attempts=${WORKER_MARKER_ATTEMPTS:-4}
wait_seconds=${WORKER_MARKER_WAIT_SECONDS:-15}

case "$base_url" in
  http://*|https://*) ;;
  *) echo "BASE_URL must start with http:// or https://." >&2; exit 1 ;;
esac
case "$timeout:$attempts:$wait_seconds" in
  *[!0-9:]*|*::*) echo "CURL_MAX_TIME, WORKER_MARKER_ATTEMPTS, and WORKER_MARKER_WAIT_SECONDS must be integers." >&2; exit 1 ;;
esac
if [ "$timeout" -eq 0 ] || [ "$attempts" -eq 0 ]; then
  echo "CURL_MAX_TIME and WORKER_MARKER_ATTEMPTS must be positive." >&2
  exit 1
fi

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-legacy-canary-headers.XXXXXX")
cleanup() {
  rm -f "$headers_file"
}
trap cleanup EXIT HUP INT TERM

attempt=1
while :; do
  status=$(curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output /dev/null --write-out '%{http_code}' "${base_url%/}/legacy-redirects-canary")
  headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')
  if [ "$status" = "204" ] &&
    printf '%s\n' "$headers" | grep -Fqx "x-palewire-legacy-redirect: cloudflare-worker-v1"; then
    break
  fi
  if [ "$attempt" -ge "$attempts" ]; then
    echo "same-zone legacy redirect canary did not return its marker." >&2
    sed -n '1,12p' "$headers_file" >&2
    exit 1
  fi
  echo "same-zone legacy redirect canary not yet visible; waiting $wait_seconds seconds before retry $((attempt + 1)) of $attempts." >&2
  sleep "$wait_seconds"
  attempt=$((attempt + 1))
done

echo "same-zone legacy redirect canary: HTTP 204"
