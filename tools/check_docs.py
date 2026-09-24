#!/usr/bin/env python3
"""Structural checks for the documentation set.

Run from the repository root: `python3 tools/check_docs.py`.
Exit code 1 when any check fails. Checks:

1. Every Markdown file has balanced ``` fences.
2. Every Markdown table row has the same number of columns as its header.
3. No raw `<placeholder>` outside code spans or fences (GitHub renders them as HTML tags).
4. Every relative link target exists.
5. Every Mermaid source in tools/diagrams/*.mmd starts with a known diagram type and is embedded
   verbatim in at least one document as a ```mermaid block.
6. Every ```mermaid block in the documents matches one of the sources (edit the source, then
   paste; never edit a diagram inline).
7. Every document under docs/ (except folder README.md indexes and docs/archive/) starts with the
   header block of CONTRIBUTING.md: Purpose, Audience, Verified and Sources.
8. Every relative link with a #fragment, and every in-page #link, points to an existing heading.
9. Warning: two headings with the same text in one file (their anchors become ambiguous).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIAGRAM_TYPES = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram", "gantt", "mindmap")
errors = []
warnings = []


def md_files():
    return [p for p in ROOT.rglob("*.md") if not {".scratch", ".git", "node_modules"} & set(p.parts)]


HEADER_LABELS = ("**Purpose:**", "**Audience:**", "**Verified:**", "**Sources:**")


def slug(heading: str) -> str:
    """GitHub heading anchor."""
    s = re.sub(r"[`*_]", "", heading.strip().lower())
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


_anchor_cache = {}


def anchors(path: pathlib.Path):
    if path not in _anchor_cache:
        seen, out, in_fence = {}, set(), False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m and not in_fence:
                base = slug(m.group(2))
                n = seen.get(base, 0)
                out.add(base if n == 0 else f"{base}-{n}")
                seen[base] = n + 1
        _anchor_cache[path] = out
    return _anchor_cache[path]


def needs_header(path: pathlib.Path) -> bool:
    rel = path.relative_to(ROOT)
    return rel.parts[0] == "docs" and "archive" not in rel.parts and path.name != "README.md"


def check_header(path: pathlib.Path, lines):
    head = "\n".join(lines[:25])
    missing = [l for l in HEADER_LABELS if l not in head]
    if missing:
        errors.append(f"{path}: header block missing {', '.join(missing)} (see CONTRIBUTING.md section 1)")


def check_markdown(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if needs_header(path):
        check_header(path, lines)
    heads, in_f = {}, False
    for n, l in enumerate(lines, 1):
        if l.strip().startswith("```"):
            in_f = not in_f
        elif not in_f and re.match(r"^#{2,6}\s", l):
            key = l.lstrip("#").strip().lower()
            if key in heads and path.name != "CHANGELOG.md":
                warnings.append(f"{path}:{n}: duplicate heading '{key}' (first at line {heads[key]})")
            heads.setdefault(key, n)
    fences = sum(1 for l in lines if l.strip().startswith("```"))
    if fences % 2:
        errors.append(f"{path}: unbalanced code fences")
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        stripped = re.sub(r"`[^`]*`", "", line)
        stripped = re.sub(r"<https?://[^>]+>", "", stripped)
        if re.search(r"<[A-Za-z][^>]*>", stripped):
            errors.append(f"{path}:{i + 1}: raw angle-bracket placeholder outside a code span")
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            ncol = line.count("|")
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                if lines[j].count("|") != ncol:
                    errors.append(f"{path}:{j + 1}: table row has {lines[j].count('|')} separators, header has {ncol}")
                j += 1
            i = j
            continue
        i += 1
    for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        file_part, _, frag = target.partition("#")
        dest = (path.parent / file_part) if file_part else path
        if file_part and not dest.exists():
            errors.append(f"{path}: broken relative link {file_part}")
            continue
        if frag and dest.suffix == ".md" and frag not in anchors(dest.resolve()):
            errors.append(f"{path}: link to missing anchor {file_part}#{frag}")


def mermaid_blocks(text: str):
    return [b.strip("\n") for b in re.findall(r"```mermaid\n(.*?)```", text, flags=re.S)]


def check_diagrams():
    sources = {p.name: p.read_text(encoding="utf-8").strip("\n") for p in sorted((ROOT / "tools" / "diagrams").glob("*.mmd"))}
    docs = {p: p.read_text(encoding="utf-8") for p in md_files() if "archive" not in p.parts}
    embedded = [b for t in docs.values() for b in mermaid_blocks(t)]
    for name, src in sources.items():
        first = src.splitlines()[0].strip() if src else ""
        if not first.startswith(DIAGRAM_TYPES):
            errors.append(f"tools/diagrams/{name}: first line is not a Mermaid diagram type ({first[:30]!r})")
        if src not in embedded:
            warnings.append(f"tools/diagrams/{name} is not embedded in any document")
    for p, t in docs.items():
        for b in mermaid_blocks(t):
            if b not in sources.values():
                errors.append(f"{p}: a mermaid block does not match any source in tools/diagrams/")


def main():
    for p in md_files():
        check_markdown(p)
    check_diagrams()
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(md_files())} Markdown files checked, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
