# michael-jacques.com

Static rebuild of the painting site, modelled on the layout and pacing of
objectandarchive.com: split hero with a rotating painting and an oversized
display name, mono captions over serif display type, a filterable catalogue,
and a spec-card detail page for each work.

## Publishing a change

The site is hosted on GitHub Pages out of `Michael-Jacques/michael-jacques-site`
and serves at https://www.michael-jacques.com. To make a change: edit
`site.json`, then run

```bash
./publish.sh "sold Higher Self"
```

That rebuilds, commits, and pushes. Pages redeploys on its own, usually within
a minute. Add `--images` when you've dropped new photos into `assets/src`.

## Editing

All content lives in `site.json`. Nothing is hard-coded in the templates except
layout.

Two settings pick which series the homepage shows, each by slug:

| Setting | Controls |
| --- | --- |
| `hero_series` | the paintings that rotate in the hero |
| `featured_series` | the row of cards under it |
| `featured_count` | how many of that series the row previews (from the end); omit for all |

The row is titled "New Work" only when it points at the newest series, and
"Selected Work" otherwise, so the heading never claims a 2023 series is new.
When it previews part of a series the subtitle says so, and the row sizes its
own columns, dropping to one full-width painting on a phone.
The "Explore the studio" link and its blurb follow `featured_series` too.

```bash
python3 build.py
```

That regenerates `index.html`, `work.html`, `about.html`, `contact.html`,
`series/<slug>.html`, `works/<slug>.html`, plus `sitemap.xml` and `robots.txt`.

- **Add a painting** — add an entry to the right series in `site.json`, drop the
  photo in `assets/src/work/<series>/<slug>.jpg`, then run the image step below.
- **Change a price or mark something sold** — edit `price` / `sold` in `site.json`.
- **Add a series** — add an object to `series` with a `slug`, `name`, `year`,
  `blurb`, and an `install` image path.

### Images

Photos are stored full-size in `assets/src/` and served as trimmed WebP at two
widths. To regenerate after adding a photo:

```bash
python3 tools/process_images.py
```

It auto-crops the white studio backdrop, writes `<slug>.webp` (1600px) and
`<slug>-800.webp`, and refreshes each work's `w`, `h`, and `palette` in
`site.json`.

## Local preview

```bash
python3 -m http.server 8791
```

Then open http://localhost:8791.

## Hosting

GitHub Pages, from `main` at the repo root. All URLs are relative, so the site
also runs from any other host or from a subfolder.

`CNAME` is generated only when `site.json` sets `custom_domain`. Leave that
field out while a domain still points somewhere else — GitHub redirects the
`github.io` preview URL to the custom domain, so setting it early makes the new
site impossible to review.

DNS lives at Squarespace (registrar and nameservers) and points here:

| Record | Host | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153, .109.153, .110.153, .111.153 |
| CNAME | www | `michael-jacques.github.io` |

### If HTTPS stops working

GitHub issues the certificate itself, but it can stall if the custom domain was
set before DNS pointed here. Clearing and re-setting the domain restarts it:

```bash
gh api -X PUT repos/Michael-Jacques/michael-jacques-site/pages -f cname=''
gh api -X PUT repos/Michael-Jacques/michael-jacques-site/pages -f cname='www.michael-jacques.com'
```

The same thing is available in the repo's Settings → Pages, by clearing the
Custom domain box, saving, retyping it, and saving again. Check progress with:

```bash
gh api repos/Michael-Jacques/michael-jacques-site/pages --jq '{status,cname,cert:.https_certificate.state}'
```

## Contact form

Every inquiry is addressed to the email in `site.json`. The contact form and the
newsletter both post to `form_endpoint`; leave it empty and they fall back to
opening a pre-filled mail draft, so nothing is ever a dead end.

**Mailto alone loses leads.** A visitor with no mail client configured clicks
Inquire and nothing happens, silently. Set an endpoint so the form actually
posts:

1. Get a free endpoint from [Formspree](https://formspree.io) or
   [Web3Forms](https://web3forms.com) using michaelsjacques@gmail.com.
2. Put the URL in `form_endpoint` in `site.json`.
3. `./publish.sh "turn on the contact form"`

Inquire on a painting links to `contact.html?work=<slug>`, and the form fills in
that painting's title, size and price from `assets/works.json`, so you know what
someone is asking about without them typing it.

The form carries a honeypot field for spam bots. If a send fails it shows the
email address rather than swallowing the message.

## Availability PDF

A tearsheet for a gallery, consultant or hotel art buyer: cover, bio, every
unsold work with its image, size, price and whereabouts, then contact details.

```bash
python3 tools/availability_pdf.py
python3 tools/availability_pdf.py --to "Hotel Art Advisory"
python3 tools/availability_pdf.py --only new-york
```

It writes to `exports/` (git-ignored) and regenerates from `site.json`, so
marking a piece sold and re-running is all it takes to refresh the list.

**Where each canvas physically is** lives in `LOCATIONS` at the top of
`tools/availability_pdf.py`. Miami is the default; only pieces that have
travelled need an entry.

Sizes are printed height × width and the orientation is checked against the
photograph, so a transposed entry is corrected rather than sent to a buyer.

Pick the cover painting with `--cover <slug>`; it defaults to `cover_work` in
`site.json`, then to Higher Self. Each painting is drawn at an exact width and
height in millimetres computed from its own aspect ratio — a percentage
max-height inside a flex box is unreliable in print, and left the image element
oversized so its drop shadow painted a grey slab around the artwork.
