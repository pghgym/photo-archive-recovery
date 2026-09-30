"""
browser_capture_recovery.py

Recovers full-resolution photos from a platform that serves images only
through authenticated, dynamically-loaded network requests -- a case where
simple URL scraping (see extract_urls_from_raw_text.py) doesn't work because
the image URLs aren't exposed until the user is logged in and actively
browsing albums.

Approach: launch a real (visible) browser session, let the user log in and
navigate manually, and listen to every network response in the background.
Any response that looks like a genuine photo asset (by content-type and a
minimum size threshold, to filter out thumbnails/icons/UI graphics) gets
saved automatically.

Usage:
    python browser_capture_recovery.py --url https://example-photo-site.com/login --out ./recovered_images
"""

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

MIN_ASSET_SIZE_BYTES = 50_000  # filters out thumbnails/icons, keeps full-res photos
ASSET_URL_HINTS = ("photo", "image", "img", "cloudfront")  # generalize per target site


def safe_filename(url: str, content_type: str = "") -> str:
    path = urlparse(url).path
    name = Path(path).name or "image"
    if "." not in name:
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", name) + ext
    return name


def run_capture(start_url: str, output_dir: Path, url_hints=ASSET_URL_HINTS,
                 min_size=MIN_ASSET_SIZE_BYTES, headless: bool = False):
    output_dir.mkdir(parents=True, exist_ok=True)
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        def handle_response(response):
            try:
                url = response.url
                content_type = (response.headers.get("content-type") or "").lower()

                looks_like_image = content_type.startswith("image/") or any(
                    ext in url.lower() for ext in (".jpg", ".jpeg", ".png", ".webp")
                )
                looks_like_target_asset = any(hint in url.lower() for hint in url_hints)

                if not (looks_like_image and looks_like_target_asset):
                    return
                if url in seen_urls:
                    return

                body = response.body()
                if len(body) < min_size:
                    return  # likely a thumbnail or UI icon, not the full photo

                seen_urls.add(url)
                filename = safe_filename(url, content_type)
                out_path = output_dir / filename

                counter = 1
                while out_path.exists():
                    out_path = output_dir / f"{out_path.stem}_{counter}{out_path.suffix}"
                    counter += 1

                out_path.write_bytes(body)
                print(f"Saved: {out_path.name} ({len(body)} bytes)")
            except Exception:
                pass  # network responses can close/error mid-capture; safe to skip

        page.on("response", handle_response)
        page.goto(start_url)

        input("Log in, open albums, and browse photos, then press Enter here to finish...")
        browser.close()

    print(f"\nCapture complete. Saved {len(seen_urls)} assets to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recover photos via live browser network capture.")
    parser.add_argument("--url", required=True, help="Starting URL (e.g., the platform's login page)")
    parser.add_argument("--out", required=True, help="Output directory for recovered images")
    parser.add_argument("--min-size", type=int, default=MIN_ASSET_SIZE_BYTES,
                         help="Minimum byte size to treat a response as a real photo (filters thumbnails)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (not recommended for manual login)")
    args = parser.parse_args()

    run_capture(args.url, Path(args.out), min_size=args.min_size, headless=args.headless)
