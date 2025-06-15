import os
import sys

try:
    import markdown
except ImportError:
    markdown = None

try:
    import pypandoc
except ImportError:
    pypandoc = None

def convert_markdown_to_html(md_path, html_path):
    if not markdown:
        print("markdown package not available; cannot convert to HTML")
        return
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


def convert_markdown_to_rtf(md_path, rtf_path):
    if not pypandoc:
        print("pypandoc not available; skipping RTF conversion for", md_path)
        return
    pypandoc.convert_file(md_path, 'rtf', outputfile=rtf_path)


def convert_output(folder, output_format):
    for root, _, files in os.walk(folder):
        for file in files:
            if not file.endswith('.md'):
                continue
            md_path = os.path.join(root, file)
            base = md_path[:-3]
            if output_format == 'md+rtf':
                rtf_path = base + '.rtf'
                convert_markdown_to_rtf(md_path, rtf_path)
            elif output_format == 'html':
                html_path = base + '.html'
                convert_markdown_to_html(md_path, html_path)
                os.remove(md_path)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python format_converter.py <folder> <format>')
        sys.exit(1)
    folder = sys.argv[1]
    output_format = sys.argv[2]
    convert_output(folder, output_format)
