import os
import sys

try:
    import markdown  # type: ignore
except ImportError:  # pragma: no cover - fallback when markdown is missing
    markdown = None

try:
    import pypandoc
except ImportError:
    pypandoc = None

def _simple_markdown_to_html(text: str) -> str:
    """Very small subset Markdown -> HTML converter used when the markdown
    package is unavailable. Only handles headings and paragraphs.
    """
    html_lines = []
    for line in text.splitlines():
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:].strip()}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:].strip()}</h2>')
        elif line:
            html_lines.append(f'<p>{line}</p>')
    return "\n".join(html_lines)


def convert_markdown_to_html(md_path, html_path):
    if not markdown:
        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()
        html = _simple_markdown_to_html(text)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return True


def convert_markdown_to_rtf(md_path, rtf_path):
    if not pypandoc:
        print("pypandoc not available; skipping RTF conversion for", md_path)
        return
    pypandoc.convert_file(md_path, 'rtf', outputfile=rtf_path)


def convert_output(folder, output_format):
    output_format = output_format.lower()
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
                if convert_markdown_to_html(md_path, html_path):
                    os.remove(md_path)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python format_converter.py <folder> <format>')
        sys.exit(1)
    folder = sys.argv[1]
    output_format = sys.argv[2]
    convert_output(folder, output_format)
