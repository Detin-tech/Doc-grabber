import os
import sys
import hashlib
import asyncio
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

# Optional: Install playwright and import only if used
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def sha256_hash(text: str) -> str:
    """Calculate SHA256 hash of a given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def url_to_filepath(url: str, base_folder: str) -> str:
    """
    Convert URL to file path inside base_folder.
    Keeps folder structure for readability.
    Example: https://domain.com/docs/page -> base_folder/docs/page.md
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path or path.endswith('/'):
        path = os.path.join(path, 'index') if path else 'index'
    full_path = os.path.join(base_folder, path) + '.md'
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path

def extract_main_content(html: str) -> str:
    """
    Extract main text content from HTML using BeautifulSoup.
    Customize selectors here for target site.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Try <main>, then <article>, then fallback to <body>
    for selector in ['main', 'article', 'body']:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator='\n').strip()
            if text:
                return text
    # Fallback full text if nothing found
    return soup.get_text(separator='\n').strip()

def save_markdown_file(filepath: str, content: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def load_existing_file(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def fetch_html_requests(url: str) -> str:
    """Simple requests-based HTML fetch as fallback."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[requests] Failed to download {url}: {e}")
        return None

async def fetch_html_playwright(url: str, wait_selector: str = None) -> str:
    """
    Use Playwright to fetch fully rendered HTML.
    Waits for `wait_selector` if provided.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[playwright] Playwright not installed. Skipping.")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)

            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=30000)

            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"[playwright] Failed to fetch {url}: {e}")
        return None

async def main_async(urls_file: str, base_folder: str, use_playwright: bool = True, wait_selector: str = None):
    if not os.path.exists(urls_file):
        print(f"URLs file not found: {urls_file}")
        sys.exit(1)

    os.makedirs(base_folder, exist_ok=True)

    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        print(f"\nProcessing: {url}")
        md_path = url_to_filepath(url, base_folder)

        existing_content = load_existing_file(md_path)
        existing_hash = sha256_hash(existing_content) if existing_content else None

        # Prefer Playwright for JS-heavy sites, else fallback to requests
        html = None
        if use_playwright:
            html = await fetch_html_playwright(url, wait_selector)
        if html is None:
            html = fetch_html_requests(url)

        if html is None:
            print(f"Skipping {url} due to download failure.")
            continue

        content = extract_main_content(html)
        new_hash = sha256_hash(content)

        if existing_hash == new_hash:
            print(f"Skipped (no change): {md_path}")
            continue

        save_markdown_file(md_path, content)
        print(f"Saved/Updated: {md_path}")

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python scraper.py <urls.txt> <output_folder> [wait_css_selector_for_playwright]")
        print("Example wait_css_selector_for_playwright: '.docs-container'")
        sys.exit(1)

    urls_file = sys.argv[1]
    output_folder = sys.argv[2]
    wait_selector = sys.argv[3] if len(sys.argv) == 4 else None

    # Run asyncio loop with playwright usage by default
    asyncio.run(main_async(urls_file, output_folder, use_playwright=True, wait_selector=wait_selector))

if __name__ == "__main__":
    main()
