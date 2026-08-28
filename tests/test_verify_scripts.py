"""Tests for production verification shell scripts."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _write_executable(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def test_legacy_canary_retries_during_route_propagation(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    count_path = tmp_path / "curl-count"
    _write_executable(
        bin_dir / "curl",
        """#!/bin/sh
headers_file=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dump-header) headers_file=$2; shift 2 ;;
    *) shift ;;
  esac
done
count=0
test ! -f "$FAKE_CURL_COUNT" || count=$(cat "$FAKE_CURL_COUNT")
count=$((count + 1))
printf '%s' "$count" > "$FAKE_CURL_COUNT"
if [ "$count" -eq 1 ]; then
  printf 'HTTP/2 404\\r\\n\\r\\n' > "$headers_file"
  printf '404'
else
  printf 'HTTP/2 204\\r\\nx-palewire-legacy-redirect: cloudflare-worker-v1\\r\\n\\r\\n' > "$headers_file"
  printf '204'
fi
""",
    )
    _write_executable(bin_dir / "sleep", "#!/bin/sh\nexit 0\n")
    env = {
        **os.environ,
        "FAKE_CURL_COUNT": str(count_path),
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "WORKER_MARKER_ATTEMPTS": "2",
        "WORKER_MARKER_WAIT_SECONDS": "0",
    }

    result = subprocess.run(
        ["sh", str(ROOT / "scripts" / "verify-legacy-redirect-canary.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert count_path.read_text(encoding="utf-8") == "2"
    assert "waiting 0 seconds before retry 2 of 2" in result.stderr
    assert "same-zone legacy redirect canary: HTTP 204" in result.stdout


def test_static_site_retries_during_asset_propagation(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    count_path = tmp_path / "curl-count"
    _write_executable(
        bin_dir / "curl",
        """#!/bin/sh
headers_file=
body_file=
url=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dump-header) headers_file=$2; shift 2 ;;
    --output) body_file=$2; shift 2 ;;
    *) url=$1; shift ;;
  esac
done
count=0
test ! -f "$FAKE_CURL_COUNT" || count=$(cat "$FAKE_CURL_COUNT")
count=$((count + 1))
printf '%s' "$count" > "$FAKE_CURL_COUNT"
status=200
location=
test "$count" -ne 1 || status=404
case "$url" in
  */posts/2010/03/10/google-charts-takes-tufte-challenge/) status=404 ;;
  */this-page-does-not-exist/) status=404 ;;
  https://palewi.re/) status=302; location=/who-is-ben-welsh/ ;;
  https://palewi.re/favicon.ico) status=302; location=/static/favicon.ico ;;
  https://palewi.re/@palewire) status=302; location=https://mastodon.palewi.re/@palewire ;;
esac
printf "HTTP/2 %s\\ncontent-type: application/rss+xml; charset=utf-8\\ncontent-security-policy: base-uri 'self'; frame-src 'self' https://datawrapper.dwcdn.net https://docs.google.com https://player.vimeo.com http://s3-us-west-1.amazonaws.com https://w.soundcloud.com\\npermissions-policy: camera=(), geolocation=(), microphone=(), payment=(), usb=()\\n" "$status" > "$headers_file"
test -z "$location" || printf "location: %s\\n" "$location" >> "$headers_file"
printf "\\n" >> "$headers_file"
cat > "$body_file" <<'EOF'
{"status":"ok"}
<link rel="canonical" href="https://palewi.re/who-is-ben-welsh/" />
<iframe src="https://docs.google.com/"></iframe>
<iframe src="http://s3-us-west-1.amazonaws.com/"></iframe>
<iframe src="https://player.vimeo.com/"></iframe>
<iframe src="https://w.soundcloud.com/"></iframe>
<iframe src="https://datawrapper.dwcdn.net/6T1Lq/4/"></iframe>
<iframe src="http://chart.apis.google.com/"></iframe>
<iframe src="http://www.palewire.com/"></iframe>
<img src="//palewire.s3.amazonaws.com/latimes-tour/1.jpg">
<video src="//palewire.s3.amazonaws.com/latimes-tour/9track.mp4"></video>
<sitemapindex></sitemapindex>
<h1 id="error-heading">404</h1>
EOF
exit 0
""",
    )
    _write_executable(bin_dir / "sleep", "#!/bin/sh\nexit 0\n")
    env = {
        **os.environ,
        "FAKE_CURL_COUNT": str(count_path),
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "SITE_VERIFY_ATTEMPTS": "2",
        "SITE_VERIFY_WAIT_SECONDS": "0",
    }

    result = subprocess.run(
        ["sh", str(ROOT / "scripts" / "verify-static-site.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "while deployment propagates; waiting 0 seconds before retry 2 of 2" in result.stderr


def test_production_verifiers_cover_new_navigation() -> None:
    static_verifier = (ROOT / "scripts" / "verify-static-site.sh").read_text(encoding="utf-8")
    redirect_verifier = (ROOT / "scripts" / "verify-legacy-redirects.sh").read_text(encoding="utf-8")

    for path in ("/apps/", "/clips/", "/code/", "/guides/"):
        assert f'request "{path}" 200' in static_verifier
        assert f'"{path}:200"' in redirect_verifier
    assert 'request "/posts/2010/03/10/google-charts-takes-tufte-challenge/" 404' in static_verifier
    assert 'request "/work/"' not in static_verifier
    assert '"/work/:200"' not in redirect_verifier
