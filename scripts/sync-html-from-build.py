#!/usr/bin/env python3
"""Patch dist/index.html folders + swiper markup from dist/_slider-manifest.txt and dist/img/sliders/."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "dist/index.html"
MANIFEST = ROOT / "dist/_slider-manifest.txt"
SL = ROOT / "dist/img/sliders"
ALLP = ROOT / "dist/img/all-projects"


def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def thumb_href(thumb_base: str) -> str:
    """Fallback when a slider folder has no raster images (video-only). Prefer png over jpg."""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (ALLP / f"{thumb_base}{ext}").is_file():
            return f"img/all-projects/{thumb_base}{ext}"
    raise FileNotFoundError(f"No thumbnail for {thumb_base} in {ALLP}")


def folder_thumb_src(slider_idx: int, thumb_base: str) -> str:
    """Same file as the first image slide (or first raster in folder order); matches big preview."""
    d = SL / f"{slider_idx:02d}"
    files = sorted([p for p in d.iterdir() if p.is_file()], key=lambda p: natural_key(p.name))
    for p in files:
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            return f"img/sliders/{slider_idx:02d}/{p.name}"
    return thumb_href(thumb_base)


def nth_tabs_folders_inner_span(html: str, n: int) -> tuple[int, int]:
    """1-based nth <div class=\"tabs__folders\"> inner span [start, end) — content between open and its closing tag."""
    needle = '<div class="tabs__folders">'
    idx = -1
    for _ in range(n):
        idx = html.find(needle, idx + 1)
        if idx == -1:
            raise ValueError(f"tabs__folders #{n} not found")
    # needle includes the closing `>` of the opening tag
    inner_start = idx + len(needle)
    depth = 0
    i = inner_start
    while True:
        sub = html[i:]
        mo = re.search(r"<div\b", sub)
        mc = re.search(r"</div>", sub)
        if mc is None:
            raise ValueError("unbalanced div in tabs__folders")
        mo_pos = mo.start() if mo else 10**9
        mc_pos = mc.start()
        if mo and mo_pos < mc_pos:
            depth += 1
            i += mo_pos + len("<div")
        else:
            if depth == 0:
                inner_end = i + mc_pos
                return inner_start, inner_end
            depth -= 1
            i += mc_pos + len("</div>")


def folder_block(ticker: str, count: int, thumb_base: str, slider_idx: int) -> str:
    src = folder_thumb_src(slider_idx, thumb_base)
    tab = "\t\t\t\t\t\t\t\t\t\t"
    tab2 = tab + "\t"
    return (
        f'{tab}<div class="tabs__folder">\n'
        f'{tab2}<div class="tabs__folder-image">\n'
        f'{tab2}\t<img src="{src}" alt="{ticker}" />\n'
        f'{tab2}</div>\n'
        f'{tab2}<div class="tabs__folder-info">\n'
        f'{tab2}\t<span>{ticker}</span>\n'
        f'{tab2}\t<span>({count})</span>\n'
        f'{tab2}</div>\n'
        f'{tab}</div>\n\n'
    )


def slide_inner(path: Path, ticker: str) -> str:
    rel = f"img/sliders/{path.parent.name}/{path.name}"
    tab = "\t\t\t\t\t\t\t\t\t\t"
    tab2 = tab + "\t"
    if path.suffix.lower() in {".mp4", ".webm", ".mov"}:
        return (
            f'{tab}<div class="main-page__slide swiper-slide">\n'
            f'{tab2}<video muted loop playsinline webkit-playsinline src="{rel}"></video>\n'
            f'{tab}</div>\n\n'
        )
    return (
        f'{tab}<div class="main-page__slide swiper-slide">\n'
        f'{tab2}<img src="{rel}" alt="{ticker}" />\n'
        f'{tab}</div>\n\n'
    )


def slider_block(idx: int, ticker: str, active: bool) -> str:
    d = SL / f"{idx:02d}"
    files = sorted([p for p in d.iterdir() if p.is_file()], key=lambda p: natural_key(p.name))
    inner = "".join(slide_inner(p, ticker) for p in files)
    active_cls = " active" if active else ""
    tab = "\t\t\t\t\t\t\t\t"
    tab2 = tab + "\t"
    tab3 = tab2 + "\t"
    return (
        f'{tab}<div class="main-page__slider main-page__slider--{idx} swiper{active_cls}">\n'
        f'{tab2}<div class="main-page__wrapper swiper-wrapper">\n'
        f"{inner}"
        f'{tab2}</div>\n'
        f'{tab2}<div class="main-page__swiper-pagination swiper-pagination"></div>\n'
        f"{tab}</div>\n\n"
    )


def parse_manifest() -> tuple[list[tuple], list[tuple]]:
    ill, anim = [], []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        idx = int(parts[0])
        thumb_base = parts[1]
        ticker = parts[2]
        count = int(parts[3])
        kind = parts[4]
        row = (idx, thumb_base, ticker, count)
        if kind == "ARTS":
            ill.append(row)
        else:
            anim.append(row)
    return ill, anim


def main() -> None:
    ill, anim = parse_manifest()
    folders_ill = "".join(folder_block(t, c, tb, idx) for idx, tb, t, c in ill)
    folders_anim = "".join(folder_block(t, c, tb, idx) for idx, tb, t, c in anim)
    sliders = "".join(slider_block(idx, ticker, idx == 1) for idx, _, ticker, _ in ill + anim)

    html = INDEX.read_text(encoding="utf-8")

    s1, e1 = nth_tabs_folders_inner_span(html, 1)
    html = html[:s1] + "\n" + folders_ill + html[e1:]

    s2, e2 = nth_tabs_folders_inner_span(html, 2)
    html = html[:s2] + "\n" + folders_anim + html[e2:]

    box_start = html.find('<div class="main-page__slider-box">')
    if box_start == -1:
        raise SystemExit("main-page__slider-box not found")
    box_inner_start = html.find(">", box_start) + 1
    nav_start = html.find('<div class="main-page__bottom-navigation">', box_inner_start)
    if nav_start == -1:
        raise SystemExit("bottom-navigation not found")
    html = html[:box_inner_start] + "\n" + sliders + "\t\t\t\t\t\t\t" + html[nav_start:]

    _, _, t1, c1 = ill[0]
    html = re.sub(
        r'<div class="main-page__bottom-navigation-info-name">\s*[\s\S]*?</div>',
        f'<div class="main-page__bottom-navigation-info-name">\n\t\t\t\t\t\t\t\t\t\t{t1}\n\t\t\t\t\t\t\t\t\t</div>',
        html,
        count=1,
    )
    html = re.sub(
        r'<div class="main-page__bottom-navigation-info-num-of-arts">\s*[\s\S]*?</div>',
        f'<div class="main-page__bottom-navigation-info-num-of-arts">\n\t\t\t\t\t\t\t\t\t\t({c1} ARTS)\n\t\t\t\t\t\t\t\t\t</div>',
        html,
        count=1,
    )

    INDEX.write_text(html, encoding="utf-8")
    print("Patched", INDEX)


if __name__ == "__main__":
    main()
