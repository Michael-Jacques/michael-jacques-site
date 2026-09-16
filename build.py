#!/usr/bin/env python3
"""Static site generator for michael-jacques.com.

Edit site.json (content) and the templates below, then run:  python3 build.py
Outputs: index.html, work.html, about.html, contact.html, series/<slug>.html, works/<slug>.html
"""
import json, os, html, re, shutil
from pathlib import Path

ROOT = Path(__file__).parent
S = json.load(open(ROOT / 'site.json'))
def _v(f):
    try: return str(int(os.path.getmtime(ROOT / f)))
    except OSError: return '1'
VCSS, VJS = _v('styles.css'), _v('main.js')
YEAR = '2026'
ALL = [dict(w, series=s) for s in S['series'] for w in s['works']]
assert len({w['slug'] for w in ALL}) == len(ALL), 'work slugs must be unique'
e = html.escape

FONTS = ('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap')

def img(w, size=''):
    return f"/assets/work/{w['series']['slug']}/{w['slug']}{size}.webp"

def mailto(w=None):
    sub = f"Inquiry: {w['title']} ({w['series']['name']})" if w else 'Studio inquiry'
    return f"mailto:{S['email']}?subject={sub.replace(' ', '%20')}"

# ---------------------------------------------------------------- chrome
def head(title, desc, canonical, og=None):
    og = og or '/assets/hero/under.webp'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{S['domain']}{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{S['domain']}{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/styles.css?v={VCSS}">
</head>
<body>
"""

def header(current='', blend=False):
    def nav(href, label):
        cur = ' aria-current="page"' if current == href else ''
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""<header class="site-header{' blend' if blend else ''}">
  <nav class="nav" aria-label="Primary">{nav('/work.html','Work')}{nav('/about.html','About')}{nav('/contact.html','Contact')}</nav>
  <a class="brand" href="/">Michael Jacques</a>
  <a class="brand brand--mark" href="/" aria-label="Michael Jacques">MJ</a>
  <div class="nav-right">
    <a href="https://www.instagram.com/{S['instagram']}/" target="_blank" rel="noopener">Instagram</a>
    <a href="{mailto()}">Inquire</a>
  </div>
  <button class="menu-btn" aria-expanded="false" aria-controls="menu">Menu</button>
</header>
<div class="menu-panel" id="menu">
  <div class="menu-top"><a class="brand" href="/">Michael Jacques</a><button class="menu-btn menu-close">Close</button></div>
  <nav>
    <a href="/work.html">All Work <small>{len(ALL)} paintings · 4 series</small></a>
    {''.join(f'<a href="/series/{s["slug"]}.html">{e(s["name"])} <small>{s["year"]} · {len(s["works"])} works</small></a>' for s in S['series'])}
    <a href="/about.html">About <small>Bio, statement, exhibitions</small></a>
    <a href="/contact.html">Contact <small>Press &amp; inquiries</small></a>
  </nav>
  <div class="menu-foot mono"><a href="https://www.instagram.com/{S['instagram']}/">@{S['instagram']}</a><a href="mailto:{S['email']}">{S['email']}</a></div>
</div>
"""

def newsletter():
    return f"""<section class="newsletter">
  <div class="newsletter__bg" aria-hidden="true"></div>
  <div class="news-card rv">
    <h2>Become a collector</h2>
    <p>A studio note every month or so. New paintings before they go anywhere else, show dates, and the occasional look at what’s on the easel. Short, and only when there’s something to say.</p>
    <p class="fine">(Collectors on the list see new work first.)</p>
    <form class="news-form" data-mailto="{S['email']}" method="post">
      <input type="email" name="email" placeholder="your email" required aria-label="Email address">
      <button type="submit">subscribe →</button>
    </form>
    <p class="thanks">Thanks. You’re on the list.</p>
  </div>
</section>
"""

def footer():
    return f"""<footer class="site-footer">
  <div class="foot-grid">
    <div><a href="https://www.instagram.com/{S['instagram']}/" target="_blank" rel="noopener">Instagram</a><br><a href="mailto:{S['email']}">{S['email']}</a><br><a href="tel:{re.sub('[^0-9+]','',S['phone'])}">{S['phone']}</a></div>
    <div><a href="/work.html">All work</a><br><a href="/about.html">About</a><br><a href="/contact.html">Contact</a></div>
    <div class="right">© {YEAR}, Michael Jacques<br>Miami, FL<br><a href="#" data-top>↑ back to top</a></div>
  </div>
  <div class="foot-script" aria-hidden="true">Michael Jacques</div>
</footer>
<script src="/main.js?v={VJS}"></script>
</body>
</html>
"""

# ---------------------------------------------------------------- pieces
def card(w, price=True):
    p = ''
    if price:
        p = f'<div class="card__price">{"<span class=sold>Sold</span>" if w["sold"] else e(w["price"])}</div>'
    return f"""<a class="card rv" href="/works/{w['slug']}.html" data-series="{w['series']['slug']}" data-year="{w['year']}" data-status="{'sold' if w['sold'] else 'available'}" data-size="{size_bucket(w)}">
  <div class="card__img"><img src="{img(w,'-800')}" srcset="{img(w,'-800')} 800w, {img(w)} 1500w" sizes="(max-width:820px) 50vw, 25vw" width="{w['w']}" height="{w['h']}" alt="{e(w['title'])}, {w['year']}, {e(w['medium'])}" loading="lazy"></div>
  <div class="card__meta"><div class="card__title">{e(w['title'])}</div><div class="card__sub">{e(w['series']['name'])}</div>{p}</div>
</a>"""

def size_bucket(w):
    a, b = [int(x) for x in re.findall(r'\d+', w['size'])[:2]]
    m = max(a, b)
    return 'small' if m < 30 else ('medium' if m < 48 else 'large')

def cards(ws, price=True):
    return '<div class="cards">' + ''.join(card(w, price) for w in ws) + '</div>'

# ---------------------------------------------------------------- pages
def page_home():
    new = S['series'][0]                     # newest series — drives the "New Work" row
    hero = next((s for s in S['series'] if s['slug'] == S.get('hero_series')), new)
    slides = ''.join(
        f'<a href="/works/{w["slug"]}.html" class="{"active" if i == 0 else ""}"><span class="hero-cap">{i+1}/{len(hero["works"])} {e(w["title"])}</span>'
        # only the first two are fetched up front; main.js loads the rest just before they show
        f'<img {"src" if i < 2 else "data-src"}="{img(w,"-800")}" {"srcset" if i < 2 else "data-srcset"}="{img(w,"-800")} 800w, {img(w)} 1500w" '
        f'sizes="(max-width:820px) 78vw, min(33vw, 470px)" width="{w["w"]}" height="{w["h"]}" alt="{e(w["title"])}"'
        f'{" fetchpriority=high" if i == 0 else ""}></a>'
        for i, w in enumerate([dict(w, series=hero) for w in hero['works']]))
    series_items = ''.join(
        f'<li data-key="{s["slug"]}" class="{"active" if i == 0 else ""}"><a href="/series/{s["slug"]}.html">{e(s["name"])}<small>{s["year"]} · {len(s["works"])} works</small></a></li>'
        for i, s in enumerate(S['series']))
    series_imgs = ''.join(f'<img data-key="{s["slug"]}" class="{"active" if i == 0 else ""}" src="/assets/{s["install"]}.webp" alt="{e(s["name"])}, installation view" loading="lazy">' for i, s in enumerate(S['series']))
    series_txt = ''.join(f'<p data-key="{s["slug"]}" class="mono-p {"active" if i == 0 else ""}">{e(s["blurb"])}</p>' for i, s in enumerate(S['series']))
    coll_btns = ''.join(f'<li><button data-key="{c["key"]}" class="{"active" if i == 0 else ""}">{e(c["title"])}</button></li>' for i, c in enumerate(S['collecting']))
    coll_body = ''.join(f'<div data-key="{c["key"]}" class="{"active" if i == 0 else ""}"><p>{e(c["text"])}</p><a class="u" href="{mailto()}">Get in touch</a></div>' for i, c in enumerate(S['collecting']))
    explore = [('work', '/work.html', 'All Work', f'Every painting from all four series, {len(ALL)} in total. Filter by series, year, size, or availability.'),
               ('series', f'/series/{new["slug"]}.html', 'Under My Own Skin', 'The 2025 series. Four new paintings, two still available.'),
               ('shows', '/about.html#shows', 'Exhibitions', 'Fairs and shows from Miami to Brooklyn to Los Angeles, 2022 to now.'),
               ('about', '/about.html', 'About the Artist', 'Self-taught, Miami-based, built from a background in design and experiential art.'),
               ('contact', '/contact.html', 'Contact', 'Press, collectors, designers, and studio visits. Email is fastest.')]
    ex_links = ''.join(f'<li><a data-key="{k}" href="{h}">{l}</a></li>' for k, h, l, d in explore)
    ex_desc = ''.join(f'<p data-key="{k}" class="mono-p {"active" if i == 0 else ""}">{d}</p>' for i, (k, h, l, d) in enumerate(explore))
    stmt_bg = '/assets/work/days-are-short/take-me-higher.webp' if False else '/assets/work/everything/take-me-higher.webp'
    return head('Michael Jacques · Painter, Miami', 'Original paintings by Michael Jacques. Figurative, abstract, and symbolic work that maps the emotional architecture beneath everyday life. Four series, available directly from the studio in Miami.', '/') + header('/', blend=True) + f"""
<section class="hero">
  <div class="hero__left">
    <div class="hero__plates" aria-hidden="true"></div>
    <div class="hero__ink" aria-hidden="true"></div>
    <div class="hero-card">{slides}</div>
    <button class="hero-arrow hero-arrow--prev" aria-label="Previous painting">&#8592;</button>
    <button class="hero-arrow hero-arrow--next" aria-label="Next painting">&#8594;</button>
  </div>
  <div class="hero__right">
    <div class="hero__bg" aria-hidden="true"></div>
    <div class="hero__copy">
      <h1>{e(S['hero_statement'])}</h1>
      <a class="hero-link u" href="/work.html">view the work</a>
    </div>
  </div>
  <div class="hero__name" aria-hidden="true"><span>Michael</span> <span>Jacques</span></div>
</section>

<section class="section">
  <div class="section-head rv">
    <div><h2>New Work</h2><p class="mono-p">{e(new['name'])}, {new['year']}. {len(new['works'])} paintings, acrylic on canvas.</p></div>
    <a class="btn" href="/series/{new['slug']}.html">See the series</a>
  </div>
  {cards([dict(w, series=new) for w in new['works']])}
</section>

<section class="banner">
  <div class="banner__bg" style="background-image:url({stmt_bg})" aria-hidden="true"></div>
  <div class="rv"><span class="label">Statement</span>
  <h2>{e(S['manifesto'])} <a class="after u" href="/about.html">About the artist</a></h2></div>
</section>

<section class="section series-explore">
  <div>
    <span class="label">Explore by series</span>
    <ul class="series-list">{series_items}</ul>
  </div>
  <div class="series-visual rv">
    <div class="series-visual__frame">{series_imgs}</div>
    <div class="series-visual__text">{series_txt}</div>
  </div>
</section>

<section class="collect">
  <div class="collect__bg" aria-hidden="true"></div>
  <div class="collect__side rv"><h2>For collectors:</h2><ul class="radio-list">{coll_btns}</ul></div>
  <div class="collect__body rv">{coll_body}</div>
</section>

<section class="explore">
  <span class="label">Explore the studio</span>
  <ul class="explore-list rv">{ex_links}</ul>
  <div class="explore-desc">{ex_desc}</div>
</section>
{newsletter()}{footer()}"""

def page_work():
    opts = lambda name, vals: ''.join(f'<label><input type="checkbox" name="{name}" value="{v}">{l}</label>' for v, l in vals)
    years = sorted({str(w['year']) for w in ALL}, reverse=True)
    filters = f"""
<details class="filter" open><summary>By series</summary><div class="opts">{opts('series', [(s['slug'], s['name']) for s in S['series']])}</div></details>
<details class="filter"><summary>By year</summary><div class="opts">{opts('year', [(y, y) for y in years])}</div></details>
<details class="filter"><summary>By availability</summary><div class="opts">{opts('status', [('available','Available'),('sold','Sold')])}</div></details>
<details class="filter"><summary>By size</summary><div class="opts">{opts('size', [('large','Large · 48" and up'),('medium','Medium · 30–40"'),('small','Small · under 30"')])}</div></details>
<a class="clear" href="#">Clear filters</a>"""
    return head('All Work · Michael Jacques', f'{len(ALL)} original paintings across four series. Browse by series, year, size, and availability.', '/work.html') + header('/work.html', blend=True) + f"""
<section class="banner" style="min-height:52svh">
  <div class="banner__bg" style="background-image:url(/assets/work/days-are-short/look-up-for-once.webp)" aria-hidden="true"></div>
  <div class="rv"><span class="label">All work</span><h1>Every painting, all four series. If you’d rather browse without a plan, start here.</h1></div>
</section>
<section class="catalogue">
  <aside class="filters"><div class="count">{len(ALL)} Results</div>{filters}</aside>
  <div class="grid" data-filterable>{''.join(card(w) for w in ALL)}<p class="empty" hidden>Nothing matches those filters. Try fewer.</p></div>
</section>
{footer()}"""

def page_series(i, s):
    ws = [dict(w, series=s) for w in s['works']]
    nxt = S['series'][(i + 1) % len(S['series'])]
    avail = sum(1 for w in ws if not w['sold'])
    sizes = sorted({w['size'] for w in ws}, key=lambda x: -int(re.findall(r'\d+', x)[0]))
    return head(f'{s["name"]} · Michael Jacques', s['blurb'], f'/series/{s["slug"]}.html', f'/assets/{s["install"]}.webp') + header('/work.html', blend=True) + f"""
<section class="series-hero">
  <div class="series-hero__bg" style="background-image:url(/assets/{s['install']}.webp)" aria-hidden="true"></div>
  <div class="rv"><span class="label">Series · {s['year']}</span><h1>{e(s['name'])}</h1></div>
</section>
<section class="series-intro">
  <p class="rv">{e(s['blurb'])}</p>
  <div class="facts rv">
    <div><span>Works</span><span>{len(ws)} paintings</span></div>
    <div><span>Year</span><span>{s['year']}</span></div>
    <div><span>Medium</span><span>{e(ws[0]['medium'].capitalize())}</span></div>
    <div><span>Sizes</span><span>{e(', '.join(sizes))}</span></div>
    <div><span>Available</span><span>{avail} of {len(ws)}</span></div>
  </div>
</section>
<section class="series-grid"><div class="grid">{''.join(card(w) for w in ws)}</div></section>
<a class="next-series" href="/series/{nxt['slug']}.html"><span class="label">Next series</span><h3>{e(nxt['name'])}</h3><span class="arrow">→</span></a>
{newsletter()}{footer()}"""

def page_work_detail(w):
    s = w['series']
    same = [x for x in ALL if x['series']['slug'] == s['slug'] and x['slug'] != w['slug']][:4]
    other = [x for x in ALL if x['series']['slug'] != s['slug'] and not x['sold']][:4]
    price = '<span class="sold">Sold</span>' if w['sold'] else e(w['price'])
    cta = (f'<a class="btn btn--fill" href="{mailto(w)}">Inquire →</a><small>Replies within a day. Shipping quoted per piece.</small>' if not w['sold']
           else f'<a class="btn" href="{mailto(w)}">Ask about similar work →</a><small>This painting has found a home.</small>')
    return head(f'{w["title"]} ({w["year"]}) · Michael Jacques', f'{w["title"]}, {w["year"]}. {w["medium"].capitalize()}, {w["size"]}. From the series {s["name"]}.', f'/works/{w["slug"]}.html', img(w)) + header('/work.html', blend=True) + f"""
<section class="work-hero">
  <div class="work-view">
    <div class="hero__ink" aria-hidden="true"></div>
    <div class="work-view__stage">
      <div class="active" data-key="painting"><img src="{img(w,'-800')}" srcset="{img(w,'-800')} 800w, {img(w)} 1500w" sizes="(max-width:820px) 92vw, min(46vw, 640px)" width="{w['w']}" height="{w['h']}" alt="{e(w['title'])}, {w['year']}, {e(w['medium'])}, {e(w['size'])}"></div>
      <div class="room" data-key="room"><img src="/assets/{s['install']}.webp" alt="{e(s['name'])}, installation view" loading="lazy"></div>
    </div>
    <div class="view-toggle"><button class="active" data-key="painting">Painting</button><button data-key="room">In the room</button></div>
  </div>
  <div class="work-panel">
    <div class="work-panel__bg" style="background-image:url({img(w,'-800')})" aria-hidden="true"></div>
    <dl class="spec rv">
      <div class="spec-row"><dt>Title</dt><dd class="title">{e(w['title'])}</dd></div>
      <div class="spec-row"><dt>Series</dt><dd class="ital"><a href="/series/{s['slug']}.html">{e(s['name'])}</a></dd></div>
      <div class="spec-row"><dt>Year</dt><dd>{w['year']}</dd></div>
      <div class="spec-row"><dt>Medium</dt><dd>{e(w['medium'].capitalize())}</dd></div>
      <div class="spec-row"><dt>Size</dt><dd>{e(w['size'])}</dd></div>
      <div class="spec-row"><dt>Palette</dt><dd><span class="swatches">{''.join(f'<i style="background:{c}"></i>' for c in w['palette'])}</span></dd></div>
      <div class="spec-row"><dt>Price</dt><dd class="price">{price}</dd></div>
      <div class="spec-body"><p>{e(s['blurb'])}</p><p>Original, one of one, signed on the back. Ships from Miami, stretched and ready to hang.</p></div>
      <div class="spec-cta">{cta}</div>
    </dl>
  </div>
</section>
<section class="see-also">
  <div class="section-head"><h2>See also</h2>
    <div class="tabs"><button class="active" data-key="same">More in this series</button><button data-key="other">Available elsewhere</button></div></div>
  <div class="cards" data-key="same">{''.join(card(x) for x in same)}</div>
  <div class="cards" data-key="other" hidden>{''.join(card(x) for x in other)}</div>
</section>
{footer()}"""

def page_about():
    rows = ''.join(f'<div class="row"><dt>{sh["year"]}</dt><dd>{e(sh["name"])}</dd><dd class="place">{e(sh["place"])}</dd></div>' for sh in S['shows'])
    bio = ''.join(f'<p>{e(p)}</p>' for p in S['bio'])
    return head('About · Michael Jacques', S['bio'][0], '/about.html', '/assets/hero/about-portrait.webp') + header('/about.html') + f"""
<section class="page-top">
  <span class="label">About the artist</span>
  <p class="lede rv">{e(S['bio'][0].split('. ')[0])}. Self-taught, and drawn to the moments where human interiority meets the wider environment.</p>
</section>
<section class="about-cols">
  <span class="label">Bio + statement</span>
  <div class="col rv"><h3>Bio</h3>{bio}</div>
  <div class="col rv"><h3>Artist statement</h3><p>{e(S['statement'])}</p></div>
</section>
<div class="portrait" style="background-image:url(/assets/hero/about-portrait.webp)" role="img" aria-label="Michael Jacques in the studio"></div>
<section class="ledger" id="shows">
  <div class="rv"><h2>Shows &amp; Fairs</h2><p class="mono-p">Local shows, art fairs, and private placements, with new series in progress for gallery and fair submission.</p></div>
  <dl class="rv">{rows}</dl>
</section>
{newsletter()}{footer()}"""

def page_contact():
    return head('Contact · Michael Jacques', 'Press and general inquiries for painter Michael Jacques, Miami.', '/contact.html') + header('/contact.html') + f"""
<section class="page-top">
  <span class="label">Contact</span>
  <p class="lede rv">Press, collectors, designers, and anyone who wants to see a painting in person. Email is the fastest way in.</p>
</section>
<section class="contact">
  <dl class="rv">
    <div class="row"><dt>Email</dt><dd><a href="mailto:{S['email']}">{S['email']}</a></dd></div>
    <div class="row"><dt>Phone</dt><dd><a href="tel:{re.sub('[^0-9+]','',S['phone'])}">{S['phone']}</a></dd></div>
    <div class="row"><dt>Instagram</dt><dd><a href="https://www.instagram.com/{S['instagram']}/" target="_blank" rel="noopener">@{S['instagram']}</a></dd></div>
    <div class="row"><dt>Studio</dt><dd>Miami, FL · by appointment</dd></div>
  </dl>
  <div class="aside rv"><p>For available work, send the title and I’ll reply with details, a studio video, and a shipping quote. For commissions and trade projects, a few lines about the space and the timeline is the best place to start.</p><p><a class="btn" href="{mailto()}">Start an inquiry →</a></p></div>
</section>
{footer()}"""

# ---------------------------------------------------------------- write
def write(path, content):
    """Write a page, rewriting root-absolute URLs to paths relative to that page
    so the site works from a subfolder, a file:// copy, or any host."""
    if not path.endswith('.html'):
        p = ROOT / path; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8'); return
    depth = path.count('/')
    prefix = '../' * depth
    content = content.replace('href="/"', f'href="{prefix}index.html"')
    if depth:
        content = re.sub(r'(href="|src="|srcset="|url\()/', lambda m: m.group(1) + prefix, content)
        content = re.sub(r'(, )/(assets/)', lambda m: m.group(1) + prefix + m.group(2), content)
    else:
        content = re.sub(r'(href="|src="|srcset="|url\()/(?!/)', lambda m: m.group(1), content)
        content = re.sub(r'(, )/(assets/)', lambda m: m.group(1) + m.group(2), content)
    p = ROOT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding='utf-8')

write('index.html', page_home())
write('work.html', page_work())
write('about.html', page_about())
write('contact.html', page_contact())
for i, s in enumerate(S['series']): write(f'series/{s["slug"]}.html', page_series(i, s))
for w in ALL: write(f'works/{w["slug"]}.html', page_work_detail(w))
# Only emit CNAME once DNS actually points here. Writing it early makes GitHub
# redirect the github.io preview url to the custom domain, which still serves
# the old host — so the new site looks broken and can't be reviewed.
if S.get('custom_domain'):
    write('CNAME', S['custom_domain'] + '\n')
write('.nojekyll', '')
write('robots.txt', f"User-agent: *\nAllow: /\nSitemap: {S['domain']}/sitemap.xml\n")

urls = ['/', '/work.html', '/about.html', '/contact.html'] \
     + [f'/series/{s_["slug"]}.html' for s_ in S['series']] \
     + [f'/works/{w["slug"]}.html' for w in ALL]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + ''.join(f'  <url><loc>{S["domain"]}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
write('assets/favicon.svg', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#f9f8f2"/><text x="32" y="44" text-anchor="middle" font-family="Georgia,serif" font-style="italic" font-size="34" fill="#121212">MJ</text></svg>')
print(f'built: 4 pages + {len(S["series"])} series + {len(ALL)} works')
