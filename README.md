# michael-jacques.com

Static rebuild of the painting site, modelled on the layout and pacing of
objectandarchive.com: split hero with a rotating painting and an oversized
display name, mono captions over serif display type, a filterable catalogue,
and a spec-card detail page for each work.

## Editing

All content lives in `site.json`. Nothing is hard-coded in the templates except
layout.

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

## Deploying

All URLs are relative, so the site runs from any host or subfolder.

**GitHub Pages** (same setup as michaeljacques.work):

1. Create a repo and push this folder.
2. Settings → Pages → Deploy from a branch → `main` / `/ (root)`.
3. `CNAME` already contains `www.michael-jacques.com`.

**DNS** — the domain is currently on Squarespace and still points there. To move it:

| Record | Host | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | `<github-user>.github.io` |

Remove the existing Squarespace A records (198.185.159.144/145,
198.49.23.144/145) and the `ext-sq.squarespace.com` www CNAME first. Keep the
Squarespace site up until Pages serves correctly.

## Newsletter form

The signup form has no backend. It opens a pre-filled mail draft. To wire it to
a real service, put the endpoint in the form's `action` attribute in
`build.py` (`newsletter()`); `main.js` hands off to a real action when one is set.
