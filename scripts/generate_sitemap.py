"""Generate and validate the GitHub Pages sitemap from published index.html files.

Run: python scripts/generate_sitemap.py
Check without writing: python scripts/generate_sitemap.py --check
"""

import argparse
import datetime
from html.parser import HTMLParser
import io
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://retuneworks.github.io/"
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"
NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
EXCLUDED_DIRS = {
    ".git", ".github", ".openai", "_site", "node_modules", "scripts",
    "test", "tests", "tmp", "temp", "backup", "backups", "draft", "drafts",
}


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href", "")
        elif tag == "meta":
            name = attrs.get("name", "").lower()
            if name == "description":
                self.description = attrs.get("content", "")
            elif name in {"robots", "googlebot"}:
                self.noindex |= "noindex" in attrs.get("content", "").lower()

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def git_output(*args):
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return result.stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Git history is required to produce reliable lastmod dates") from exc


def dirty_html_paths():
    # A new or edited HTML page is considered changed today, even before commit.
    output = git_output("status", "--porcelain", "--untracked-files=all", "-z")
    entries = output.split("\0")
    paths = set()
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        paths.add(entry[3:])
        if entry[:2][0] in "RC" or entry[:2][1] in "RC":
            index += 1  # Rename/copy records include the original path.
    return paths


def public_pages():
    dirty = dirty_html_paths()
    today = datetime.datetime.now().astimezone().date().isoformat()
    pages = []
    for html_file in ROOT.rglob("index.html"):
        relative = html_file.relative_to(ROOT)
        if any(part.startswith(".") or part.lower() in EXCLUDED_DIRS for part in relative.parts[:-1]):
            continue
        suffix = "/".join(quote(part) for part in relative.parts[:-1])
        url = SITE_URL + (suffix + "/" if suffix else "")
        head = HeadParser()
        head.feed(html_file.read_text(encoding="utf-8"))
        if head.noindex:
            print("Excluded noindex page: " + relative.as_posix(), file=sys.stderr)
            continue
        if head.canonical and head.canonical != url:
            print("Excluded non-canonical page: " + relative.as_posix(), file=sys.stderr)
            continue
        missing = [name for name, value in (("title", head.title), ("description", head.description), ("canonical", head.canonical)) if not value.strip()]
        if missing:
            raise ValueError("Missing " + ", ".join(missing) + " in " + relative.as_posix())
        path = relative.as_posix()
        lastmod = today if path in dirty else git_output("log", "-1", "--format=%cs", "--", path).strip()
        if not lastmod:
            # Newly created, not yet staged: its content was added today.
            lastmod = today
        datetime.date.fromisoformat(lastmod)
        pages.append((url, lastmod))
    pages.sort(key=lambda page: (page[0] != SITE_URL, page[0]))
    urls = [url for url, _ in pages]
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate public URL found")
    return pages


def sitemap_bytes(pages):
    ET.register_namespace("", NAMESPACE)
    root = ET.Element("{" + NAMESPACE + "}urlset")
    for url, lastmod in pages:
        item = ET.SubElement(root, "{" + NAMESPACE + "}url")
        ET.SubElement(item, "{" + NAMESPACE + "}loc").text = url
        ET.SubElement(item, "{" + NAMESPACE + "}lastmod").text = lastmod
    def indent(element, level=0):
        # Compatible with Python versions before ElementTree.indent was added.
        space = "\n" + "  " * level
        if len(element):
            element.text = space + "  "
            for child in element:
                indent(child, level + 1)
            element[-1].tail = space
        if level:
            element.tail = space

    indent(root)
    buffer = io.BytesIO()
    ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue() + b"\n"


def validate(content, pages):
    root = ET.fromstring(content)
    if root.tag != "{" + NAMESPACE + "}urlset":
        raise ValueError("Invalid sitemap namespace")
    entries = []
    for item in root.findall("{" + NAMESPACE + "}url"):
        url = item.findtext("{" + NAMESPACE + "}loc")
        lastmod = item.findtext("{" + NAMESPACE + "}lastmod")
        if not url or not url.startswith(SITE_URL) or "index.html" in url or "404.html" in url:
            raise ValueError("Invalid sitemap URL: " + str(url))
        if not lastmod or datetime.date.fromisoformat(lastmod).isoformat() != lastmod:
            raise ValueError("Invalid lastmod: " + str(lastmod))
        entries.append((url, lastmod))
    if entries != pages:
        raise ValueError("Sitemap entries do not match the published pages")
    robots = ROBOTS.read_text(encoding="utf-8")
    if "Sitemap: " + SITE_URL + "sitemap.xml" not in robots:
        raise ValueError("robots.txt does not reference sitemap.xml")
    if any(line.strip().lower() == "disallow: /" for line in robots.splitlines()):
        raise ValueError("robots.txt blocks the entire site")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate sitemap.xml without changing it")
    args = parser.parse_args()
    pages = public_pages()
    content = sitemap_bytes(pages)
    validate(content, pages)
    if args.check:
        if not SITEMAP.exists() or SITEMAP.read_bytes() != content:
            raise ValueError("sitemap.xml is out of date; run python scripts/generate_sitemap.py")
        print("sitemap.xml is current ({} URLs)".format(len(pages)))
    else:
        if not SITEMAP.exists() or SITEMAP.read_bytes() != content:
            SITEMAP.write_bytes(content)
            print("Updated sitemap.xml ({} URLs)".format(len(pages)))
        else:
            print("sitemap.xml is already current ({} URLs)".format(len(pages)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, ET.ParseError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        sys.exit(1)
