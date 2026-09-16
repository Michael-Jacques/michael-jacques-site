/* Michael Jacques studio site — small progressive-enhancement layer. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  /* mobile menu */
  const menuBtn = $('.menu-btn'), panel = $('.menu-panel');
  if (menuBtn && panel) {
    const toggle = (open) => { panel.classList.toggle('open', open); document.body.style.overflow = open ? 'hidden' : ''; menuBtn.setAttribute('aria-expanded', String(open)); };
    menuBtn.addEventListener('click', () => toggle(!panel.classList.contains('open')));
    $$('.menu-close, .menu-panel nav a', panel).forEach(el => el.addEventListener('click', () => toggle(false)));
  }

  /* hero carousel — the painting you leave expands into the ground behind the next one */
  const heroCard = $('.hero-card'), plates = $('.hero__plates');
  if (heroCard && plates) {
    const slides = $$('a', heroCard);
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    // slides past the first two carry their urls in data attributes until needed
    const hydrate = (n) => {
      const im = slides[(n + slides.length) % slides.length].querySelector('img');
      if (im.dataset.src) {
        im.srcset = im.dataset.srcset || '';
        im.src = im.dataset.src;
        delete im.dataset.src; delete im.dataset.srcset;
      }
      return im;
    };
    const srcOf = (n) => { const im = hydrate(n); return im.currentSrc || im.src; };
    let i = 0, busy = false, pending = 0, auto = null;

    const setPlate = (src, animate) => {
      const d = document.createElement('div');
      d.className = 'hero__plate' + (animate ? ' is-entering' : '');
      d.style.backgroundImage = 'url("' + src + '")';
      plates.appendChild(d);
      // keep the outgoing plate underneath until the new one has covered it
      while (plates.children.length > 2) plates.removeChild(plates.firstChild);
    };

    const go = (dir) => {
      if (slides.length < 2) return;
      if (busy) { pending = dir; return; }   // a click landing mid-transition still counts
      busy = true;
      const from = i;
      i = (i + dir + slides.length) % slides.length;
      setPlate(srcOf(from), !reduce);
      slides[from].classList.remove('active', 'is-zooming');
      hydrate(i); hydrate(i + 1);            // current, and the one queued behind it
      const next = slides[i];
      next.classList.add('active');
      if (!reduce) { void next.offsetWidth; next.classList.add('is-zooming'); }
      setTimeout(() => {
        busy = false;
        if (pending) { const d = pending; pending = 0; go(d); }
      }, reduce ? 260 : 820);
    };

    heroCard.addEventListener('animationend', (e) => {
      if (e.animationName === 'card-in') e.target.closest('a')?.classList.remove('is-zooming');
    });

    // the ground starts on the painting just before the first card
    if (slides.length) { setPlate(srcOf(slides.length - 1), false); hydrate(1); }

    // advance on its own every 5s; a click just restarts the clock
    const restart = () => {
      clearInterval(auto);
      auto = slides.length > 1 ? setInterval(() => go(1), 5000) : null;
    };
    const step = (dir) => { go(dir); restart(); };
    restart();

    // a backgrounded tab would otherwise queue up a burst of advances
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { clearInterval(auto); auto = null; } else restart();
    });

    $$('.hero-arrow').forEach(btn => btn.addEventListener('click', () =>
      step(btn.classList.contains('hero-arrow--prev') ? -1 : 1)));
    heroCard.closest('.hero__left')?.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault(); step(e.key === 'ArrowLeft' ? -1 : 1);
    });
  }

  /* explore-by-series hover list */
  const sl = $('.series-list');
  if (sl) {
    const items = $$('li', sl), imgs = $$('.series-visual__frame img'), texts = $$('.series-visual__text p');
    const set = (k) => {
      items.forEach(li => li.classList.toggle('active', li.dataset.key === k));
      imgs.forEach(im => im.classList.toggle('active', im.dataset.key === k));
      texts.forEach(p => p.classList.toggle('active', p.dataset.key === k));
    };
    items.forEach(li => { li.addEventListener('mouseenter', () => set(li.dataset.key)); li.addEventListener('focusin', () => set(li.dataset.key)); });
  }

  /* collecting radio list */
  const rl = $('.radio-list');
  if (rl) {
    const btns = $$('button', rl), bodies = $$('.collect__body > div');
    btns.forEach(b => b.addEventListener('click', () => {
      btns.forEach(x => x.classList.toggle('active', x === b));
      bodies.forEach(d => d.classList.toggle('active', d.dataset.key === b.dataset.key));
    }));
  }

  /* explore links hover descriptions */
  const el = $('.explore-list');
  if (el) {
    const descs = $$('.explore-desc p');
    $$('a', el).forEach(a => a.addEventListener('mouseenter', () => descs.forEach(p => p.classList.toggle('active', p.dataset.key === a.dataset.key))));
  }

  /* catalogue filters */
  const grid = $('.grid[data-filterable]');
  if (grid) {
    const cards = $$('.card', grid), count = $('.filters .count'), empty = $('.grid .empty');
    const inputs = $$('.filters input');
    const apply = () => {
      const active = {};
      inputs.filter(i => i.checked).forEach(i => (active[i.name] = active[i.name] || []).push(i.value));
      let n = 0;
      cards.forEach(c => {
        const ok = Object.keys(active).every(k => active[k].includes(c.dataset[k]));
        c.hidden = !ok; if (ok) n++;
      });
      if (count) count.textContent = n + (n === 1 ? ' Result' : ' Results');
      if (empty) empty.hidden = n > 0;
    };
    inputs.forEach(i => i.addEventListener('change', apply));
    const clear = $('.filters .clear');
    if (clear) clear.addEventListener('click', (e) => { e.preventDefault(); inputs.forEach(i => i.checked = false); apply(); });
    // preselect from ?series=slug
    const q = new URLSearchParams(location.search);
    q.forEach((v, k) => { const inp = inputs.find(i => i.name === k && i.value === v); if (inp) inp.checked = true; });
    apply();
  }

  /* work detail view toggle */
  const vt = $('.view-toggle');
  if (vt) {
    const btns = $$('button', vt), views = $$('.work-view__stage > div');
    btns.forEach(b => b.addEventListener('click', () => {
      btns.forEach(x => x.classList.toggle('active', x === b));
      views.forEach(v => v.classList.toggle('active', v.dataset.key === b.dataset.key));
    }));
  }

  /* see-also tabs */
  const tabs = $('.see-also .tabs');
  if (tabs) {
    const btns = $$('button', tabs), rows = $$('.see-also .cards');
    btns.forEach(b => b.addEventListener('click', () => {
      btns.forEach(x => x.classList.toggle('active', x === b));
      rows.forEach(r => r.hidden = r.dataset.key !== b.dataset.key);
    }));
  }

  /* newsletter: posts to the form action if one is configured, otherwise opens a mail draft */
  const nf = $('.news-form');
  if (nf) nf.addEventListener('submit', (e) => {
    if (nf.getAttribute('action')) return; // real endpoint configured
    e.preventDefault();
    const email = $('input[type=email]', nf).value.trim();
    const to = nf.dataset.mailto;
    location.href = `mailto:${to}?subject=${encodeURIComponent('Add me to the studio list')}&body=${encodeURIComponent('Please add ' + email + ' to the newsletter.')}`;
    $('.thanks', nf.parentElement).style.display = 'block';
  });

  /* back to top */
  $$('[data-top]').forEach(a => a.addEventListener('click', (e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }));

  /* reveal on scroll */
  const rv = $$('.rv');
  if ('IntersectionObserver' in window && rv.length) {
    const vh = window.innerHeight;
    const io = new IntersectionObserver((es) => es.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } }), { rootMargin: '0px 0px -8% 0px' });
    rv.forEach(el => {
      // anything already on screen at load appears immediately; only later content animates in
      if (el.getBoundingClientRect().top < vh) { el.classList.add('now'); io.unobserve(el); }
      else io.observe(el);
    });
  } else rv.forEach(el => el.classList.add('in'));
})();
