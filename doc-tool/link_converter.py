import os
import sys
import re
import hashlib
import requests
from urllib.parse import urlparse

verbose = False  # Global flag

def log(msg):
    if verbose:
        print(msg)

def is_url_valid(url):
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        log(f"Checked URL: {url} -> {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        log(f"URL check failed: {url} -> {e}")
        return False

def url_to_path(url, base_folder):
    path = urlparse(url).path.strip('/')
    if not path:
        path = 'index.md'
    elif path.endswith('/'):
        path += 'index.md'
    else:
        path += '.md'
    return os.path.join(base_folder, path)

def file_checksum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def replace_links_in_markdown(folder, output_format='md'):
    print(f"Scanning markdown files in: {folder}")
    url_map = {}
    skipped_urls = set()

    for root, _, files in os.walk(folder):
        for file in files:
            if not file.endswith('.md'):
                continue
            filepath = os.path.join(root, file)
            log(f"Processing file: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find both absolute URLs and relative paths starting with /
            urls = set(re.findall(r'(https?://[^\s)>\]]+|\/[^\s)>\]]+)', content))
            log(f"  Found {len(urls)} links")
            for url in urls:
                if url not in url_map:
                    if url.startswith('http'):
                        if is_url_valid(url):
                            rel_path = os.path.relpath(url_to_path(url, folder), os.path.dirname(filepath))
                            rel_path = rel_path.replace(os.sep, '/')
                            if rel_path.endswith('.md'):
                                rel_path = rel_path[:-3]
                            if output_format == 'html':
                                url_map[url] = f'[{rel_path}]({rel_path}.html)'
                                log(f"    HTTP: {url} -> [{rel_path}]({rel_path}.html)")
                            else:
                                url_map[url] = f'[[{rel_path}]]'
                                log(f"    HTTP: {url} -> [[{rel_path}]]")
                        else:
                            skipped_urls.add(url)
                            log(f"    Skipped invalid URL: {url}")
                    elif url.startswith('/'):
                        rel_path = os.path.relpath(url_to_path(url, folder), os.path.dirname(filepath))
                        rel_path = rel_path.replace(os.sep, '/')
                        if rel_path.endswith('.md'):
                            rel_path = rel_path[:-3]
                        if output_format == 'html':
                            url_map[url] = f'[{rel_path}]({rel_path}.html)'
                            log(f"    REL: {url} -> [{rel_path}]({rel_path}.html)")
                        else:
                            url_map[url] = f'[[{rel_path}]]'
                            log(f"    REL: {url} -> [[{rel_path}]]")

            for url, obsidian_link in url_map.items():
                content = content.replace(url, obsidian_link)

            # Clean up any accidental [[open-webui]]/foo/bar leftovers
            content = re.sub(r'\[\[open-webui\]\]/([^\s)]+)', r'\1', content)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    print(f"Replaced {len(url_map)} links with Obsidian style links.")
    if skipped_urls:
        print(f"Skipped {len(skipped_urls)} URLs due to invalid/unreachable status:")
        for url in skipped_urls:
            print(f"  - {url}")

def load_sitemap_urls(folder):
    sitemap_path = os.path.join(folder, "sitemap.xml")
    if not os.path.exists(sitemap_path):
        print(f"No sitemap.xml found in {folder}, skipping sitemap link loading.")
        return []
    with open(sitemap_path, 'r', encoding='utf-8') as f:
        content = f.read()
    urls = re.findall(r'<loc>(.*?)</loc>', content)
    log(f"Loaded {len(urls)} URLs from sitemap")
    return urls

def inject_backlinks(folder, output_format='md'):
    print(f"Injecting backlinks in markdown files at: {folder}")

    # Load all markdown files content indexed by relative path without .md
    md_files = {}
    for root, _, files in os.walk(folder):
        for file in files:
            if not file.endswith('.md'):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, folder).replace(os.sep, '/')
            key = rel_path[:-3]  # strip .md
            with open(full_path, 'r', encoding='utf-8') as f:
                md_files[key] = f.read()

    sitemap_urls = load_sitemap_urls(folder)
    # Map sitemap URLs to keys (relative md paths)
    sitemap_map = {}
    for url in sitemap_urls:
        path = urlparse(url).path.strip('/')
        if not path or path.endswith('/'):
            path = os.path.join(path, 'index.md')
        else:
            path += '.md'
        rel_path = path.replace('\\','/').lstrip('/')
        key = rel_path[:-3]
        sitemap_map[url] = key

    # Build a reverse index: for each md file, find what other files mention it
    mentions = {k: set() for k in md_files.keys()}

    # For performance, precompile regexes for each key
    key_regex = {k: re.compile(r'\b' + re.escape(k.split('/')[-1].replace('-', ' ')) + r'\b', re.IGNORECASE) for k in md_files.keys()}

    # Detect mentions (simple heuristic: does file content mention the last slug of other files)
    for src_key, src_content in md_files.items():
        for target_key, regex in key_regex.items():
            if src_key == target_key:
                continue
            if regex.search(src_content):
                mentions[target_key].add(src_key)

    # Now inject backlinks for each md file
    for key, backlinked_from in mentions.items():
        if not backlinked_from:
            continue
        md_path = os.path.join(folder, key + '.md')
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Prepare backlink section
        backlinks = '\n\n---\n\n**Related:**\n\n'
        for ref_key in sorted(backlinked_from):
            display_name = ref_key.split('/')[-1].replace('-', ' ')
            if output_format == 'html':
                backlinks += f"- [{display_name}]({ref_key}.html)\n"
            else:
                backlinks += f"- [[{ref_key}]]\n"

        # Append backlink section if not already present (idempotency)
        if '**Related:**' not in content:
            content += backlinks
            # Write only if changed
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log(f"Injected backlinks into {md_path}")

    print("Backlink injection complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python link_converter.py <output_folder> [--verbose] [--format <fmt>]")
        sys.exit(1)

    output_folder = sys.argv[1]
    output_format = 'md'
    args = sys.argv[2:]
    if "--verbose" in args:
        verbose = True
        print("Verbose mode enabled.")
        args.remove("--verbose")
    if "--format" in args:
        idx = args.index("--format")
        if idx < len(args) - 1:
            output_format = args[idx + 1]

    replace_links_in_markdown(output_folder, output_format)
    inject_backlinks(output_folder, output_format)
