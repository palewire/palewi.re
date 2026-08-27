from __future__ import annotations

import ipaddress
import json
import re
import shutil
import struct
import subprocess
import unicodedata
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import click

REPO_ROOT = Path(__file__).resolve().parents[3]
FRAME_PATH = Path(__file__).with_name("frame.html")
WORK_DIR = REPO_ROOT / ".lead-art"
IMAGE_DIR = REPO_ROOT / "coltrane" / "static" / "img"
CHROME_DEVTOOLS_VERSION = "1.8.0"
SOURCE_VIEWPORT = "2000x1022x1"
OUTPUT_VIEWPORT = "2000x1250x1"
OUTPUT_SIZE = (2000, 1250)
FRAME_BOUNDS = (0, 70, 2000, 1180)
FRAME_RADIUS = 24


class ChromeDevTools:
    def __init__(self) -> None:
        self.command = [
            "npx",
            "--yes",
            "--package",
            f"chrome-devtools-mcp@{CHROME_DEVTOOLS_VERSION}",
            "chrome-devtools",
        ]

    def _run(self, *args: str) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [*self.command, *args, "--output-format=json"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            details = exc.stderr.strip() or exc.stdout.strip() or "No details returned."
            raise click.ClickException(f"Chrome command failed: {details}") from exc
        try:
            data: object = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise click.ClickException(f"Chrome returned an invalid response: {result.stdout.strip()}") from exc
        if not isinstance(data, dict):
            raise click.ClickException(f"Chrome returned an unexpected response: {data!r}")
        return data

    def open_page(self) -> int:
        data = self._run("new_page", "about:blank", "--background", "--timeout", "30000")
        selected_pages = [page for page in data.get("pages", []) if page.get("selected")]
        if not selected_pages:
            raise click.ClickException("Chrome did not report the new page.")
        return int(selected_pages[-1]["id"])

    def emulate(self, page_id: int, viewport: str) -> None:
        self._run("emulate", str(page_id), "--viewport", viewport, "--colorScheme", "light")

    def navigate(self, page_id: int, url: str) -> None:
        self._run(
            "navigate_page",
            str(page_id),
            "--type",
            "url",
            "--url",
            url,
            "--timeout",
            "30000",
        )

    def prepare_source(self, page_id: int) -> None:
        script = """
        async () => {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          window.scrollTo(0, 0);
          const style = document.createElement("style");
          style.textContent = `
            html { scrollbar-width: none !important; }
            html::-webkit-scrollbar { display: none !important; }
            *, *::before, *::after {
              animation-duration: 0s !important;
              animation-delay: 0s !important;
              transition-duration: 0s !important;
            }
          `;
          document.head.appendChild(style);
          return document.title;
        }
        """
        self._run("evaluate_script", script, "--pageId", str(page_id), "--waitForStableDom", "false")

    def page_title(self, page_id: int) -> str:
        data = self._run("list_pages")
        for page in data.get("pages", []):
            if int(page["id"]) == page_id:
                return str(page.get("title", "")).strip()
        raise click.ClickException("Chrome lost track of the source page.")

    def wait_for_frame(self, page_id: int) -> None:
        script = """
        async () => {
          for (let attempt = 0; attempt < 50; attempt += 1) {
            if (document.title === "Ready") return true;
            if (document.title === "Image failed to load") {
              throw new Error("The raw screenshot failed to load.");
            }
            await new Promise((resolve) => setTimeout(resolve, 100));
          }
          throw new Error("The browser frame did not finish loading.");
        }
        """
        self._run("evaluate_script", script, "--pageId", str(page_id), "--waitForStableDom", "false")

    def screenshot(self, page_id: int, destination: Path) -> None:
        data = self._run("take_screenshot", str(page_id), "--format", "png")
        images = data.get("images", [])
        if not images:
            raise click.ClickException("Chrome did not return a screenshot.")
        source = Path(str(images[0]["filePath"]))
        if not source.is_file():
            raise click.ClickException(f"Chrome screenshot is missing: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    def close_page(self, page_id: int) -> None:
        self._run("close_page", str(page_id))


def validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise click.BadParameter("Use a complete public HTTP or HTTPS URL.", param_hint="URL")
    if parsed.username or parsed.password:
        raise click.BadParameter("The URL must not contain credentials.", param_hint="URL")

    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        raise click.BadParameter("The URL must be public.", param_hint="URL")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise click.BadParameter("The URL must use a public IP address.", param_hint="URL")

    return value


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")[:80]


def output_name(value: str | None, title: str, source_url: str) -> str:
    if value:
        candidate = Path(value)
        if candidate.parent != Path(".") or candidate.suffix not in {"", ".png"}:
            raise click.BadParameter("Use a filename or slug, not a path.", param_hint="--output")
        name = slugify(candidate.stem)
    else:
        parsed = urlparse(source_url)
        fallback = f"{parsed.hostname or ''}-{parsed.path.strip('/').replace('/', '-')}"
        name = slugify(title) or slugify(fallback)

    if not name:
        raise click.ClickException("Could not derive an output filename. Pass --output.")
    return name


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise click.ClickException(f"Chrome did not create a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def add_transparent_margin(path: Path) -> None:
    data = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise click.ClickException(f"Chrome did not create a valid PNG: {path}")

    chunks: list[tuple[bytes, bytes]] = []
    position = len(signature)
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        chunk_data = data[position + 8 : position + 8 + length]
        chunks.append((chunk_type, chunk_data))
        position += 12 + length

    ihdr = next((chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IHDR"), None)
    if ihdr is None:
        raise click.ClickException(f"Chrome did not create a valid PNG: {path}")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr)
    if (width, height, bit_depth, color_type, compression, filtering, interlace) != (
        *OUTPUT_SIZE,
        8,
        2,
        0,
        0,
        0,
    ):
        raise click.ClickException("Chrome created an unsupported PNG for transparent lead art.")

    compressed = b"".join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IDAT")
    source = zlib.decompress(compressed)
    row_length = width * 3
    rows: list[bytearray] = []
    cursor = 0
    previous = bytearray(row_length)
    for _ in range(height):
        filter_type = source[cursor]
        cursor += 1
        row = bytearray(source[cursor : cursor + row_length])
        cursor += row_length
        for index, value in enumerate(row):
            left = row[index - 3] if index >= 3 else 0
            above = previous[index]
            upper_left = previous[index - 3] if index >= 3 else 0
            if filter_type == 1:
                row[index] = (value + left) & 0xFF
            elif filter_type == 2:
                row[index] = (value + above) & 0xFF
            elif filter_type == 3:
                row[index] = (value + ((left + above) // 2)) & 0xFF
            elif filter_type == 4:
                prediction = left + above - upper_left
                distances = (abs(prediction - left), abs(prediction - above), abs(prediction - upper_left))
                row[index] = (value + (left, above, upper_left)[distances.index(min(distances))]) & 0xFF
            elif filter_type != 0:
                raise click.ClickException("Chrome created an unsupported PNG filter for transparent lead art.")
        rows.append(row)
        previous = row

    left, top, right, bottom = FRAME_BOUNDS
    output = bytearray()
    for y, row in enumerate(rows):
        output.append(0)
        for x in range(width):
            in_frame = left <= x < right and top <= y < bottom
            if in_frame:
                corner_x = min(x - left, right - 1 - x)
                corner_y = min(y - top, bottom - 1 - y)
                if corner_x < FRAME_RADIUS and corner_y < FRAME_RADIUS:
                    in_frame = (corner_x - FRAME_RADIUS + 1) ** 2 + (
                        corner_y - FRAME_RADIUS + 1
                    ) ** 2 <= FRAME_RADIUS**2
            offset = x * 3
            output.extend((*row[offset : offset + 3], 255 if in_frame else 0))

    def chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
        return (
            struct.pack(">I", len(chunk_data))
            + chunk_type
            + chunk_data
            + struct.pack(">I", zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
        )

    rgba_header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        signature + chunk(b"IHDR", rgba_header) + chunk(b"IDAT", zlib.compress(output)) + chunk(b"IEND", b"")
    )


@click.command()
@click.argument("url")
@click.option("--output", help="Output filename or post slug. Defaults to the page title.")
def main(url: str, output: str | None) -> None:
    """Create browser-framed lead art from URL."""
    source_url = validate_url(url)
    browser = ChromeDevTools()
    page_id = browser.open_page()
    raw_path: Path | None = None

    try:
        browser.emulate(page_id, SOURCE_VIEWPORT)
        browser.navigate(page_id, source_url)
        browser.prepare_source(page_id)

        name = output_name(output, browser.page_title(page_id), source_url)
        raw_path = WORK_DIR / "source.png"
        final_path = IMAGE_DIR / f"{name}.png"
        browser.screenshot(page_id, raw_path)

        frame_url = f"{FRAME_PATH.as_uri()}?{urlencode({'url': source_url})}"
        browser.navigate(page_id, frame_url)
        browser.emulate(page_id, OUTPUT_VIEWPORT)
        browser.wait_for_frame(page_id)
        browser.screenshot(page_id, final_path)
        add_transparent_margin(final_path)

        actual_size = png_size(final_path)
        if actual_size != OUTPUT_SIZE:
            final_path.unlink(missing_ok=True)
            raise click.ClickException(
                f"Expected a 2000x1250 PNG, but Chrome created {actual_size[0]}x{actual_size[1]}."
            )

        click.echo(final_path.relative_to(REPO_ROOT))
    finally:
        if raw_path is not None:
            raw_path.unlink(missing_ok=True)
        browser.close_page(page_id)


if __name__ == "__main__":
    main()
