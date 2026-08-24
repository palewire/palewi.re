#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
marker_attempts=${WORKER_MARKER_ATTEMPTS:-4}
marker_wait_seconds=${WORKER_MARKER_WAIT_SECONDS:-15}

case "$base_url" in
  http://*|https://*) ;;
  *) echo "BASE_URL must start with http:// or https://." >&2; exit 1 ;;
esac
case "$timeout:$marker_attempts:$marker_wait_seconds" in
  *[!0-9:]*|*::*) echo "CURL_MAX_TIME, WORKER_MARKER_ATTEMPTS, and WORKER_MARKER_WAIT_SECONDS must be integers." >&2; exit 1 ;;
esac
if [ "$timeout" -eq 0 ] || [ "$marker_attempts" -eq 0 ]; then
  echo "CURL_MAX_TIME and WORKER_MARKER_ATTEMPTS must be positive." >&2
  exit 1
fi

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-legacy-redirect-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-legacy-redirect-body.XXXXXX")
cleanup() {
  rm -f "$headers_file" "$body_file"
}
trap cleanup EXIT HUP INT TERM

verify_redirect() {
  source_path=$1
  expected_location=$2
  status=$(curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" --write-out '%{http_code}' "${base_url%/}${source_path}") || return 1
  headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')
  location=$(awk 'tolower($1) == "location:" { sub(/\r$/, ""); print substr($0, 11); exit }' "$headers_file")
  if [ "$status" != "302" ] || [ "$location" != "$expected_location" ]; then
    echo "$source_path: expected 302 Location $expected_location, received $status $location" >&2
    return 1
  fi
  if ! printf '%s\n' "$headers" | grep -Fqx "x-palewire-legacy-redirect: cloudflare-worker-v1"; then
    return 2
  fi
}

verify_all() {
  python_output=$(UV_NO_ENV_FILE=1 uv run python -m project.redirect_manifest --production-cases)
  tab=$(printf '\t')
  printf '%s\n' "$python_output" | while IFS="$tab" read -r source_path expected_location; do
    verify_redirect "$source_path" "$expected_location" || exit $?
  done
}

verify_untouched() {
  for path in /who-is-ben-welsh/ /health/ /posts/2026/08/24/current-post/; do
    curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" "${base_url%/}${path}" >/dev/null || return 1
    headers=$(tr '[:upper:]' '[:lower:]' < "$headers_file" | tr -d '\r')
    if printf '%s\n' "$headers" | grep -Fq "x-palewire-legacy-redirect:"; then
      echo "$path: an adjacent non-legacy path was intercepted." >&2
      return 1
    fi
  done
}

attempt=1
while :; do
  if verify_all; then
    break
  fi
  result=$?
  if [ "$result" -ne 2 ] || [ "$attempt" -ge "$marker_attempts" ]; then
    echo "legacy redirect verification failed." >&2
    exit 1
  fi
  echo "legacy redirect marker not yet visible; waiting $marker_wait_seconds seconds before retry $((attempt + 1)) of $marker_attempts." >&2
  sleep "$marker_wait_seconds"
  attempt=$((attempt + 1))
done

verify_untouched
echo "legacy redirect production verification passed"
