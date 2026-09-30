"""
extract_urls_from_raw_text.py

Extracts image URLs from a raw text dump (e.g., a saved page source or
network log) using regex, then downloads each one directly.

This is the "simple first attempt" approach: works well when image URLs are
exposed in plain text and don't require authentication or dynamic loading to
fetch. See browser_capture_recovery.py for the fallback approach when this
isn't sufficient.

Usage:
    python extract_urls_from_raw_text.py --input raw_page_dump.txt --out ./recovered_images
"""

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

URL_PATTERN = re.compile(r"(https?://[^\s\"']+\.(?:jpg|jpeg|png|webp))", re.IGNORECASE)


def find_image_urls(text: str) -> list:
    return sorted(set(URL_PATTERN.findall(text)))


def safe_filename(url: str) -> str:
    path = urlparse(url).path
    name = Path(path).name or "image.jpg"
    if "." not in name:
        name += ".jpg"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def download_all(urls: list, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for url in urls:
        try:
            print(f"Downloading {url}")
            response = session.get(url, timeout=30)
            response.raise_for_status()

            out_path = output_dir / safe_filename(url)
            counter = 1
            while out_path.exists():
                out_path = output_dir / f"{out_path.stem}_{counter}{out_path.suffix}"
                counter += 1

            out_path.write_bytes(response.content)
        except Exception as exc:
            print(f"Failed {url}: {exc}")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and download image URLs from a raw text dump.")
    parser.add_argument("--input", required=True, help="Path to raw text file containing URLs")
    parser.add_argument("--out", required=True, help="Output directory for downloaded images")
    args = parser.parse_args()

    raw_text = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    image_urls = find_image_urls(raw_text)
    print(f"Found {len(image_urls)} image URLs")

    download_all(image_urls, Path(args.out))
