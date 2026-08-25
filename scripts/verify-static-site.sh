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

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-static-site-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-static-site-body.XXXXXX")
cleanup() {
  rm -f "$headers_file" "$body_file"
}
trap cleanup EXIT HUP INT TERM

request() {
  path=$1
  expected_status=$2
  curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" "${base_url%/}${path}"
  status=$(awk '/^HTTP\// { code=$2 } END { print code }' "$headers_file")
  test "$status" = "$expected_status" || {
    echo "$path: expected HTTP $expected_status, received $status." >&2
    exit 1
  }
}

request "/health/" 200
grep -Fq '{"status":"ok"}' "$body_file"
request "/who-is-ben-welsh/" 200
grep -Fq '<link rel="canonical" href="https://palewi.re/who-is-ben-welsh/"' "$body_file"
request "/posts/" 200
request "/sitemap.xml" 200
grep -Fq '<sitemapindex' "$body_file"
request "/robots.txt" 200
request "/this-page-does-not-exist/" 404
grep -Fq 'id="error-heading">404<' "$body_file"
request "/feeds/posts/" 200
grep -Fiq 'content-type: application/rss+xml; charset=utf-8' "$headers_file"
request "/" 302
grep -Fiq 'location: /who-is-ben-welsh/' "$headers_file"
request "/favicon.ico" 302
grep -Fiq 'location: /static/favicon.ico' "$headers_file"
request "/@palewire" 302
grep -Fiq 'location: https://mastodon.palewi.re/@palewire' "$headers_file"

echo "static site verification passed"
