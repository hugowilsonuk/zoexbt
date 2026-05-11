#!/usr/bin/env python3
"""
Merge legacy carousel assets (dist/img/sliders-legacy-git/) with portfolio/ sources
into dist/img/sliders/01..22 — additive rebuild (nothing dropped).

Requires dist/img/sliders-legacy-git/ from: git archive HEAD dist/img/sliders | tar -x
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "dist/img/sliders-legacy-git"
PORT = ROOT / "portfolio"
OUT = ROOT / "dist/img/sliders"
ALLP = ROOT / "dist/img/all-projects"

CHROME_NAMES = ("bl-hover.svg", "bl.svg", "border.png", "br-hover.svg", "br.svg", "wrapper.png")


def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def sorted_media(folder: Path, image: bool) -> list[Path]:
    if not folder.is_dir():
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp"} if image else {".mp4", ".webm", ".mov"}
    files = [p for p in folder.iterdir() if p.suffix.lower() in exts and not p.name.startswith(".")]
    return sorted(files, key=lambda p: natural_key(p.name))


def merge_slider(idx: int, parts: list[tuple[str, Path]]) -> int:
    """parts: list of (kind, Path). Writes OUT/{idx:02d}/01.ext ... Returns slide count."""
    d = OUT / f"{idx:02d}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    n = 1
    for _kind, folder in parts:
        imgs = sorted_media(folder, image=True)
        vids = sorted_media(folder, image=False)
        for p in imgs + vids:
            ext = p.suffix.lower() or ".bin"
            shutil.copy2(p, d / f"{n:02d}{ext}")
            n += 1
    return n - 1


def thumb_from_first_slide(idx: int, dest_name: str) -> None:
    """Copy first merged asset as folder thumbnail (jpg/png/webp)."""
    d = OUT / f"{idx:02d}"
    files = sorted([p for p in d.iterdir() if p.is_file()], key=lambda p: natural_key(p.name))
    if not files:
        return
    first = files[0]
    if first.suffix.lower() == ".mp4":
        return
    ext = first.suffix.lower() or ".jpg"
    shutil.copy2(first, ALLP / f"{dest_name}{ext}")


def copy_slider_chrome() -> None:
    for name in CHROME_NAMES:
        src = LEGACY / name
        if src.is_file():
            shutil.copy2(src, OUT / name)


def main() -> None:
    if not LEGACY.is_dir():
        raise SystemExit(f"Missing {LEGACY}")

    ALLP.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # Illustration sliders 1–15
    ill_specs = [
        (1, "myro", "$MYRO", [("legacy", LEGACY / "01"), ("port", PORT / "MYRO" / "illustrations")]),
        (2, "four", "$FOUR", [("legacy", LEGACY / "02")]),
        (3, "axol", "$AXOL", [("legacy", LEGACY / "03"), ("port", PORT / "AXOL" / "illustrations")]),
        (4, "lofi", "$LOFI", [("legacy", LEGACY / "04"), ("port", PORT / "LOFI" / "illustrations")]),
        (5, "kimba", "$KIMBA", [("legacy", LEGACY / "05")]),
        (6, "metropolis", "$METROPOLIS", [("port", PORT / "METROPOLIS" / "illustrations")]),
        (7, "muskit", "$MUSKIT", [("port", PORT / "MUSKIT" / "illustrations")]),
        (8, "dino", "$DINO", [("port", PORT / "DINO" / "illustrations")]),
        (9, "trump", "$TRUMP", [("legacy", LEGACY / "06"), ("port", PORT / "TRUMP" / "illustrations")]),
        (10, "mbapepe", "$MBAPEPE", [("legacy", LEGACY / "07")]),
        (11, "lucky", "$LUCKY", [("legacy", LEGACY / "08")]),
        (12, "duck", "$DUCK", [("legacy", LEGACY / "09")]),
        (13, "ducky", "$DUCKY", [("port", PORT / "DUCKY" / "illustrations")]),
        (14, "evan", "$EVAN", [("port", PORT / "EVAN" / "illustrations")]),
        (15, "orbit-boy", "$ORBIT", [("port", PORT / "ORBIT-BOY" / "illustrations")]),
    ]

    ill_rows: list[tuple[int, str, str, str, int]] = []
    for idx, thumb_base, ticker, parts in ill_specs:
        c = merge_slider(idx, [(k, p) for k, p in parts])
        thumb_from_first_slide(idx, thumb_base)
        ill_rows.append((idx, thumb_base, ticker, "ARTS", c))

    # Animation sliders 16–22 (reuse illustration thumbs for shared tickers)
    anim_specs = [
        (16, "axol", "$AXOL", [("legacy", LEGACY / "10"), ("port", PORT / "AXOL" / "animations")]),
        (17, "lofi", "$LOFI", [("legacy", LEGACY / "11"), ("port", PORT / "LOFI" / "animations")]),
        (18, "metropolis", "$METROPOLIS", [("port", PORT / "METROPOLIS" / "animations")]),
        (19, "muskit", "$MUSKIT", [("port", PORT / "MUSKIT" / "animations")]),
        (20, "evan", "$EVAN", [("port", PORT / "EVAN" / "animations")]),
        (21, "nyan", "$NYAN", [("legacy", LEGACY / "12"), ("port", PORT / "NYAN" / "animations")]),
        (22, "suicy", "$SUICY", [("port", PORT / "SUICY" / "animations")]),
    ]

    anim_rows: list[tuple[int, str, str, str, int]] = []
    for idx, thumb_base, ticker, parts in anim_specs:
        c = merge_slider(idx, [(k, p) for k, p in parts])
        anim_rows.append((idx, thumb_base, ticker, "ANIMATIONS", c))

    # Folder icons: shared tickers already have thumbs from illustration pass.
    pag_nyan = LEGACY / "12" / "pag" / "01.png"
    if pag_nyan.is_file():
        shutil.copy2(pag_nyan, ALLP / "nyan.png")
    suicy_fallback = ALLP / "suicy.png"
    if not suicy_fallback.is_file():
        # Optional: user adds suicy.png manually; animation-only project
        pass

    copy_slider_chrome()

    manifest = ROOT / "dist" / "_slider-manifest.txt"
    lines = ["# idx thumb_base ticker count kind"]
    for idx, thumb_base, ticker, kind, c in ill_rows:
        lines.append(f"{idx:02d} {thumb_base} {ticker} {c} {kind}")
    for idx, thumb_base, ticker, kind, c in anim_rows:
        lines.append(f"{idx:02d} {thumb_base} {ticker} {c} {kind}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote", manifest)
    print("Sliders 1–15 illustration, 16–22 animation. Chrome copied to", OUT)


if __name__ == "__main__":
    main()
