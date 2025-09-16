from __future__ import annotations

import os
import re
from typing import Dict, List, Any

from ebooklib import epub


def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\-\s]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name or "chapter"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_multimarkdown(base_dir: str, title: str, toc: List[str], chapters: Dict[str, str]) -> None:
    book_dir = os.path.join(base_dir, slugify(title))
    ensure_dir(book_dir)

    index_path = os.path.join(book_dir, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("## Table of Contents\n\n")
        for i, ch in enumerate(toc, 1):
            f.write(f"{i}. {ch}\n")

    for ch_title, content in chapters.items():
        ch_dir = os.path.join(book_dir, slugify(ch_title))
        ensure_dir(ch_dir)
        ch_path = os.path.join(ch_dir, "chapter.md")
        with open(ch_path, "w", encoding="utf-8") as f:
            f.write(f"# {ch_title}\n\n")
            f.write(content.strip() + "\n")


def make_epub(base_dir: str, title: str, author: str, toc: List[str], chapters: Dict[str, str]) -> str:
    book = epub.EpubBook()
    book.set_title(title)
    if author:
        book.add_author(author)

    items = []
    spine = ["nav"]
    nav = []

    for idx, ch_title in enumerate(toc, 1):
        content = chapters.get(ch_title, "")
        html = f"<h1>{ch_title}</h1>\n" + content.replace("\n", "<br/>")
        chapter_item = epub.EpubHtml(title=ch_title, file_name=f"chap_{idx}.xhtml", lang="en")
        chapter_item.content = html
        book.add_item(chapter_item)
        items.append(chapter_item)
        spine.append(chapter_item)
        nav.append(chapter_item)

    book.toc = tuple(nav)
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_dir = os.path.join(base_dir, slugify(title))
    ensure_dir(epub_dir)
    epub_path = os.path.join(epub_dir, f"{slugify(title)}.epub")
    epub.write_epub(epub_path, book)
    return epub_path


def publish(cfg: Dict[str, Any], toc: List[str], chapters: Dict[str, str]) -> Dict[str, str]:
    meta = cfg.get("meta", {})
    publishing = cfg.get("publishing", {})
    out_dir = publishing.get("out_dir", "./output")
    ensure_dir(out_dir)

    save_multimarkdown(out_dir, meta.get("title", "Untitled"), toc, chapters)

    result: Dict[str, str] = {}
    if publishing.get("make_epub", True):
        path = make_epub(out_dir, meta.get("title", "Untitled"), meta.get("author", ""), toc, chapters)
        result["epub"] = path
    return result
