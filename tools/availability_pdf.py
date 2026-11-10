#!/usr/bin/env python3
"""Build an availability PDF for a gallery, consultant or hotel art buyer.

Reads site.json, keeps the works that haven't sold, groups them by where the
canvas physically is, and prints a tearsheet: cover, bio, one card per work
with its image, dimensions and price, then contact details.

    python3 tools/availability_pdf.py
    python3 tools/availability_pdf.py --to "Hotel Art Advisory"
    python3 tools/availability_pdf.py --only new-york

Where each painting is stored lives in LOCATIONS below — the default is Miami,
so only the pieces that have travelled need listing.
"""
import argparse, base64, json, mimetypes, shutil, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'exports'
FONTS = OUT / '.fonts'

# Slugs that are NOT in the Miami studio. Everything else is Miami.
LOCATIONS = {
    'look-up-for-once':        'New York',
    'under-the-magnolia-tree': 'New York',
    'deep':                    'New York',
    'higher-self':             'New York',
}
DEFAULT_LOCATION = 'Miami'
ORDER = ['New York', 'Miami']          # the order cities appear in the document

CHROME = ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
          '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
          '/Applications/Chromium.app/Contents/MacOS/Chromium')

PRINT_PX = 1100        # long edge of the images embedded in the PDF (~300dpi at print size)


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def font_face(file: Path) -> str:
    _, style, weight = file.stem.split('-')
    family = 'Newsreader' if file.stem.startswith('newsreader') else 'PlexMono'
    return (f"@font-face{{font-family:'{family}';font-style:{style};"
            f"font-weight:{weight};src:url({data_uri(file)}) format('woff2')}}")


def print_image(slug: str, series_slug: str) -> str:
    """Re-encode the web asset down to print size, as a JPEG data URI."""
    from PIL import Image
    src = ROOT / 'assets' / 'work' / series_slug / f'{slug}.webp'
    im = Image.open(src).convert('RGB')
    im.thumbnail((PRINT_PX, PRINT_PX))
    tmp = OUT / '.print' / f'{slug}.jpg'
    tmp.parent.mkdir(parents=True, exist_ok=True)
    im.save(tmp, 'JPEG', quality=86, optimize=True)
    return data_uri(tmp)


def dimensions(w):
    """Return the size as height x width, checked against the photograph.

    The site lists sizes height-first, but at least one work was entered the
    other way round. The photo's aspect settles it: the long side of the canvas
    is the long side of the picture, so a landscape piece gets the smaller
    number first whatever order it was typed in.
    """
    import re
    nums = [int(n) for n in re.findall(r'\d+', w['size'])[:2]]
    if len(nums) != 2 or nums[0] == nums[1]:
        return w['size'], False
    lo, hi = min(nums), max(nums)
    landscape = w['w'] > w['h']
    h, v = (lo, hi) if landscape else (hi, lo)
    fixed = f'{h}" x {v}"'
    return fixed, fixed.replace(' ', '') != w['size'].replace(' ', '')


def collect(site, only=None):
    works = []
    for series in site['series']:
        for w in series['works']:
            if w['sold']:
                continue
            city = LOCATIONS.get(w['slug'], DEFAULT_LOCATION)
            if only and city.lower().replace(' ', '-') != only:
                continue
            size, corrected = dimensions(w)
            works.append(dict(w, series=series['name'], series_slug=series['slug'],
                              city=city, size=size, corrected=corrected))
    works.sort(key=lambda w: (ORDER.index(w['city']) if w['city'] in ORDER else 99,
                              -int(w['size'].split('"')[0]), w['title']))
    return works


