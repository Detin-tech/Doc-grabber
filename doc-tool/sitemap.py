import sys
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import subprocess
import asyncio

class SitemapBuilder:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc.lower().lstrip('www.')
        self.visited = set()
        self.to_visit = [self.base_url]
        self.urls = []

    def is_internal(self, url):
        parsed = urlparse(url)
        url_domain = parsed.netloc.lower().lstrip('www.')
        # Allow subdomains
        return url_domain.endswith(self.domain)

    def crawl(self):
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; SitemapBuilder/1.0)'}
        while self.to_visit:
            url = self.to_visit.pop(0)
            if url in self.visited:
                continue
            print(f"Crawling {url}")
            try:
                r = requests.get(url, timeout=10, headers=headers)
                r.raise_for_status()
            except Exception as e:
                print(f"Failed {url}: {e}")
                self.visited.add(url)
                continue

            self.visited.add(url)
            self.urls.append(url)

            soup = BeautifulSoup(r.text, 'html.parser')
            links_found = []
            for link in soup.find_all('a', href=True):
                href = urljoin(url, link['href']).split('#')[0].rstrip('/')
                if not href.startswith('http'):
                    continue
                links_found.append(href)

                if self.is_internal(href) and href not in self.visited and href not in self.to_visit:
                    self.to_visit.append(href)

            print(f"  Found {len(links_found)} links on {url}")
            time.sleep(0.5)

    def save_xml(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in sorted(self.urls):
                f.write('  <url>\n')
                f.write(f'    <loc>{url}</loc>\n')
                f.write('  </url>\n')
            f.write('</urlset>\n')
        print(f"Sitemap saved to {filename}")

    def save_url_list(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            for url in sorted(self.urls):
                f.write(f"{url}\n")
        print(f"URL list saved to {filename}")

def ensure_playwright_installed():
    try:
        import playwright
        return True
    except ImportError:
        print("Playwright not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print("Running 'playwright install' to install browser binaries...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("Playwright installation complete.")
        return True

async def playwright_crawl(base_url, output_folder):
    from playwright.async_api import async_playwright

    urls = set()
    domain = urlparse(base_url).netloc.lower().lstrip("www.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Playwright crawling: {base_url}")

        to_visit = [base_url]
        visited = set()

        while to_visit:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            try:
                await page.goto(current_url, timeout=30000)
                print(f"Playwright visiting: {current_url}")
                visited.add(current_url)
                urls.add(current_url)

                anchors = await page.query_selector_all("a[href]")
                for a in anchors:
                    href = await a.get_attribute("href")
                    if href:
                        full_url = urljoin(current_url, href).split('#')[0].rstrip('/')
                        parsed = urlparse(full_url)
                        href_domain = parsed.netloc.lower().lstrip("www.")
                        if href_domain.endswith(domain) and full_url not in visited and full_url not in to_visit:
                            to_visit.append(full_url)

                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Playwright failed to visit {current_url}: {e}")

        await browser.close()

    os.makedirs(output_folder, exist_ok=True)
    sitemap_path = os.path.join(output_folder, "sitemap.xml")
    urls_txt_path = os.path.join(output_folder, "urls.txt")

    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in sorted(urls):
            f.write('  <url>\n')
            f.write(f'    <loc>{url}</loc>\n')
            f.write('  </url>\n')
        f.write('</urlset>\n')

    with open(urls_txt_path, 'w', encoding='utf-8') as f:
        for url in sorted(urls):
            f.write(f"{url}\n")

    print(f"Playwright crawler saved {len(urls)} URLs.")
    return sitemap_path, len(urls)

def run_playwright_crawler(base_url, output_folder):
    if not ensure_playwright_installed():
        print("Failed to install Playwright dependencies.")
        return None, 0
    try:
        return asyncio.run(playwright_crawl(base_url, output_folder))
    except Exception as e:
        print(f"Playwright crawling failed: {e}")
        return None, 0

def main():
    if len(sys.argv) != 3:
        print("Usage: python sitemap.py <base_url> <output_folder>")
        sys.exit(1)

    base_url = sys.argv[1]
    output_folder = sys.argv[2]

    sitemap_path = os.path.join(output_folder, "sitemap.xml")
    urls_txt_path = os.path.join(output_folder, "urls.txt")

    # First attempt: simple crawl
    print("Starting primary crawl with requests + BS4...")
    sitemap = SitemapBuilder(base_url)
    sitemap.crawl()

    # If too few URLs, do a more aggressive crawl (could be same logic or different approach)
    if len(sitemap.urls) < 20:
        print(f"Primary crawl too small ({len(sitemap.urls)} URLs). Retrying with recursive crawl...")

        # Reset and retry crawl to be sure (could be same class; here just recall crawl)
        sitemap = SitemapBuilder(base_url)
        sitemap.crawl()

    if len(sitemap.urls) < 20:
        print(f"Recursive crawl still too small ({len(sitemap.urls)} URLs). Falling back to Playwright...")
        sitemap_path, count = run_playwright_crawler(base_url, output_folder)
        if count < 20:
            print(f"Playwright crawler also returned too few URLs ({count}). Exiting.")
            sys.exit(1)
        else:
            print(f"Playwright crawler succeeded with {count} URLs.")
            sys.exit(0)
    else:
        sitemap.save_xml(sitemap_path)
        sitemap.save_url_list(urls_txt_path)
        print(f"Crawled {len(sitemap.urls)} URLs total.")

if __name__ == "__main__":
    main()
