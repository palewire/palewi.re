#!/bin/sh

set -eu

timeout=${CURL_MAX_TIME:-20}
legacy_hosts=${LEGACY_HOSTS:-"palewire.com www.palewire.com"}

case "$timeout" in
  *[!0-9]*|"") echo "CURL_MAX_TIME must be a positive integer." >&2; exit 1 ;;
esac
if [ "$timeout" -eq 0 ]; then
  echo "CURL_MAX_TIME must be a positive integer." >&2
  exit 1
fi

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-legacy-domain-headers.XXXXXX")
cleanup() {
  rm -f "$headers_file"
}
trap cleanup EXIT HUP INT TERM

verify_redirect() {
  host=$1
  path=$2
  expected_location=$3
  status=$(curl --silent --show-error --max-time "$timeout" \
    --dump-header "$headers_file" --output /dev/null --write-out '%{http_code}' \
    "https://${host}${path}") || {
    echo "${host}${path}: request failed." >&2
    return 1
  }
  location=$(awk 'tolower($1) == "location:" { sub(/\r$/, ""); print substr($0, 11); exit }' "$headers_file")
  if [ "$status" != "301" ] || [ "$location" != "$expected_location" ]; then
    echo "${host}${path}: expected HTTP 301 Location ${expected_location}, received ${status} ${location}." >&2
    return 1
  fi
  echo "${host}${path}: HTTP 301 ${location}"
}

for host in $legacy_hosts; do
  case "$host" in
    *[!A-Za-z0-9.-]*|"") echo "LEGACY_HOSTS contains an invalid host." >&2; exit 1 ;;
  esac
  verify_redirect "$host" "/" "https://palewi.re/"
  verify_redirect "$host" "/who-is-ben-welsh/" "https://palewi.re/who-is-ben-welsh/"
done

echo "legacy domain verification passed"