def build_html(site, works, to=None):
    e = lambda s: (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    fonts = ''.join(font_face(f) for f in sorted(FONTS.glob('*.woff2')))
    today = date.today().strftime('%B %Y')
    cities = [c for c in ORDER if any(w['city'] == c for w in works)]
    by_city = {c: [w for w in works if w['city'] == c] for c in cities}
    cover_img = print_image('introspection', 'everything')

    def tally(c):
        n = len(by_city[c])
        return f"{n} work{'s' if n != 1 else ''}"

    cards = ''
    for city in cities:
        cards += f'''<section class="city">
  <div class="city-head">
    <h2>{e(city)}</h2>
    <p class="mono">{tally(city)} available · ready to view</p>
  </div>
  <div class="grid">'''
        for w in by_city[city]:
            cards += f'''
    <figure class="work">
      <div class="plate"><img src="{print_image(w['slug'], w['series_slug'])}" alt="{e(w['title'])}"></div>
      <figcaption>
        <h3>{e(w['title'])}<span class="yr">, {w['year']}</span></h3>
        <p class="series">{e(w['series'])}</p>
        <dl>
          <div><dt>Size (h&nbsp;&times;&nbsp;w)</dt><dd>{e(w['size'])}</dd></div>
          <div><dt>Medium</dt><dd>{e(w['medium'].capitalize())}</dd></div>
          <div><dt>Location</dt><dd>{e(w['city'])}</dd></div>
          <div><dt>Price</dt><dd class="price">{e(w['price'])}</dd></div>
        </dl>
      </figcaption>
    </figure>'''
        cards += '\n  </div>\n</section>'

    shows = ''.join(
        f'<div><dt>{e(s["year"])}</dt><dd>{e(s["name"])}<span>{e(s["place"])}</span></dd></div>'
        for s in site['shows'])
    summary = ''.join(
        f'<div><dt>{e(c)}</dt><dd>{tally(c)}</dd></div>' for c in cities)
    total_low = min(int(w['price'].replace('$', '').replace(',', '')) for w in works)
    total_high = max(int(w['price'].replace('$', '').replace(',', '')) for w in works)
    addressed = f'<p class="mono to">Prepared for {e(to)}</p>' if to else ''

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Michael Jacques — Available Works</title>
<style>
{fonts}
@page {{ size: Letter; margin: 14mm 14mm 16mm; }}
@page :first {{ margin: 0; }}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{font-family:'Newsreader',Georgia,serif;color:#121212;background:#fff;
     font-size:10.5pt;line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
h1,h2,h3{{font-weight:400;margin:0;letter-spacing:-.015em}}
.mono{{font-family:'PlexMono',ui-monospace,monospace;font-size:7.6pt;letter-spacing:.14em;
      text-transform:uppercase;line-height:1.7}}

/* cover */
.cover{{position:relative;height:279.4mm;width:215.9mm;overflow:hidden;
       page-break-after:always;background:#f9f8f2;display:flex;flex-direction:column}}
.cover-img{{height:58%;overflow:hidden;background:#121212}}
.cover-img img{{width:100%;height:100%;object-fit:cover;display:block;opacity:.94}}
.cover-body{{flex:1;padding:14mm 16mm;display:flex;flex-direction:column;justify-content:space-between}}
.cover h1{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-weight:600;
          font-size:34pt;line-height:.95;letter-spacing:-.035em;text-transform:uppercase}}
.cover .sub{{font-size:15pt;font-style:italic;margin-top:5mm;color:#3a3a38}}
.cover .meta{{display:flex;gap:9mm;border-top:.4pt solid rgba(18,18,18,.35);padding-top:4mm}}
.cover .meta div{{flex:1}}
.cover .meta dd{{white-space:nowrap}}
.cover .meta dt{{font-family:'PlexMono',monospace;font-size:7pt;letter-spacing:.16em;
                text-transform:uppercase;color:#6b6a66;margin-bottom:1.5mm}}
.cover .meta dd{{margin:0;font-size:10.5pt}}
.to{{color:#6b6a66;margin:0 0 3mm}}

/* bio */
.bio{{page-break-after:always;padding-top:2mm}}
.lede{{font-size:17pt;line-height:1.25;letter-spacing:-.02em;max-width:30em;margin:0 0 9mm;text-wrap:pretty}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:10mm;margin-bottom:9mm}}
.two p{{margin:0 0 3.5mm}}
.label{{display:block;color:#6b6a66;margin-bottom:3mm;border-top:.4pt solid rgba(18,18,18,.3);padding-top:2mm}}
dl{{margin:0}}
dl div{{display:grid;grid-template-columns:auto 1fr;gap:4mm;padding:1.6mm 0;
       border-bottom:.3pt solid rgba(18,18,18,.14);align-items:baseline}}
dl dt{{font-family:'PlexMono',monospace;font-size:7.4pt;letter-spacing:.1em;
      text-transform:uppercase;color:#6b6a66;white-space:nowrap}}
dl dd{{margin:0;font-size:10pt}}
dl dd span{{display:block;font-family:'PlexMono',monospace;font-size:7.2pt;
           letter-spacing:.08em;text-transform:uppercase;color:#6b6a66}}
.summary dl div{{grid-template-columns:1fr auto}}
.summary dd{{font-family:'PlexMono',monospace;font-size:8pt;letter-spacing:.06em}}

/* works */
.city{{page-break-before:always}}
.city-head{{display:flex;align-items:baseline;justify-content:space-between;
           border-bottom:.6pt solid #121212;padding-bottom:2.5mm;margin-bottom:6mm}}
.city-head h2{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-weight:600;
              font-size:17pt;letter-spacing:-.025em;text-transform:uppercase}}
.city-head p{{margin:0;color:#6b6a66}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:9mm 10mm}}
.work{{margin:0;page-break-inside:avoid;break-inside:avoid}}
.plate{{height:62mm;display:flex;align-items:center;justify-content:center;
       background:#f3f1ea;padding:3mm;margin-bottom:3mm}}
.plate img{{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;
           box-shadow:0 1.4mm 3.5mm rgba(0,0,0,.26)}}
.work h3{{font-size:11.5pt;line-height:1.2}}
.work .yr{{color:#6b6a66}}
.work .series{{margin:.6mm 0 2mm;font-style:italic;font-size:9.5pt;color:#3a3a38}}
.work dl div{{padding:1.1mm 0}}
.price{{font-family:'PlexMono',monospace;font-size:9pt;letter-spacing:.04em}}

/* closing */
.close{{page-break-before:always}}
.close h2{{font-size:20pt;margin-bottom:6mm}}
.terms{{display:grid;grid-template-columns:1fr 1fr;gap:10mm;margin-top:8mm}}
.terms p{{margin:0 0 3mm}}
.foot{{margin-top:12mm;border-top:.4pt solid rgba(18,18,18,.3);padding-top:3mm;
      display:flex;justify-content:space-between;color:#6b6a66}}
</style></head><body>

<div class="cover">
  <div class="cover-img"><img src="{cover_img}" alt=""></div>
  <div class="cover-body">
    <div>
      {addressed}
      <h1>Michael<br>Jacques</h1>
      <p class="sub">Available works — {e(' and '.join(cities))}</p>
    </div>
    <dl class="meta">
      <div><dt>Works available</dt><dd>{len(works)}</dd></div>
      <div><dt>Sizes</dt><dd>10&quot; to 50&quot;</dd></div>
      <div><dt>Price range</dt><dd>${total_low:,}&ndash;${total_high:,}</dd></div>
      <div><dt>Issued</dt><dd>{today}</dd></div>
    </dl>
  </div>
</div>

<section class="bio">
  <span class="mono label">About the artist</span>
  <p class="lede">Michael Jacques is an American painter based in Miami whose work explores the tension and harmony between the inner world and the natural landscape.</p>
  <div class="two">
    <div>
      <p>Self-taught and driven by a multidisciplinary background spanning design, creative strategy, and experiential art, Jacques approaches painting as a way to map the emotional architecture that sits beneath everyday life.</p>
      <p>His mixed-media practice blends figurative forms, abstract environments, and symbolic motifs from nature, creating compositions that feel both intimate and expansive. The work often integrates collage, layered texture, and bold yet restrained colour.</p>
    </div>
    <div>
      <p>The paintings read like snapshots of the subconscious — moments where human interiority meets the wider environment. They resonate with viewers drawn to introspection, symbolism, and contemporary surrealism.</p>
      <p>Jacques has built a growing collector base in the U.S., exhibiting in local shows and private placements while preparing new series for gallery and art-fair submission. Works are available directly from the studio, unframed or framed to specification.</p>
    </div>
  </div>

  <div class="two">
    <div>
      <span class="mono label">Selected exhibitions &amp; fairs</span>
      <dl>{shows}</dl>
    </div>
    <div class="summary">
      <span class="mono label">What's in this document</span>
      <dl>{summary}</dl>
      <p class="mono" style="margin-top:4mm;color:#6b6a66;text-transform:none;letter-spacing:.02em;font-size:8pt;line-height:1.6">
        Every piece listed is an original, one of one, signed on the reverse.
        Prices are studio prices and exclude shipping and framing.
      </p>
    </div>
  </div>
</section>

{cards}

<section class="close">
  <span class="mono label">Next steps</span>
  <h2>Happy to send anything you'd like to see in more detail.</h2>
  <div class="terms">
    <div>
      <span class="mono label">Viewing</span>
      <p>The Miami works can be seen at the studio by appointment. The New York pieces are available to view in the city on request.</p>
      <p>For any piece here I can send additional photography, a short video in natural light, and a scale mockup against your wall dimensions.</p>
    </div>
    <div>
      <span class="mono label">Placement &amp; commissions</span>
      <p>Series can be placed together as a set — several of these were painted as groups and hang well in sequence.</p>
      <p>Commissions are open for specific dimensions, palettes or site requirements, typically 36" and up, with sketches shared before work begins.</p>
    </div>
  </div>
  <dl style="margin-top:10mm;max-width:92mm">
    <div><dt>Email</dt><dd>{e(site['email'])}</dd></div>
    <div><dt>Phone</dt><dd>{e(site['phone'])}</dd></div>
    <div><dt>Instagram</dt><dd>@{e(site['instagram'])}</dd></div>
    <div><dt>Portfolio</dt><dd>michael-jacques.com</dd></div>
  </dl>
  <div class="foot mono"><span>Michael Jacques — Available Works</span><span>{today}</span></div>
</section>
</body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', help='name to print on the cover')
    ap.add_argument('--only', help='one city slug, e.g. new-york')
    ap.add_argument('--out', default='Michael-Jacques-Available-Works.pdf')
    a = ap.parse_args()

    site = json.load(open(ROOT / 'site.json'))
    works = collect(site, a.only)
    if not works:
        sys.exit('no available works matched')

    OUT.mkdir(exist_ok=True)
    html_path = OUT / '.availability.html'
    html_path.write_text(build_html(site, works, a.to), encoding='utf-8')

    chrome = next((c for c in CHROME if Path(c).exists()), None)
    if not chrome:
        sys.exit('no Chrome/Edge/Chromium found to print with')

    pdf = OUT / a.out
    subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={pdf}', html_path.as_uri()],
                   check=True, capture_output=True)
    shutil.rmtree(OUT / '.print', ignore_errors=True)

    cities = {}
    for w in works:
        cities[w['city']] = cities.get(w['city'], 0) + 1
    print(f'{pdf}  ({pdf.stat().st_size/1e6:.1f} MB)')
    print('  ' + ', '.join(f'{n} in {c}' for c, n in cities.items()))


if __name__ == '__main__':
    main()
