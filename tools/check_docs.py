#!/usr/bin/env python3
"""Structural checks for the documentation set.

Run from the repository root: `python3 tools/check_docs.py`.
Exit code 1 when any check fails. Checks:

1. Every Markdown file has balanced ``` fences.
2. Every Markdown table row has the same number of columns as its header.
3. No raw `<placeholder>` outside code spans or fences (GitHub renders them as HTML tags).
4. Every relative link target exists.
5. Every rendered diagram in docs/diagrams/ is identical to the output of its script in
   tools/diagrams/ and is at most 100 columns wide.
6. Every diagram file is embedded verbatim somewhere in the documents (unused diagrams are
   reported as warnings, not failures).
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_WIDTH = 100
errors = []
warnings = []


def md_files():
    return [p for p in ROOT.rglob("*.md") if ".scratch" not in p.parts and ".git" not in p.parts]


def check_markdown(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
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
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#")[0]
        if target and not (path.parent / target).exists():
            errors.append(f"{path}: broken relative link {target}")


def check_diagrams():
    scripts = sorted((ROOT / "tools" / "diagrams").glob("*.py"))
    rendered_dir = ROOT / "docs" / "diagrams"
    all_docs = "\n".join(p.read_text(encoding="utf-8") for p in md_files())
    for script in scripts:
        rendered = rendered_dir / (script.stem + ".txt")
        out = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True).stdout
        if not rendered.exists():
            errors.append(f"{rendered} missing (run the script and save its output)")
            continue
        if out.rstrip("\n") != rendered.read_text(encoding="utf-8").rstrip("\n"):
            errors.append(f"{rendered} differs from the output of {script.name}")
        width = max((len(l) for l in out.splitlines()), default=0)
        if width > MAX_WIDTH:
            errors.append(f"{script.name}: diagram is {width} columns wide (max {MAX_WIDTH})")
        if out.rstrip("\n") not in all_docs:
            warnings.append(f"{rendered.name} is not embedded in any document")


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
