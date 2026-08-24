#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
marker_attempts=${WORKER_MARKER_ATTEMPTS:-4}
marker_wait_seconds=${WORKER_MARKER_WAIT_SECONDS:-15}

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

case "$marker_attempts" in
  *[!0-9]*|"")
    echo "WORKER_MARKER_ATTEMPTS must be a positive integer." >&2
    exit 1
    ;;
esac

if [ "$marker_attempts" -eq 0 ]; then
  echo "WORKER_MARKER_ATTEMPTS must be a positive integer." >&2
  exit 1
fi

case "$marker_wait_seconds" in
  *[!0-9]*|"")
    echo "WORKER_MARKER_WAIT_SECONDS must be a non-negative integer." >&2
    exit 1
    ;;
esac

base_url=${base_url%/}
headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-worker-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-worker-body.XXXXXX")

cleanup() {
  rm -f "$headers_file" "$body_file"
}
trap cleanup EXIT HUP INT TERM

diagnose() {
  endpoint=$1
  message=$2
  echo "$endpoint: $message" >&2
  sed -n '1,12p' "$headers_file" >&2
}

verify_endpoint() {
  endpoint=$1
  path=$2
  expected_content_type=$3
  url="${base_url}${path}"

  if ! status=$(curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" --write-out '%{http_code}' "$url"); then
    diagnose "$endpoint" "request failed"
    return 3
  fi

  normalized_headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')
  if [ "$status" != "200" ]; then
    diagnose "$endpoint" "expected HTTP 200, received $status"
    return 1
  fi
  if ! printf '%s\n' "$normalized_headers" | grep -Fqx "content-type: $expected_content_type"; then
    diagnose "$endpoint" "expected Content-Type $expected_content_type"
    return 1
  fi
  if ! printf '%s\n' "$normalized_headers" | grep -Fqx "x-palewire-discovery-proxy: cloudflare-worker-v1"; then
    diagnose "$endpoint" "Worker marker was not found"
    return 2
  fi

  echo "$endpoint: HTTP 200 $expected_content_type"
}

verify_all_endpoints() {
  marker_missing=false
  result=0

  verify_endpoint \
    "webfinger" \
    "/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re" \
    "application/jrd+json; charset=utf-8" || result=$?
  if [ "${result:-0}" -eq 1 ]; then return 1; fi
  if [ "${result:-0}" -eq 3 ]; then return 3; fi
  if [ "${result:-0}" -eq 2 ]; then marker_missing=true; fi
  result=0

  verify_endpoint "host-meta" "/.well-known/host-meta" "application/xrd+xml; charset=utf-8" || result=$?
  if [ "$result" -eq 1 ]; then return 1; fi
  if [ "$result" -eq 3 ]; then return 3; fi
  if [ "$result" -eq 2 ]; then marker_missing=true; fi
  result=0

  verify_endpoint "nodeinfo" "/.well-known/nodeinfo" "application/json; charset=utf-8" || result=$?
  if [ "$result" -eq 1 ]; then return 1; fi
  if [ "$result" -eq 3 ]; then return 3; fi
  if [ "$result" -eq 2 ]; then marker_missing=true; fi

  if [ "$marker_missing" = "true" ]; then
    return 2
  fi
}

attempt=1
while :; do
  if verify_all_endpoints; then
    exit 0
  else
    result=$?
  fi

  if [ "$result" -ne 2 ] && [ "$result" -ne 3 ]; then
    exit 1
  fi
  if [ "$attempt" -ge "$marker_attempts" ]; then
    if [ "$result" -eq 2 ]; then
      echo "Worker marker was not visible after $marker_attempts attempts." >&2
    else
      echo "Worker endpoint request failed after $marker_attempts attempts." >&2
    fi
    exit 1
  fi

  if [ "$result" -eq 2 ]; then
    echo "Worker marker not yet visible; waiting $marker_wait_seconds seconds before retry $((attempt + 1)) of $marker_attempts." >&2
  else
    echo "Worker endpoint request failed; waiting $marker_wait_seconds seconds before retry $((attempt + 1)) of $marker_attempts." >&2
  fi
  if [ "$marker_wait_seconds" -gt 0 ]; then
    sleep "$marker_wait_seconds"
  fi
  attempt=$((attempt + 1))
done
