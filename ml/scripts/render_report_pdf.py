"""Render a Markdown report to PDF using an installed Chromium browser.

The report is converted to styled HTML and printed with headless Chrome or Edge.
Relative images are embedded so the PDF is a single portable file.
"""

from __future__ import annotations

import argparse
import base64
import re
import subprocess
import sys
from pathlib import Path

import markdown

BROWSER_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

STYLESHEET = """
@page { size: A4; margin: 17mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.4pt;
  line-height: 1.52;
  color: #1c2430;
  margin: 0;
}
h1 {
  font-size: 21pt;
  line-height: 1.2;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 3px solid #3b6ea5;
  color: #14263a;
}
h2 {
  font-size: 14.5pt;
  margin: 26px 0 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid #d7dee8;
  color: #1f4e79;
  page-break-after: avoid;
}
h3 {
  font-size: 11.5pt;
  margin: 18px 0 8px;
  color: #33475b;
  page-break-after: avoid;
}
h1 code, h2 code, h3 code { font-size: inherit; background: none; padding: 0; }
p, li { orphans: 3; widows: 3; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0 16px;
  font-size: 9.1pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th, td {
  border: 1px solid #c7d1dd;
  padding: 4px 7px;
  vertical-align: top;
  text-align: left;
}
th { background: #e8eef6; color: #14263a; font-weight: 600; }
tbody tr:nth-child(even) { background: #f7f9fc; }
code {
  font-family: Consolas, "Cascadia Mono", monospace;
  font-size: 8.9pt;
  background: #f1f4f8;
  padding: 1px 3px;
  border-radius: 3px;
}
pre {
  background: #f4f6f9;
  border-left: 3px solid #3b6ea5;
  padding: 8px 10px;
  margin: 8px 0 14px;
  white-space: pre-wrap;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 8.6pt; }
img {
  display: block;
  max-width: 100%;
  max-height: 125mm;
  width: auto;
  margin: 12px auto 4px;
  page-break-inside: avoid;
}
blockquote {
  border-left: 3px solid #c58b3b;
  background: #fbf7ee;
  margin: 12px 0;
  padding: 6px 12px;
}
a { color: #1f4e79; text-decoration: none; }
ul, ol { margin: 6px 0 12px; padding-left: 22px; }
li { margin: 3px 0; }
hr { border: none; border-top: 1px solid #d7dee8; margin: 22px 0; }
"""

IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\((?!data:)([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Markdown report to PDF.")
    parser.add_argument("report", type=Path, help="Markdown file to render.")
    parser.add_argument(
        "--output",
        type=Path,
        help="PDF destination. Defaults to the report path with a .pdf suffix.",
    )
    parser.add_argument("--browser", type=Path, help="Chromium executable to use.")
    return parser.parse_args()


def find_browser(explicit: Path | None) -> Path:
    if explicit is not None:
        if not explicit.is_file():
            raise SystemExit(f"Browser not found: {explicit}")
        return explicit
    for candidate in BROWSER_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return path
    raise SystemExit("No Chromium browser found. Pass --browser <path>.")


def inline_images(source: str, base_dir: Path) -> str:
    """Embed relative images as data URIs so the HTML has no external files."""

    def replace(match: re.Match[str]) -> str:
        alt, reference = match.group(1), match.group(2)
        path = (base_dir / reference).resolve()
        if not path.is_file():
            print(f"warning: missing image {path}", file=sys.stderr)
            return match.group(0)
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        suffix = path.suffix.lower().lstrip(".").replace("jpg", "jpeg")
        return f"![{alt}](data:image/{suffix};base64,{payload})"

    return IMAGE_PATTERN.sub(replace, source)


def build_html(source: str, base_dir: Path, title: str) -> str:
    body = markdown.markdown(
        inline_images(source, base_dir),
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        output_format="html5",
    )
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{title}</title>\n<style>{STYLESHEET}</style>\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def render_pdf(html_path: Path, pdf_path: Path, browser: Path) -> None:
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if completed.returncode != 0 or not pdf_path.is_file():
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(f"PDF rendering failed:\n{detail}")


def main() -> None:
    args = parse_args()
    report = args.report.resolve()
    if not report.is_file():
        raise SystemExit(f"Report not found: {report}")

    pdf = (args.output or report.with_suffix(".pdf")).resolve()
    html = pdf.with_suffix(".html")
    browser = find_browser(args.browser)

    html.write_text(
        build_html(report.read_text(encoding="utf-8"), report.parent, report.stem),
        encoding="utf-8",
    )
    try:
        render_pdf(html, pdf, browser)
    finally:
        html.unlink(missing_ok=True)

    print(f"PDF written: {pdf} ({pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
