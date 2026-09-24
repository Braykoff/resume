#!/usr/bin/env python3
"""Compile resume.tex to PDF with secret-latex and render each page as a PNG.

Pages are written under rendered/. Also rewrites the "Resume Preview" section at the bottom of README.md to
show one image per rendered page.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEX_FILE = REPO_ROOT / "resume.tex"
RENDERED_DIR = REPO_ROOT / "rendered"
README_FILE = REPO_ROOT / "README.md"

PAGE_PREFIX = "page_"


def compile_pdf(tex_file: Path, out_dir: Path) -> Path:
    subprocess.run(
        [
            "secret-latex",
            "build",
            tex_file.name,
            "--root",
            str(tex_file.parent),
            "--output-dir",
            str(out_dir),
            "--engine-arg=-interaction=nonstopmode",
            "--engine-arg=-halt-on-error",
            "--secrets-file=none" # Do not use any secrets file
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    pdf_path = out_dir / (tex_file.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"Expected PDF not found at {pdf_path}")
    return pdf_path


def clear_rendered_dir(rendered_dir: Path) -> None:
    rendered_dir.mkdir(parents=True, exist_ok=True)
    for png in rendered_dir.glob("*.png"):
        png.unlink()


def render_pages(pdf_path: Path, rendered_dir: Path) -> list[Path]:
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            "150",
            str(pdf_path),
            str(rendered_dir / PAGE_PREFIX.rstrip("_")),
        ],
        check=True,
    )

    pages = []
    for png in sorted(rendered_dir.glob(f"{PAGE_PREFIX.rstrip('_')}-*.png")):
        match = re.search(r"-(\d+)\.png$", png.name)
        page_num = int(match.group(1))
        new_name = rendered_dir / f"{PAGE_PREFIX}{page_num:03d}.png"
        png.rename(new_name)
        pages.append(new_name)

    return sorted(pages)


def update_readme(readme_file: Path, pages: list[Path], rendered_dir: Path) -> None:
    content = readme_file.read_text()

    marker = "<!-- BEGIN RESUME PREVIEW -->"
    end_marker = "<!-- END RESUME PREVIEW -->"

    rel_dir = rendered_dir.relative_to(readme_file.parent)
    lines = [marker, "## Resume Preview", ""]
    for page in pages:
        rel_path = rel_dir / page.name
        lines.append(f"![{page.stem}]({rel_path.as_posix()})")
        lines.append("")
    lines.append(end_marker)
    block = "\n".join(lines).rstrip() + "\n"

    if marker in content and end_marker in content:
        pattern = re.compile(
            re.escape(marker) + r".*?" + re.escape(end_marker), re.DOTALL
        )
        content = pattern.sub(block.rstrip("\n"), content)
    else:
        content = content.rstrip("\n") + "\n\n" + block

    readme_file.write_text(content)


def main() -> int:
    if not TEX_FILE.exists():
        print(f"Could not find {TEX_FILE}", file=sys.stderr)
        return 1

    clear_rendered_dir(RENDERED_DIR)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pdf_path = compile_pdf(TEX_FILE, tmp_path)
        pages = render_pages(pdf_path, RENDERED_DIR)

    if not pages:
        print("No pages were rendered", file=sys.stderr)
        return 1

    update_readme(README_FILE, pages, RENDERED_DIR)

    print(f"Rendered {len(pages)} page(s) to {RENDERED_DIR}")
    print(f"Updated {README_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
