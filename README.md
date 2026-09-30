# Photo Archive Recovery & HTML-to-Slideshow Converter

Two related utilities built to solve a real problem: recovering personal photo archives from a platform without a reliable bulk-export feature, then repurposing saved HTML pages (e.g., old photo-book/scrapbook page exports) into shareable slide decks.

## Problem

Some consumer photo platforms don't offer a simple "download everything" option. When a bulk export isn't available, the only way to recover full-resolution images is to capture them as the browser loads them. Separately, content saved as static HTML (like an exported scrapbook or photo-book page) isn't easy to share or present, but the images and text inside it can be extracted and reassembled into a slide deck.

## What's here

### 1. Photo recovery (two approaches, escalating in complexity)

- **extract_urls_from_raw_text.py** - the first approach: pulls image URLs out of raw saved page text/network logs via regex, then downloads each one directly. Fast and simple, but only works if the image URLs are exposed in plain text and don't require an authenticated session to fetch.
- **browser_capture_recovery.py** - the approach used when the simple method wasn't enough: a Playwright browser automation script that logs into the photo platform, listens to live network responses as pages/albums are browsed, and saves any response that looks like a real photo asset (by content-type and minimum file size, to filter out thumbnails/icons). This was necessary because the platform served full-resolution images only through authenticated, dynamically-loaded network requests that a simple URL scrape couldn't reach.

### 2. HTML to slideshow

- **html_to_pptx.py** - parses a saved HTML page (headings, paragraphs, images), downloads any linked images, and reassembles the content into a PowerPoint deck: one slide per heading section, with body text and the section's image placed automatically.

## Why this is here

This shows practical problem-solving under real constraints: when the straightforward method (regex + direct download) didn't work because of authentication and dynamic loading, the solution was to move up a level of technical sophistication (browser automation with response interception) rather than give up on recovering the data. The HTML-to-PPTX tool is a separate but related skill: parsing semi-structured markup and programmatically generating a structured document from it.

## Tech stack

- **Playwright** - headless/headed browser automation, network response interception
- **BeautifulSoup + lxml** - HTML parsing
- **python-pptx** - programmatic PowerPoint generation
- **requests** - HTTP downloads

## Status

Functional for personal use cases; in progress - next step is parameterizing the site-specific filters in browser_capture_recovery.py (currently tuned to one photo platform's URL patterns) so it generalizes to other sites.

## Usage

```bash
pip install -r requirements.txt
playwright install chromium

# Approach 1: if image URLs are visible in saved page text/logs
python extract_urls_from_raw_text.py --input raw_page_dump.txt --out ./recovered_images

# Approach 2: if images require an authenticated, dynamically-loaded session
python browser_capture_recovery.py --url https://example-photo-site.com/login --out ./recovered_images

# HTML to slideshow
python html_to_pptx.py --html scrapbook_page.html --out slideshow.pptx --base-url https://example.com
```
