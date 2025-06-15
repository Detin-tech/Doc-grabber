import importlib.util
import pathlib
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('sitemap', pathlib.Path(__file__).parent.parent / 'doc-tool' / 'sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)


def test_sitemap_crawl(monkeypatch):
    html_pages = {
        'http://example.com': '<a href="/about">About</a><a href="http://external.com">Ext</a>',
        'http://example.com/about': '<p>No links</p>'
    }

    class MockResponse:
        def __init__(self, url):
            self.text = html_pages[url]
            self.status_code = 200
        def raise_for_status(self):
            pass

    def mock_get(url, timeout=10, headers=None):
        return MockResponse(url)

    monkeypatch.setattr(sitemap.requests, 'get', mock_get)
    monkeypatch.setattr(sitemap.time, 'sleep', lambda x: None)

    builder = sitemap.SitemapBuilder('http://example.com')
    builder.crawl()

    assert sorted(builder.urls) == ['http://example.com', 'http://example.com/about']

