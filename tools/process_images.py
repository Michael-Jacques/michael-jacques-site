#!/usr/bin/env python3
"""Turn studio photos into the WebP the site serves.

Reads every JPG under assets/src/, auto-crops the seamless studio backdrop,
writes a 1600px and an 800px WebP alongside the site's other assets, and
refreshes each work's pixel size and colour palette in site.json.

    python3 tools/process_images.py
"""
import json, glob, os, colorsys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'src'
TRIM_TOLERANCE = 28   # how far a pixel must differ from the backdrop to count as artwork
EDGE_COVERAGE = .55   # fraction of a line that must be artwork for it to be an edge
EDGE_SEARCH = .22     # how far in from each side to look for that edge
SHAVE_FLAT = .45      # a strip this much flatter than the picture's middle is wall
SHAVE_BRIGHT = 4      # ...and this much lighter than it
SHAVE_MAX = .14       # never peel more than this off one side


def autocrop(im):
    """Crop away the studio backdrop.

    The backdrop colour is the median border pixel. A first pass finds the
    rough bounding box of everything that differs from it; a second pass walks
    in from each edge and stops at the first line that is genuinely part of the
    artwork, which removes the soft shadow and vignette the rough box keeps.
    """
    px = im.load(); W, H = im.size
    border = ([px[x, y] for x in range(0, W, 7) for y in (0, 1, H - 2, H - 1)] +
              [px[x, y] for y in range(0, H, 7) for x in (0, 1, W - 2, W - 1)])
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    diff = ImageChops.difference(im, Image.new('RGB', im.size, bg)).convert('L')
    mask = diff.point(lambda v: 255 if v > TRIM_TOLERANCE else 0)

    bb = mask.resize((max(W // 8, 1), max(H // 8, 1))).getbbox()
    if not bb:
        return im
    l, t, r, b = [v * 8 for v in bb]
    l, t = max(0, l - 8), max(0, t - 8)
    r, b = min(W, r + 8), min(H, b + 8)

    m = mask.crop((l, t, r, b)); mw, mh = m.size
    rows = [sum(m.crop((0, y, mw, y + 1)).point(lambda v: v // 255).getdata()) for y in range(mh)]
    cols = [sum(m.crop((x, 0, x + 1, mh)).point(lambda v: v // 255).getdata()) for x in range(mw)]

    def edge(counts, span, limit):
        """First index where the line is solidly artwork, not backdrop or shadow."""
        need = max(3, int(span * EDGE_COVERAGE))
        for i, c in enumerate(counts[:limit]):
            if c >= need:
                return i
        return 0

    depth_y, depth_x = int(mh * EDGE_SEARCH), int(mw * EDGE_SEARCH)
    top = edge(rows, mw, depth_y)
    bottom = mh - edge(rows[::-1], mw, depth_y)
    left = edge(cols, mh, depth_x)
    right = mw - edge(cols[::-1], mh, depth_x)
    if bottom - top < mh * .35 or right - left < mw * .35:
        return im.crop((l, t, r, b))
    return im.crop((l + left, t + top, l + right, t + bottom))


def shave_backdrop(im):
    """Peel any wall left on the edges after the bounding-box crop.

    The seamless backdrop reads flatter and lighter than the piece itself, so
    thin strips come off an edge only while that edge still looks like wall.
    """
    g = np.asarray(im.convert('L'), dtype=np.float32)
    H, W = g.shape
    core = g[int(H * .25):int(H * .75), int(W * .25):int(W * .75)]
    cm, cs = core.mean(), max(core.std(), 1e-6)
    step = .004
    sy, sx = max(3, int(H * step)), max(3, int(W * step))
    t, b, l, r = 0, H, 0, W
    is_wall = lambda s: s.std() / cs < SHAVE_FLAT and s.mean() - cm > SHAVE_BRIGHT

    for _ in range(int(SHAVE_MAX / step)):
        if not is_wall(g[t:t + sy, l:r]): break
        t += sy
    for _ in range(int(SHAVE_MAX / step)):
        if not is_wall(g[b - sy:b, l:r]): break
        b -= sy
    for _ in range(int(SHAVE_MAX / step)):
        if not is_wall(g[t:b, l:l + sx]): break
        l += sx
    for _ in range(int(SHAVE_MAX / step)):
        if not is_wall(g[t:b, r - sx:r]): break
        r -= sx

    if b - t < H * .6 or r - l < W * .6:
        return im                      # would cut into the painting; leave it alone
    return im.crop((l, t, r, b))


def palette(im, n=5, min_distance=46):
    """Five distinct colours from the painting, ordered light to dark.

    Sampled from the middle of the canvas so the frame and the wall behind it
    don't flood the result with neutrals."""
    W, H = im.size
    sm = im.crop((int(W * .14), int(H * .14), int(W * .86), int(H * .86)))
    sm.thumbnail((240, 240))
    q = sm.quantize(colors=14, method=Image.Quantize.MEDIANCUT).convert('RGB')
    ranked = [c for _, c in sorted(q.getcolors(240 * 240), reverse=True)]
    dist = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b)) ** .5
    picked = []
    for c in ranked:
        if all(dist(c, p) > min_distance for p in picked):
            picked.append(c)
        if len(picked) == n:
            break
    picked += ranked[len(picked):n]
    picked.sort(key=lambda c: -colorsys.rgb_to_hls(*[v / 255 for v in c])[1])
    return ['#%02x%02x%02x' % c for c in picked[:n]]


def render(src, out_base, widths, crop):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    if crop:
        im = shave_backdrop(autocrop(im))
    for suffix, w, q in widths:
        r = im.copy(); r.thumbnail((w, w * 4))
        r.save(f'{out_base}{suffix}.webp', 'WEBP', quality=q, method=6)
    return im


def main():
    site = json.load(open(ROOT / 'site.json'))
    by_slug = {w['slug']: (s['slug'], w) for s in site['series'] for w in s['works']}
    seen = set()

    for src in sorted(glob.glob(str(SRC / 'work' / '*' / '*.jpg'))):
        series, slug = Path(src).parent.name, Path(src).stem
        out_dir = ROOT / 'assets' / 'work' / series
        out_dir.mkdir(parents=True, exist_ok=True)
        im = render(src, out_dir / slug, [('', 1500, 78), ('-800', 800, 76)], crop=True)
        if slug in by_slug:
            _, w = by_slug[slug]
            w['w'], w['h'] = im.size
            w['palette'] = palette(im)
            seen.add(slug)
        else:
            print(f'  ! {series}/{slug}.jpg has no entry in site.json')
        print(f'  {series}/{slug}  {im.size[0]}x{im.size[1]}')

    for src in sorted(glob.glob(str(SRC / 'hero' / '*.jpg'))):
        out = ROOT / 'assets' / 'hero'
        out.mkdir(parents=True, exist_ok=True)
        render(src, out / Path(src).stem, [('', 1900, 78), ('-800', 800, 76)], crop=False)
        print(f'  hero/{Path(src).stem}')

    missing = set(by_slug) - seen
    if missing:
        print('  ! no photo found for:', ', '.join(sorted(missing)))

    json.dump(site, open(ROOT / 'site.json', 'w'), indent=1, ensure_ascii=False)
    print(f'\nupdated {len(seen)} works in site.json — now run: python3 build.py')


if __name__ == '__main__':
    main()
