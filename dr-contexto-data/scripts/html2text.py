#!/usr/bin/env python3
"""Minimal HTML -> readable text extractor (stdlib only).

Strips script/style/nav/footer noise and collapses whitespace so the output is
usable as source material for downstream text analysis. Not a full-fidelity
renderer, just a clean reading copy.

Usage:
    python3 html2text.py <input.html> [output.txt]
    cat page.html | python3 html2text.py - > out.txt
"""
import sys
import re
from html.parser import HTMLParser
from html import unescape

SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form"}
BLOCK_TAGS = {
    "p", "div", "section", "article", "li", "ul", "ol", "br", "tr", "table",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "blockquote",
}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag in {"h1", "h2", "h3"}:
            self.parts.append("\n## ")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            text = data.strip()
            if text:
                self.parts.append(text + " ")


def clean(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    html = sys.stdin.read() if src == "-" else open(src, encoding="utf-8", errors="replace").read()
    parser = Extractor()
    parser.feed(html)
    out = clean("".join(parser.parts))
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as fh:
            fh.write(out)
        print(f"wrote {len(out)} chars -> {sys.argv[2]}")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
