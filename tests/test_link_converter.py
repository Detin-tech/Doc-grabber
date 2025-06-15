import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location('link_converter', pathlib.Path(__file__).parent.parent / 'doc-tool' / 'link_converter.py')
link_converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(link_converter)


def test_replace_links_in_markdown(monkeypatch, tmp_path):
    md = tmp_path / 'test.md'
    md.write_text('See https://example.com/docs/page1 and https://bad.com/invalid. Also see /guide/intro')

    def fake_is_url_valid(url):
        return 'example.com' in url

    monkeypatch.setattr(link_converter, 'is_url_valid', fake_is_url_valid)

    link_converter.replace_links_in_markdown(str(tmp_path))

    content = md.read_text()
    assert '[[docs/page1]]' in content
    assert 'https://bad.com/invalid' in content
    assert '[[guide/intro]]' in content

