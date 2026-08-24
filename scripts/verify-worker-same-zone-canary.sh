#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
canary_path=/.well-known/cloudflare-worker-canary

case "$base_url" in
  http://*|https://*) ;;
  *)
    echo "BASE_URL must start with http:// or https://." >&2
    exit 1
    ;;
esac

case "$timeout" in
  *[!0-9]*|"")
    echo "CURL_MAX_TIME must be a positive integer." >&2
    exit 1
    ;;
esac

if [ "$timeout" -eq 0 ]; then
  echo "CURL_MAX_TIME must be a positive integer." >&2
  exit 1
fi

base_url=${base_url%/}
headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-worker-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-worker-body.XXXXXX")

cleanup() {
  rm -f "$headers_file" "$body_file"
}
trap cleanup EXIT HUP INT TERM

if ! status=$(curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" --write-out '%{http_code}' "${base_url}${canary_path}"); then
  echo "same-zone canary: request failed" >&2
  sed -n '1,12p' "$headers_file" >&2
  exit 1
fi

normalized_headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')
if [ "$status" != "200" ]; then
  echo "same-zone canary: expected HTTP 200, received $status" >&2
  sed -n '1,12p' "$headers_file" >&2
  exit 1
fi
if ! printf '%s\n' "$normalized_headers" | grep -Fqx "content-type: application/json; charset=utf-8"; then
  echo "same-zone canary: expected NodeInfo Content-Type" >&2
  sed -n '1,12p' "$headers_file" >&2
  exit 1
fi
if ! printf '%s\n' "$normalized_headers" | grep -Fqx "x-palewire-discovery-proxy: cloudflare-worker-v1"; then
  echo "same-zone canary: Worker marker was not found" >&2
  exit 1
fi
if ! grep -Eq '"links"[[:space:]]*:' "$body_file"; then
  echo "same-zone canary: expected NodeInfo links response" >&2
  exit 1
fi

echo "same-zone canary: HTTP 200 application/json; charset=utf-8"
