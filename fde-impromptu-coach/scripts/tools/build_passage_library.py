#!/usr/bin/env python3
"""Build (or verify) assets/passages.json: verbatim paragraphs from free,
public-domain books for the legato and pronunciation practices.

Every passage is located in a downloaded source edition (Standard Ebooks via
its GitHub sources, or Project Gutenberg via the GITenberg mirror) by
paragraph position plus optional start/end anchors, then copied verbatim.
Only typographic normalisation is applied: line wrapping, invisible word
joiners, Gutenberg _italic_ / =bold= markers, "--" dashes and drop-cap
capitals. Nothing is paraphrased or written by a model.

    python3 build_passage_library.py build   [--cache DIR]   # writes assets/passages.json
    python3 build_passage_library.py verify  [--cache DIR]   # re-extracts, diffs against the asset

Inputs (next to the skill's assets folder):
    assets/passage_sources.json   books + passage locations
    assets/passage_annotations.json  pronunciation target words per passage (coach notes)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / "assets"
SE_RAW = "https://raw.githubusercontent.com/standardebooks/{repo}/master/src/epub/{path}"
GB_RAW = "https://raw.githubusercontent.com/GITenberg/{repo}/master/{file}"
SE_PAGE = "https://standardebooks.org/ebooks/{path}"
GB_PAGE = "https://www.gutenberg.org/ebooks/{id}"
NS = {"opf": "http://www.idpf.org/2007/opf", "x": "http://www.w3.org/1999/xhtml"}
EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"


# --------------------------------------------------------------------------- download

def _get(url: str) -> bytes:
    err: Exception = RuntimeError("no attempt")
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - retried, then raised
            err = exc
            time.sleep(2)
    raise err


def _xhtml_text(el) -> str:
    from lxml import etree
    out: List[str] = []

    def walk(node, top: bool = False) -> None:
        if not isinstance(node.tag, str):
            if node.tail and not top:
                out.append(node.tail)
            return
        tag = etree.QName(node).localname
        noteref = tag == "a" and "noteref" in (node.get(EPUB_TYPE) or "")
        if not noteref:
            if tag == "br":
                out.append(" ")
            if node.text:
                out.append(node.text)
            for child in node:
                walk(child)
        if node.tail and not top:
            out.append(node.tail)

    walk(el, top=True)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def fetch_standardebooks(repo: str) -> List[Dict[str, Any]]:
    from lxml import etree
    opf = etree.fromstring(_get(SE_RAW.format(repo=repo, path="content.opf")))
    manifest = {i.get("id"): i.get("href") for i in opf.findall(".//opf:manifest/opf:item", namespaces=NS)}
    spine = [manifest[i.get("idref")] for i in opf.findall(".//opf:spine/opf:itemref", namespaces=NS)]
    skip = ("titlepage", "imprint", "colophon", "uncopyright", "halftitle", "endnotes", "loi")
    sections = []
    for href in spine:
        if not href.startswith("text/") or any(k in href for k in skip):
            continue
        doc = etree.fromstring(_get(SE_RAW.format(repo=repo, path=href)))
        paras = [_xhtml_text(p) for p in doc.xpath("//x:body//x:p[not(ancestor::x:header)]", namespaces=NS)]
        sections.append({"file": href, "paras": [p for p in paras if p]})
    return sections


def fetch_gutenberg(repo: str, file: str) -> List[Dict[str, Any]]:
    raw = _get(GB_RAW.format(repo=repo, file=file)).decode("utf-8", errors="replace").replace("\r\n", "\n")
    start = re.search(r"\*\*\*\s*START OF.*?\*\*\*", raw)
    end = re.search(r"\*\*\*\s*END OF", raw)
    body = raw[start.end() if start else 0: end.start() if end else len(raw)]
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body)]
    return [{"file": file, "paras": [p for p in paras if p]}]


def load_book(key: str, book: Dict[str, Any], cache: Path) -> List[Dict[str, Any]]:
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{book['repo']}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["sections"]
    if book["source"] == "standardebooks":
        sections = fetch_standardebooks(book["repo"])
    else:
        sections = fetch_gutenberg(book["repo"], book["file"])
    path.write_text(json.dumps({"repo": book["repo"], "sections": sections}, ensure_ascii=False), encoding="utf-8")
    return sections


# --------------------------------------------------------------------------- normalisation + stats
# One implementation shared with the runtime importer (fdecoach.library).
sys.path.insert(0, str(SKILL / "scripts"))
from fdecoach.library import MAX_WORDS as LIB_MAX, MIN_WORDS as LIB_MIN  # noqa: E402
from fdecoach.library import level_of, normalize as _normalize  # noqa: E402


def normalize(text: str, source: str) -> str:
    return _normalize(text, gutenberg=(source == "gutenberg"))


def extract(spec: Dict[str, Any], book: Dict[str, Any], sections: List[Dict[str, Any]]) -> str:
    si, pi = spec["loc"]
    span = int(spec.get("span", 1))
    paras = sections[si]["paras"][pi:pi + span]
    if len(paras) != span:
        raise ValueError(f"{spec['id']}: location out of range")
    text = normalize(" ".join(paras), book["source"])
    if spec.get("start"):
        i = text.find(spec["start"])
        if i < 0:
            raise ValueError(f"{spec['id']}: start anchor not found")
        if i > 0 and not re.search(r"[.!?;:][”’\"']?\s$", text[:i]):
            raise ValueError(f"{spec['id']}: start anchor is not at a sentence boundary")
        text = text[i:]
    if spec.get("end"):
        j = text.find(spec["end"])
        if j < 0:
            raise ValueError(f"{spec['id']}: end anchor not found")
        text = text[:j + len(spec["end"])]
    if not re.search(r"[.!?;”’\"']$", text):
        raise ValueError(f"{spec['id']}: passage does not end at a sentence boundary: …{text[-30:]!r}")
    return text


def source_info(book: Dict[str, Any]) -> Dict[str, Any]:
    if book["source"] == "standardebooks":
        return {"name": "Standard Ebooks", "url": SE_PAGE.format(path=book["repo"].replace("_", "/")),
                "license": "Public domain (Standard Ebooks' own edits are CC0)"}
    return {"name": "Project Gutenberg", "url": GB_PAGE.format(id=book["gutenberg_id"]),
            "gutenberg_id": book["gutenberg_id"], "license": "Public domain in the USA"}


def build(cache: Path) -> Dict[str, Any]:
    spec = json.loads((ASSETS / "passage_sources.json").read_text(encoding="utf-8"))
    ann_path = ASSETS / "passage_annotations.json"
    annotations = json.loads(ann_path.read_text(encoding="utf-8")) if ann_path.exists() else {}
    books = spec["books"]
    loaded: Dict[str, List[Dict[str, Any]]] = {}
    out: List[Dict[str, Any]] = []
    problems: List[str] = []
    for p in spec["passages"]:
        book = books[p["book"]]
        if p["book"] not in loaded:
            loaded[p["book"]] = load_book(p["book"], book, cache)
        try:
            text = extract(p, book, loaded[p["book"]])
        except ValueError as exc:
            problems.append(str(exc))
            continue
        words = len(text.split())
        if not LIB_MIN <= words <= LIB_MAX:
            problems.append(f"{p['id']}: {words} words (want {LIB_MIN}-{LIB_MAX})")
        entry = {
            "id": p["id"], "text": text, "author": book["author"], "work": book["work"], "year": book["year"],
            "section": p.get("section", ""), "theme": p.get("theme", ""), "words": words, "level": level_of(text),
            "source": source_info(book),
        }
        if book.get("translator"):
            entry["translator"] = book["translator"]
        if p["id"] in annotations:
            entry["pronunciation"] = annotations[p["id"]]
        out.append(entry)
    return {"version": 1, "about": spec["about"], "passages": out, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["build", "verify", "review"])
    ap.add_argument("--cache", default=str(Path.home() / ".cache" / "fde-coach-sources"))
    args = ap.parse_args()
    lib = build(Path(args.cache).expanduser())
    problems = lib.pop("problems")
    for prob in problems:
        print("PROBLEM:", prob, file=sys.stderr)
    if args.mode == "review":
        for e in lib["passages"]:
            print(f"--- {e['id']}  ({e['words']}w, L{e['level']})  {e['author']}, {e['work']} — {e['section']}")
            print(e["text"], "\n")
        return 1 if problems else 0
    target = ASSETS / "passages.json"
    if args.mode == "verify":
        have = json.loads(target.read_text(encoding="utf-8"))
        want = {e["id"]: e["text"] for e in lib["passages"]}
        bad = [e["id"] for e in have["passages"] if e.get("origin", "builtin") == "builtin" and want.get(e["id"]) != e["text"]]
        print(f"{len(have['passages']) - len(bad)} passages match their sources verbatim; {len(bad)} differ: {bad}")
        return 1 if bad or problems else 0
    if problems:
        return 1
    target.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(lib['passages'])} passages -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
