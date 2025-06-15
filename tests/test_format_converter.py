import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location('format_converter', pathlib.Path(__file__).parent.parent / 'doc-tool' / 'format_converter.py')
format_converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(format_converter)


def test_convert_output_html(tmp_path):
    md = tmp_path / 'file.md'
    md.write_text('# Title\n\nSome text', encoding='utf-8')
    format_converter.convert_output(str(tmp_path), 'html')
    html = tmp_path / 'file.html'
    assert html.exists()
    assert '<h1>Title' in html.read_text(encoding='utf-8')
    assert not md.exists()

