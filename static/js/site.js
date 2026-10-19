(() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const search = document.querySelector('#search');
  const clear = document.querySelector('.clear-search');
  if (search && clear) {
    search.addEventListener('input', () => { clear.hidden = !search.value; });
    clear.addEventListener('click', event => {
      event.preventDefault(); search.value = ''; search.focus(); search.form.requestSubmit();
    });
  }
  const menu = document.querySelector('.mobile-menu');
  if (menu) {
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape') { menu.open = false; menu.querySelector('summary').focus(); }
    });
    document.addEventListener('click', event => { if (!menu.contains(event.target)) menu.open = false; });
  }

  // Media only runs while it can be watched. Non-hero clips require an explicit play.
  const clips = [...document.querySelectorAll('video')];
  const visibility = new IntersectionObserver(entries => entries.forEach(entry => {
    if (!entry.isIntersecting) entry.target.pause();
  }), {threshold: 0.15});
  clips.forEach(video => {
    if (!video.classList.contains('scene-video')) visibility.observe(video);
    video.addEventListener('play', () => clips.forEach(other => { if (other !== video) other.pause(); }));
    video.addEventListener('error', () => {
      if (video.parentElement.querySelector('.media-error')) return;
      const note = document.createElement('p'); note.className = 'media-error';
      note.textContent = 'Не удалось загрузить видео. Попробуйте обновить страницу.';
      video.after(note);
    });
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) clips.forEach(v => v.pause()); });

  const cover = document.querySelector('[data-cover]');
  if (cover) {
    const slides = [...cover.querySelectorAll('[data-cover-slide]')];
    const navigation = cover.querySelector('.cover-navigation');
    if (slides.length && navigation) {
      let current = 0, timer, pointerStart, suppressClickUntil = 0;
      const setCurrent = (index, announce = true) => {
        const next = (index + slides.length) % slides.length;
        if (next === current) return;
        clearTimeout(timer);
        slides.forEach(slide => slide.classList.remove('is-entering', 'is-leaving'));
        slides[current].classList.add('is-leaving');
        current = next;
        slides.forEach((slide, i) => {
          slide.classList.toggle('is-active', i === current);
          slide.inert = i !== current;
          slide.setAttribute('aria-hidden', String(i !== current));
          if (i === current) slide.querySelectorAll('img').forEach(image => { image.loading = 'eager'; });
        });
        slides[current].classList.add('is-entering');
        timer = setTimeout(() => slides.forEach(slide => slide.classList.remove('is-entering', 'is-leaving')), 850);
        cover.querySelectorAll('[data-cover-dot]').forEach(dot => dot.setAttribute('aria-pressed', String(Number(dot.dataset.coverDot) === current)));
        cover.querySelector('[data-cover-current]').textContent = String(current + 1).padStart(2, '0');
        if (announce) cover.querySelector('[data-cover-announcement]').textContent = `История ${current + 1} из ${slides.length}. ${slides[current].querySelector('.cover-story-link').textContent}`;
      };
      cover.classList.add('is-enhanced');
      slides.forEach((slide, i) => { slide.inert = i !== current; slide.setAttribute('aria-hidden', String(i !== current)); });
      navigation.hidden = slides.length < 2;
      navigation.querySelectorAll('button').forEach(button => { button.disabled = false; });
      cover.querySelectorAll('[data-cover-dot]').forEach(dot => dot.addEventListener('click', () => setCurrent(Number(dot.dataset.coverDot))));
      cover.querySelector('[data-cover-prev]').addEventListener('click', () => setCurrent(current - 1));
      cover.querySelector('[data-cover-next]').addEventListener('click', () => setCurrent(current + 1));
      navigation.addEventListener('keydown', event => {
        if (['ArrowLeft', 'ArrowRight'].includes(event.key)) { event.preventDefault(); setCurrent(current + (event.key === 'ArrowRight' ? 1 : -1)); }
      });
      const stage = cover.querySelector('.cover-stage');
      stage.addEventListener('pointerdown', event => {
        if (!event.target.closest('button, .cover-catalog, .cover-story-link')) pointerStart = {x:event.clientX,y:event.clientY};
      });
      stage.addEventListener('pointercancel', () => { pointerStart = null; });
      stage.addEventListener('pointerup', event => {
        if (!pointerStart) return;
        const dx = event.clientX - pointerStart.x, dy = event.clientY - pointerStart.y;
        pointerStart = null;
        if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.5) {
          suppressClickUntil = Date.now() + 400; setCurrent(current + (dx < 0 ? 1 : -1));
        }
      });
      stage.addEventListener('click', event => {
        if (Date.now() < suppressClickUntil) { event.preventDefault(); event.stopPropagation(); }
      }, true);
    }
  }

  const collectionLinks = [...document.querySelectorAll('[data-collection]')];
  const setCollection = key => {
    collectionLinks.forEach(link => {
      if (link.dataset.collection === key) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    document.querySelectorAll('[data-collection-panel]').forEach(panel => {
      panel.hidden = panel.dataset.collectionPanel !== key;
      if (!panel.hidden) panel.querySelectorAll('img').forEach(img => { img.loading = 'eager'; });
    });
  };
  collectionLinks.forEach(link => link.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); setCollection(link.dataset.collection);
    history.pushState({}, '', link.href);
  }));
  if (collectionLinks.length) window.addEventListener('popstate', () => {
    const key = new URLSearchParams(location.search).get('collection') || 'all';
    setCollection(collectionLinks.some(link => link.dataset.collection === key) ? key : 'all');
  });

  document.querySelectorAll('[data-gallery]').forEach(gallery => {
    const track = gallery.querySelector('.gallery-track');
    const slides = [...track.children];
    const controls = gallery.querySelector('.gallery-buttons');
    const count = gallery.querySelector('[data-gallery-count]');
    const previous = gallery.querySelector('[data-gallery-prev]');
    const next = gallery.querySelector('[data-gallery-next]');
    const index = () => Math.round(track.scrollLeft / track.clientWidth);
    const update = () => {
      const active = index(); count.textContent = `${active + 1} / ${slides.length}`;
      previous.disabled = active === 0; next.disabled = active >= slides.length - 1;
      slides.forEach((slide, i) => { if (i !== active) slide.querySelector('video')?.pause(); });
    };
    const go = i => track.scrollTo({left: Math.max(0, Math.min(slides.length - 1, i)) * track.clientWidth, behavior: motion.matches ? 'instant' : 'smooth'});
    controls.hidden = slides.length < 2;
    previous.addEventListener('click', () => go(index() - 1));
    next.addEventListener('click', () => go(index() + 1));
    track.addEventListener('scroll', update, {passive: true});
    track.addEventListener('keydown', event => {
      if (event.target.tagName === 'VIDEO') return;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') { event.preventDefault(); go(index() + (event.key === 'ArrowRight' ? 1 : -1)); }
    });
    gallery.querySelector('[data-watch-fitting]')?.addEventListener('click', event => {
      event.preventDefault(); go(slides.findIndex(s => s.classList.contains('video-slide'))); track.focus({preventScroll:true});
    });
    update();
  });
})();
