#!/usr/bin/env python3
"""
Legacy portfolio-only sync (no legacy carousel merge).

For the full site (legacy Git sliders + portfolio), run instead:

  python3 scripts/build-merged-sliders.py
  python3 scripts/sync-html-from-build.py

Then minify JS if you ship app.min.js (e.g. npx terser dist/js/app.js -c -m -o dist/js/app.min.js).

Copies portfolio media from portfolio/<PROJECT>/ into dist/img/ for deploy.

Run from repo root: python3 scripts/sync-portfolio-assets.py
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_IMG = ROOT / "dist" / "img"
SRC = ROOT / "portfolio"

# Illustration tab order → slider index 1..10 (folder thumbnails + image sliders)
ILLUSTRATION = [
    ("MYRO", "myro"),
    ("AXOL", "axol"),
    ("LOFI", "lofi"),
    ("METROPOLIS", "metropolis"),
    ("MUSKIT", "muskit"),
    ("DINO", "dino"),
    ("DUCKY", "ducky"),
    ("EVAN", "evan"),
    ("ORBIT-BOY", "orbit-boy"),
    ("TRUMP", "trump"),
]

# Animation tab order → slider index 11..17 (must match JS tab order: folders after illustration set)
ANIMATION = [
    ("AXOL", "axol"),
    ("LOFI", "lofi"),
    ("METROPOLIS", "metropolis"),
    ("MUSKIT", "muskit"),
    ("EVAN", "evan"),
    ("NYAN", "nyan"),
    ("SUICY", "suicy"),
]


def natural_key(s: str):
    return [
        int(t) if t.isdigit() else t.lower()
        for t in re.split(r"(\d+)", s)
    ]


def sorted_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    files = [
        p for p in folder.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        and not p.name.startswith(".")
    ]
    return sorted(files, key=lambda p: natural_key(p.name))


def sorted_videos(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    files = [
        p for p in folder.iterdir()
        if p.suffix.lower() in {".mp4", ".webm", ".mov"}
        and not p.name.startswith(".")
    ]
    return sorted(files, key=lambda p: natural_key(p.name))


def ensure_clean_slider_dir(idx: int) -> Path:
    d = DIST_IMG / "sliders" / f"{idx:02d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def copy_slide(src: Path, dest_dir: Path, n: int) -> None:
    ext = src.suffix.lower() or ".jpg"
    name = f"{n:02d}{ext}"
    shutil.copy2(src, dest_dir / name)


def main() -> None:
    all_projects = DIST_IMG / "all-projects"
    all_projects.mkdir(parents=True, exist_ok=True)

    for i, (folder_name, slug) in enumerate(ILLUSTRATION, start=1):
        ill = SRC / folder_name / "illustrations"
        imgs = sorted_images(ill)
        if not imgs:
            print(f"WARN: no illustrations in {ill}")
            continue
        ext = imgs[0].suffix.lower() or ".jpg"
        shutil.copy2(imgs[0], all_projects / f"{slug}{ext}")

        dest = ensure_clean_slider_dir(i)
        for j, img in enumerate(imgs, start=1):
            copy_slide(img, dest, j)

    # Animation-only projects: folder thumbnail from first video frame not available — reuse legacy or generic
    for folder_name, slug in ANIMATION:
        ill = SRC / folder_name / "illustrations"
        imgs = sorted_images(ill)
        if imgs:
            ext = imgs[0].suffix.lower() or ".jpg"
            shutil.copy2(imgs[0], all_projects / f"{slug}{ext}")
        elif slug == "nyan" and (legacy := all_projects / "nyan-anim.png").exists():
            shutil.copy2(legacy, all_projects / "nyan.png")
        else:
            placeholder = all_projects / "folder.png"
            if placeholder.exists():
                shutil.copy2(placeholder, all_projects / f"{slug}.png")
            print(f"WARN: no illustration thumb for {slug}, used folder.png if present")

    offset = len(ILLUSTRATION)
    for i, (folder_name, slug) in enumerate(ANIMATION, start=1):
        idx = offset + i
        anim = SRC / folder_name / "animations"
        vids = sorted_videos(anim)
        if not vids:
            print(f"WARN: no animations in {anim}")
            continue
        dest = ensure_clean_slider_dir(idx)
        for j, vid in enumerate(vids, start=1):
            ext = vid.suffix.lower() or ".mp4"
            shutil.copy2(vid, dest / f"{j:02d}{ext}")

    print("Done. Slider dirs:", DIST_IMG / "sliders")


if __name__ == "__main__":
    main()
