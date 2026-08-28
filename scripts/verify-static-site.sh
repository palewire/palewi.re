#!/bin/sh

set -eu

base_url=${BASE_URL:-https://palewi.re}
timeout=${CURL_MAX_TIME:-20}
attempts=${SITE_VERIFY_ATTEMPTS:-5}
wait_seconds=${SITE_VERIFY_WAIT_SECONDS:-15}

case "$base_url" in
  http://*|https://*) ;;
  *) echo "BASE_URL must start with http:// or https://." >&2; exit 1 ;;
esac
case "$timeout:$attempts:$wait_seconds" in
  *[!0-9:]*|*::*) echo "CURL_MAX_TIME, SITE_VERIFY_ATTEMPTS, and SITE_VERIFY_WAIT_SECONDS must be integers." >&2; exit 1 ;;
esac
if [ "$timeout" -eq 0 ] || [ "$attempts" -eq 0 ]; then
  echo "CURL_MAX_TIME and SITE_VERIFY_ATTEMPTS must be positive." >&2
  exit 1
fi

headers_file=$(mktemp "${TMPDIR:-/tmp}/palewire-static-site-headers.XXXXXX")
body_file=$(mktemp "${TMPDIR:-/tmp}/palewire-static-site-body.XXXXXX")
cleanup() {
  rm -f "$headers_file" "$body_file"
}
trap cleanup EXIT HUP INT TERM

request() {
  path=$1
  expected_status=$2
  attempt=1
  while :; do
    : > "$headers_file"
    : > "$body_file"
    if curl --silent --show-error --max-time "$timeout" --dump-header "$headers_file" --output "$body_file" "${base_url%/}${path}"; then
      status=$(awk '/^HTTP\// { code=$2 } END { print code }' "$headers_file")
    else
      status=000
    fi
    if [ "$status" = "$expected_status" ]; then
      break
    fi
    if [ "$attempt" -ge "$attempts" ]; then
      echo "$path: expected HTTP $expected_status, received $status." >&2
      exit 1
    fi
    echo "$path: received HTTP $status while deployment propagates; waiting $wait_seconds seconds before retry $((attempt + 1)) of $attempts." >&2
    sleep "$wait_seconds"
    attempt=$((attempt + 1))
  done
}

expect_security_headers() {
  grep -Fiq "content-security-policy: " "$headers_file"
  grep -Fiq "frame-src 'self' https://datawrapper.dwcdn.net https://docs.google.com https://player.vimeo.com http://s3-us-west-1.amazonaws.com https://w.soundcloud.com" "$headers_file"
  grep -Fiq "permissions-policy: camera=(), geolocation=(), microphone=(), payment=(), usb=()" "$headers_file"
}

request "/health/" 200
grep -Fq '{"status":"ok"}' "$body_file"
expect_security_headers
request "/who-is-ben-welsh/" 200
grep -Fq '<link rel="canonical" href="https://palewi.re/who-is-ben-welsh/"' "$body_file"
expect_security_headers
request "/posts/" 200
request "/clips/" 200
request "/apps/" 200
request "/code/" 200
request "/guides/" 200
request "/talks/" 200
request "/docs/" 200
request "/posts/2012/02/25/nicar-2012-things-i-said/" 200
grep -Fq 'src="https://docs.google.com/' "$body_file"
request "/posts/2012/03/26/leaflet-recipe-hover-events-features-and-polygons/" 200
grep -Fq 'src="http://s3-us-west-1.amazonaws.com/' "$body_file"
request "/posts/2017/09/09/what-i-learned/" 200
grep -Fq 'src="https://player.vimeo.com/' "$body_file"
request "/posts/2025/05/21/ire-podcast-transcript/" 200
grep -Fq 'src="https://w.soundcloud.com/' "$body_file"
request "/posts/2026/01/27/how-journalism-lost-its-culture-of-sharing/" 200
grep -Fq 'src="https://datawrapper.dwcdn.net/6T1Lq/4/"' "$body_file"
request "/posts/2010/03/10/google-charts-takes-tufte-challenge/" 404
request "/posts/2008/07/06/permalinks-low-rent-data-viz-and-other-stupid-caspio-tricks/" 200
grep -Fq 'src="http://www.palewire.com/' "$body_file"
request "/posts/2018/04/14/my-times/" 200
grep -Fq 'src="//palewire.s3.amazonaws.com/latimes-tour/1.jpg"' "$body_file"
grep -Fq 'src="//palewire.s3.amazonaws.com/latimes-tour/9track.mp4"' "$body_file"
request "/sitemap.xml" 200
grep -Fq '<sitemapindex' "$body_file"
request "/robots.txt" 200
request "/this-page-does-not-exist/" 404
grep -Fq 'id="error-heading">404<' "$body_file"
request "/feeds/posts/" 200
grep -Fiq 'content-type: application/rss+xml; charset=utf-8' "$headers_file"
request "/static/styles.css" 200
test -s "$body_file"
request "/static/favicon.ico" 200
test -s "$body_file"
request "/" 302
grep -Fiq 'location: /who-is-ben-welsh/' "$headers_file"
request "/favicon.ico" 302
grep -Fiq 'location: /static/favicon.ico' "$headers_file"
request "/@palewire" 302
grep -Fiq 'location: https://mastodon.palewi.re/@palewire' "$headers_file"

echo "static site verification passed"
