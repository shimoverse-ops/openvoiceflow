(() => {
  const hamburger = document.getElementById('navHamburger');
  const drawer = document.getElementById('navDrawer');
  if (!hamburger || !drawer || hamburger.dataset.navWired === 'true') return;

  hamburger.dataset.navWired = 'true';

  function setOpen(open) {
    hamburger.classList.toggle('active', open);
    drawer.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  hamburger.addEventListener('click', () => {
    setOpen(!drawer.classList.contains('open'));
  });

  drawer.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => setOpen(false));
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') setOpen(false);
  });
})();

(() => {
  const panel = document.querySelector('[data-download-recommendation]');
  const cta = document.querySelector('[data-recommended-download]');
  if (!panel || !cta) return;

  const builds = {
    arm64: {
      href: 'downloads/OpenVoiceFlow-0.5.22.dmg',
      title: 'Universal macOS DMG',
      subtitle: 'One universal native build for Apple Silicon and Intel Macs running macOS 14 or later.',
      badge: 'Universal macOS',
    },
    x86_64: {
      href: 'downloads/OpenVoiceFlow-0.5.22.dmg',
      title: 'Universal macOS DMG',
      subtitle: 'One universal native build for Apple Silicon and Intel Macs running macOS 14 or later.',
      badge: 'Universal macOS',
    },
  };

  const OS_LABELS = {
    windows: 'Windows',
    linux: 'Linux',
    chromeos: 'ChromeOS',
    android: 'Android',
    ios: 'iOS',
    ipados: 'iPadOS',
  };

  function trackRecommendation(result) {
    if (typeof window.va !== 'function') return;
    window.va('event', {
      name: 'download_recommendation_detected',
      data: {
        os: result.os || 'unknown',
        arch: result.arch || 'unknown',
        confidence: result.confidence || 'unknown',
        source: result.source || 'unknown',
        source_path: window.location.pathname || '/',
      },
    });
  }

  function normalizedArchitecture(value) {
    const arch = String(value || '').toLowerCase();
    if (['arm', 'arm64', 'aarch64'].includes(arch)) return 'arm64';
    if (['x86', 'x86_64', 'x64', 'amd64', 'ia32'].includes(arch)) return 'x86_64';
    return '';
  }

  function detectOS() {
    const ua = navigator.userAgent || '';
    const uaData = navigator.userAgentData;
    const platform = String((uaData && uaData.platform) || navigator.platform || '').toLowerCase();
    const isMacLike = platform.includes('mac') || /Macintosh|Mac OS X/i.test(ua);

    if (/android/i.test(ua) || platform.includes('android')) return 'android';
    if (/iphone|ipod/i.test(ua)) return 'ios';
    // iPad Safari masquerades as a Mac but reports multitouch.
    if (/ipad/i.test(ua) || (isMacLike && (navigator.maxTouchPoints || 0) > 1)) return 'ipados';
    if (/CrOS/.test(ua) || platform.includes('cros') || platform.includes('chrome os')) return 'chromeos';
    if (platform.includes('win') || /Windows/i.test(ua)) return 'windows';
    if (isMacLike) return 'macos';
    if (platform.includes('linux') || /Linux|X11/i.test(ua)) return 'linux';
    return 'unknown';
  }

  // Safari never exposes userAgentData, so on Macs fall back to the WebGL
  // renderer string: Apple Silicon reports "Apple M1/M2/..." GPUs, Intel
  // Macs report Intel/AMD GPUs. Masked strings ("Apple GPU") stay unknown.
  function webglArchitectureHint() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return '';
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      const renderer = String(
        ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER) || ''
      );
      if (/Apple M\d/i.test(renderer)) return 'arm64';
      if (/(intel|amd|radeon|iris|nvidia)/i.test(renderer)) return 'x86_64';
      return '';
    } catch (error) {
      return '';
    }
  }

  async function detectPlatform() {
    const os = detectOS();
    if (os !== 'macos' && os !== 'unknown') {
      return { os, arch: '', confidence: 'high', source: 'not-mac' };
    }

    const uaData = navigator.userAgentData;
    if (uaData && typeof uaData.getHighEntropyValues === 'function') {
      try {
        const values = await uaData.getHighEntropyValues(['architecture', 'platform', 'platformVersion']);
        const hintedPlatform = String(values.platform || uaData.platform || '').toLowerCase();
        const hintedArch = normalizedArchitecture(values.architecture);
        // Chromium reports the real macOS version here (unlike the UA string,
        // frozen at 10.15.7 for privacy — which is also why Safari visitors
        // can never be version-detected and rely on the visible fallback
        // link instead). Major 11–13 → the native app won't run; steer to
        // the retained 0.3.6 build rather than recommending a dead end.
        const major = parseInt(String(values.platformVersion || '').split('.')[0], 10);
        const legacyMac = Number.isFinite(major) && major >= 11 && major < 14;
        if (hintedPlatform.includes('mac') && hintedArch) {
          return { os: 'macos', arch: hintedArch, confidence: 'high', source: 'userAgentData', legacyMac };
        }
      } catch (error) {
        // Architecture hints are optional browser privacy surfaces.
      }
    }

    if (os === 'macos') {
      const webglArch = webglArchitectureHint();
      if (webglArch) {
        return { os: 'macos', arch: webglArch, confidence: 'medium', source: 'webgl' };
      }
      return { os: 'macos', arch: '', confidence: 'low', source: 'mac-undetected' };
    }

    return { os: 'unknown', arch: '', confidence: 'none', source: 'os-undetected' };
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function applyNotMacNotice(result) {
    const label = OS_LABELS[result.os] || 'this device';
    // Neutralize the CTA: an <a> without href is a non-interactive
    // placeholder, so a non-Mac visitor can't download a DMG that will
    // never run for them.
    cta.removeAttribute('href');
    cta.setAttribute('aria-disabled', 'true');
    cta.classList.remove('btn-primary');
    cta.classList.add('btn-unavailable');
    setText('downloadKicker', 'macOS required');
    setText('downloadArchBadge', 'macOS 14+ only');
    setText('downloadConfidence', 'Detection runs locally in your browser; nothing is uploaded.');
    // Mobile visitors get the truthful future ("in the works" — store links
    // land here when real), never a claim of availability.
    const mobile = result.os === 'ios' || result.os === 'ipados' || result.os === 'android';
    if (mobile) {
      cta.textContent = `Coming soon to ${label}`;
      setText('downloadTitle', `OpenVoiceFlow for ${label} is in the works`);
      setText(
        'downloadSubtitle',
        `Not in the store yet — this page will link it the day it ships. ` +
        'The Mac app is available today; both Mac builds stay below for a Mac you own.'
      );
      return;
    }
    cta.textContent = `Not available for ${label}`;
    setText('downloadTitle', 'OpenVoiceFlow is a Mac-only app');
    setText(
      'downloadSubtitle',
      `You appear to be browsing from ${label}. OpenVoiceFlow needs macOS 14 or newer — ` +
      `there is no ${label} version, and the Mac DMGs will not run on this device. ` +
      'Downloading for a Mac you own? Both builds stay available below.'
    );
  }

  function applyLegacyMacNotice(result) {
    setText('downloadKicker', 'Older macOS detected');
    setText('downloadArchBadge', 'macOS 12–13');
    setText('downloadConfidence', 'Detection runs locally in your browser; nothing is uploaded.');
    // The retained 0.3.6 fallback is Apple Silicon only. Handing it to a
    // legacy Intel Mac trades one dead-end download for another — for them
    // the honest answer is that no current build runs, and macOS 14 (which
    // every OpenVoiceFlow-capable Intel Mac can install) is the way in.
    if (result.arch === 'x86_64') {
      cta.removeAttribute('href');
      cta.setAttribute('aria-disabled', 'true');
      cta.classList.remove('btn-primary');
      cta.classList.add('btn-unavailable');
      cta.textContent = 'Needs macOS 14 on Intel Macs';
      setText('downloadTitle', 'Update to macOS 14 to run OpenVoiceFlow');
      setText(
        'downloadSubtitle',
        'The current app requires macOS 14, and the older 0.3.6 fallback is ' +
        'Apple Silicon only. Your Intel Mac can run OpenVoiceFlow after a free ' +
        'macOS update.'
      );
      return;
    }
    // Apple Silicon on macOS 12–13: the CTA becomes the build that runs.
    cta.href = 'downloads/OpenVoiceFlow-0.3.6-arm64.dmg';
    cta.textContent = 'Download for macOS 12–13 (v0.3.6)';
    setText('downloadTitle', 'Your Mac needs the 0.3.6 build');
    setText(
      'downloadSubtitle',
      'The current native app requires macOS 14. Your browser reports an earlier ' +
      'macOS, so the retained 0.3.6 Apple Silicon build is the one to grab — or ' +
      'update macOS to get the current app.'
    );
  }

  function applyDownloadRecommendation(result) {
    document.querySelectorAll('[data-arch]').forEach(row => {
      row.classList.toggle('is-recommended', row.dataset.arch === result.arch);
    });

    if (result.source === 'not-mac') {
      applyNotMacNotice(result);
      trackRecommendation(result);
      return;
    }

    if (result.legacyMac) {
      applyLegacyMacNotice(result);
      trackRecommendation(result);
      return;
    }

    if (result.arch && builds[result.arch]) {
      const build = builds[result.arch];
      cta.href = build.href;
      cta.textContent = `Download ${build.title}`;
      setText('downloadKicker', 'Recommended for your Mac');
      setText('downloadTitle', build.title);
      setText('downloadSubtitle', build.subtitle);
      setText('downloadArchBadge', build.badge);
      setText(
        'downloadConfidence',
        result.source === 'webgl'
          ? 'Detected from this Mac’s GPU renderer string.'
          : 'Detected from browser architecture hints.'
      );
      trackRecommendation(result);
      return;
    }

    cta.href = builds.arm64.href;
    cta.textContent = 'Download Apple Silicon DMG';
    setText('downloadKicker', 'Choose your Mac build');
    setText('downloadTitle', 'Pick Apple Silicon or Intel');
    setText('downloadSubtitle', 'This browser did not expose enough detail to safely identify your chip. Apple menu →  About This Mac shows it: an "Apple M…" chip needs the Apple Silicon DMG, an Intel processor needs the Intel DMG.');
    setText('downloadArchBadge', 'macOS 14+');
    setText('downloadConfidence', 'Both Mac builds are listed below.');

    trackRecommendation(result);
  }

  detectPlatform().then(applyDownloadRecommendation);
})();

(() => {
  const endpoint = '/api/analytics/event';
  const sessionKey = 'ovf_analytics_visit';
  const sessionTimeoutMs = 30 * 60 * 1000;

  function privacyOptedOut() {
    return navigator.globalPrivacyControl === true || navigator.doNotTrack === '1';
  }

  function uuid() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    const bytes = window.crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    return [...bytes].map((byte, index) => `${index === 4 || index === 6 || index === 8 || index === 10 ? '-' : ''}${byte.toString(16).padStart(2, '0')}`).join('');
  }

  function pathname() {
    return window.location.pathname || '/';
  }

  function classifyAcquisitionSource() {
    const params = new URLSearchParams(window.location.search || '');
    const taggedSource = String(params.get('utm_source') || '').toLowerCase();
    const taggedMedium = String(params.get('utm_medium') || '').toLowerCase();
    if (params.has('gclid') || (taggedSource === 'google' && /^(cpc|ppc|paid|paid_search)$/.test(taggedMedium))) {
      return 'google_paid';
    }

    const knownTag = {
      google: 'google_organic', bing: 'bing_organic', github: 'github', reddit: 'reddit',
      linkedin: 'linkedin', x: 'x', twitter: 'x', youtube: 'youtube', newsletter: 'newsletter',
      chatgpt: 'chatgpt', openai: 'chatgpt', perplexity: 'perplexity', claude: 'claude',
      anthropic: 'claude', gemini: 'gemini', copilot: 'copilot',
    }[taggedSource];
    if (knownTag) return knownTag;
    if (taggedSource) return taggedMedium.includes('ai') ? 'other_ai' : 'other';

    let host = '';
    try { host = new URL(document.referrer).hostname.toLowerCase(); } catch {}
    if (!host) return 'direct';
    if (host === 'google.com' || host.endsWith('.google.com') || host.includes('.google.')) return 'google_organic';
    if (host === 'bing.com' || host.endsWith('.bing.com')) return 'bing_organic';
    if (host === 'github.com' || host.endsWith('.github.com')) return 'github';
    if (host === 'reddit.com' || host.endsWith('.reddit.com')) return 'reddit';
    if (host === 'linkedin.com' || host.endsWith('.linkedin.com')) return 'linkedin';
    if (host === 'x.com' || host.endsWith('.x.com') || host === 'twitter.com' || host.endsWith('.twitter.com')) return 'x';
    if (host === 'youtube.com' || host.endsWith('.youtube.com') || host === 'youtu.be') return 'youtube';
    if (host === 'chatgpt.com' || host.endsWith('.chatgpt.com')) return 'chatgpt';
    if (host === 'perplexity.ai' || host.endsWith('.perplexity.ai')) return 'perplexity';
    if (host === 'claude.ai' || host.endsWith('.claude.ai')) return 'claude';
    if (host === 'gemini.google.com') return 'gemini';
    if (host.includes('copilot.microsoft.com')) return 'copilot';
    return 'other';
  }

  function currentVisit() {
    const now = Date.now();
    try {
      const existing = JSON.parse(window.sessionStorage.getItem(sessionKey) || 'null');
      if (existing && /^[0-9a-f-]{36}$/i.test(existing.id || '')
          && Number.isFinite(existing.lastSeen)
          && now - existing.lastSeen < sessionTimeoutMs) {
        existing.lastSeen = now;
        window.sessionStorage.setItem(sessionKey, JSON.stringify(existing));
        return existing;
      }
      const visit = { id: uuid(), source: classifyAcquisitionSource(), lastSeen: now };
      window.sessionStorage.setItem(sessionKey, JSON.stringify(visit));
      return visit;
    } catch {
      return { id: uuid(), source: classifyAcquisitionSource(), lastSeen: now };
    }
  }

  function firstPartyTarget(data) {
    return data.filename || data.destination || data.target || null;
  }

  function sendFirstParty(name, data) {
    if (privacyOptedOut()) return;
    const visit = currentVisit();
    const payload = JSON.stringify({
      eventId: uuid(),
      sessionId: visit.id,
      eventName: name,
      path: pathname(),
      target: firstPartyTarget(data),
      acquisitionSource: visit.source,
    });
    const blob = new Blob([payload], { type: 'application/json' });
    if (typeof navigator.sendBeacon === 'function' && navigator.sendBeacon(endpoint, blob)) return;
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true,
      credentials: 'omit',
    }).catch(() => {});
  }

  function track(name, data = {}) {
    sendFirstParty(name, data);
    if (!privacyOptedOut() && typeof window.va === 'function') window.va('event', { name, data });
  }

  track('page_view');

  document.addEventListener('click', event => {
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href') || '';

    if (href.includes('/downloads/') || href.startsWith('downloads/')) {
      const filename = href.split('/').pop() || href;
      const arch = filename.includes('arm64') ? 'arm64' : filename.includes('x86_64') ? 'x86_64' : 'unknown';
      const versionMatch = filename.match(/OpenVoiceFlow-([0-9]+\.[0-9]+\.[0-9]+)/);
      track('download_click', {
        arch,
        version: versionMatch ? versionMatch[1] : 'unknown',
        filename,
        source_path: pathname(),
      });
      return;
    }

    if (['install.html', '/install.html', '../install.html'].includes(href)) {
      track('install_guide_click', { source_path: pathname() });
      return;
    }
    if (link.closest('.docs-sidebar')) {
      track('docs_nav_click', { destination: href, source_path: pathname() });
      return;
    }
    if (link.closest('.hero-cta-row')) {
      track('hero_cta_click', { destination: href, source_path: pathname() });
      return;
    }
    if (href.includes('github.com/shimoverse/openvoiceflow')) {
      track('github_click', { source_path: pathname() });
      return;
    }
    if (link.closest('.nav')) {
      track('navigation_click', { destination: href, source_path: pathname() });
    }
  });

  document.querySelectorAll('video[data-film]').forEach(video => {
    video.addEventListener('play', () => track('demo_play', { source_path: pathname() }), { once: true });
  });

  document.querySelectorAll('.footer-links a[href]').forEach(link => {
    link.addEventListener('click', () => {
      track('footer_click', {
        destination: link.getAttribute('href') || '',
        source_path: pathname(),
      });
    });
  });

  // Copying the checksum is a distinct intent from clicking Download — it is
  // someone verifying the build before they trust it.
  document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', () => {
      track('copy_click', { source_path: pathname() });
    });
  });

  // Which release notes and which FAQ answers people actually open. `label` is
  // the visible heading, which is authored copy on our own pages — never
  // anything a visitor typed.
  document.querySelectorAll('details > summary').forEach((summary, index) => {
    summary.addEventListener('click', () => {
      const details = summary.parentElement;
      // Fires before the toggle applies, so `open` is still the old state.
      if (details && details.open) return;
      track('disclosure_open', {
        label: (summary.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
        anchor: (details && details.id) || '',
        target: details && details.id ? `#${details.id}` : `disclosure-${index + 1}`,
        source_path: pathname(),
      });
    });
  });
})();

/* ── Docs sidebar: collapsed on phones, always open on desktop ────────
   The markup ships collapsed so a phone doesn't open on 25 links; this
   expands it on wide viewports so desktop never depends on JS running. */
(() => {
  const sidebar = document.getElementById('docsSidebar');
  const toggle = document.getElementById('docsSidebarToggle');
  if (!sidebar || !toggle) return;

  const wide = window.matchMedia('(min-width: 861px)');
  const sync = () => { if (wide.matches) sidebar.dataset.collapsed = 'false'; };
  sync();
  wide.addEventListener('change', sync);

  toggle.addEventListener('click', () => {
    const open = sidebar.dataset.collapsed === 'false';
    sidebar.dataset.collapsed = open ? 'true' : 'false';
    toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    toggle.textContent = open ? 'Documentation menu ▾' : 'Documentation menu ▴';
  });
})();

/* ── Waveform identity ──────────────────────────────────────────────────
   One brand waveform everywhere: the ring glyph (nav/footer), the hero
   listen→transcribe→type demo, the "02 · SPEAK" card wave, and the
   privacy-panel pipeline wave. Ported from the design spec; vanilla JS,
   no dependencies. Honors prefers-reduced-motion (static frames, full
   sentence shown immediately) and pauses when the tab is hidden. */
(() => {
  const canvases = Array.from(document.querySelectorAll('canvas[data-wf]'));
  if (!canvases.length) return;

  const typedNode = document.getElementById('typedDemo');
  const chipNode = document.getElementById('heroChip');
  const statusNode = document.getElementById('heroStatus');
  const TYPED_TEXT = 'Ship the beta tonight — the release notes are already in the doc.';

  const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  function palette() {
    const dark = darkQuery.matches;
    return {
      acc: dark ? '#E8974E' : '#B4661F',
      dim: dark ? 'rgba(214,208,194,.5)' : 'rgba(58,52,40,.45)',
      // The privacy panel is deliberately dark in both themes.
      pline: '#E8974E',
    };
  }

  const state = { loop: 'listen', amp: 0, tgt: 0, sylT: 0, last: 0 };
  const hist = new Float32Array(150);
  const timers = [];
  let typeTimer = null;
  let raf = 0;

  function after(ms, fn) { timers.push(setTimeout(fn, ms)); }

  function setLoop(loop) {
    state.loop = loop;
    if (chipNode) chipNode.classList.toggle('idle', loop !== 'listen');
    if (statusNode) {
      statusNode.textContent =
        loop === 'listen' ? 'listening'
        : loop === 'spool' ? 'transcribing — on device'
        : 'pasted at the cursor';
    }
  }

  function cycle() {
    setLoop('listen');
    if (typedNode) typedNode.textContent = '';
    after(3000, () => {
      setLoop('spool');
      after(900, () => {
        setLoop('type');
        let i = 0;
        typeTimer = setInterval(() => {
          i += 2;
          if (typedNode) typedNode.textContent = TYPED_TEXT.slice(0, i);
          if (i >= TYPED_TEXT.length) {
            clearInterval(typeTimer);
            typeTimer = null;
            after(2600, cycle);
          }
        }, 20);
      });
    });
  }

  function speechEnvelope(t) {
    const gate = (Math.sin(t * 0.9) + Math.sin(t * 0.53 + 1.2)) > 0.9 ? 0.06 : 1;
    let v = (Math.sin(t * 2.3) + Math.sin(t * 3.85 + 1.4) + Math.sin(t * 5.9 + 0.4)) / 3;
    v = Math.max(0, v * 0.75 + 0.5);
    return Math.min(1, v * gate);
  }

  function windowFn(u) { return Math.pow(Math.max(0, Math.sin(Math.PI * u)), 0.85); }

  function drawRing(ctx, w, h, t, color) {
    const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.34, gap = 0.62, off = -1.0;
    ctx.beginPath();
    for (let a = off + gap / 2; a <= off + 2 * Math.PI - gap / 2; a += 0.045) {
      const r = R * (1 + 0.10 * Math.sin(a * 5 - t * 0.7));
      const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
      a <= off + gap / 2 + 0.05 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.lineWidth = 2.2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function drawWave(ctx, w, h, t, ampAt, color, glow) {
    ctx.beginPath();
    const mid = h / 2;
    for (let x = 0; x <= w; x += 2) {
      const u = x / w, a = ampAt(u);
      const y = mid
        + (a < 0.03 ? Math.sin(x * 0.045 - t * 1.7) * 1.15 : 0)
        + a * h * 0.30 * (
          Math.sin(x * 0.052 + t * 6.6) * 0.55 +
          Math.sin(x * 0.117 - t * 9.4) * 0.26 +
          Math.sin(x * 0.026 + t * 3.2) * 0.42
        ) * windowFn(u);
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = color;
    if (glow) { ctx.shadowColor = color; ctx.shadowBlur = 7; }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function drawSpool(ctx, w, h, t, color) {
    const cx = w / 2, cy = h / 2, rot = t * 6.9;
    ctx.beginPath();
    for (let a = 0; a <= 4 * Math.PI; a += 0.12) {
      const r = (2.5 + a * 0.95) * Math.min(1, h * 0.028);
      const x = cx + Math.cos(a + rot) * r, y = cy + Math.sin(a + rot) * r * 0.92;
      a === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function paint(now) {
    const t = now / 1000;
    const dt = Math.min(50, now - (state.last || now));
    state.last = now;
    const colors = palette();

    if (state.loop === 'listen') {
      if (now > state.sylT) {
        state.sylT = now + 90 + Math.random() * 190;
        const r = Math.random();
        state.tgt = r < 0.18 ? 0.04 : 0.25 + Math.random() * 0.7;
      }
    } else {
      state.tgt = 0;
    }
    state.amp += (state.tgt - state.amp) * (1 - Math.exp(-dt / 70));
    hist.copyWithin(0, 1);
    hist[hist.length - 1] = state.amp;

    const d = Math.min(2, window.devicePixelRatio || 1);
    for (const el of canvases) {
      const w = el.clientWidth, h = el.clientHeight;
      if (!w || !h) continue;
      if (el.width !== (w * d | 0) || el.height !== (h * d | 0)) {
        el.width = w * d | 0;
        el.height = h * d | 0;
      }
      const ctx = el.getContext('2d');
      ctx.setTransform(d, 0, 0, d, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const mode = el.dataset.wf;

      if (mode === 'glyph') {
        drawRing(ctx, w, h, t, colors.acc);
      } else if (mode === 'hero') {
        if (state.loop === 'listen') {
          const n = hist.length;
          const ampAt = u => hist[Math.min(n - 1, (u * (n - 1)) | 0)];
          drawWave(ctx, w, h, t, ampAt, state.amp > 0.06 ? colors.acc : colors.dim, state.amp > 0.12);
        } else if (state.loop === 'spool') {
          drawSpool(ctx, w, h, t, colors.acc);
        } else {
          const mid = h / 2, cx = w / 2;
          ctx.beginPath();
          ctx.moveTo(cx - 8, mid);
          ctx.lineTo(cx + 8, mid);
          ctx.lineWidth = 2.4;
          ctx.lineCap = 'round';
          ctx.strokeStyle = colors.acc;
          ctx.stroke();
        }
      } else if (mode === 'card') {
        drawWave(ctx, w, h, t, u => speechEnvelope(t - (1 - u) * 1.25), colors.acc, true);
      } else if (mode === 'pline') {
        drawWave(ctx, w, h, t, u => speechEnvelope(t * 0.8 - (1 - u) * 1.4), colors.pline, true);
      }
    }
  }

  function tick(now) {
    if (!document.hidden) paint(now);
    raf = requestAnimationFrame(tick);
  }

  function staticFrame() {
    // Reduce Motion: one calm, representative frame — no loops, no typing.
    if (typedNode) typedNode.textContent = TYPED_TEXT;
    setLoop('listen');
    for (let i = 0; i < hist.length; i++) {
      hist[i] = speechEnvelope(i / 18) * 0.6;
    }
    state.amp = 0.4;
    state.loop = 'listen';
    paint(1000);
    if (statusNode) statusNode.textContent = 'listening';
  }

  if (motionQuery.matches) {
    staticFrame();
    darkQuery.addEventListener('change', staticFrame);
    window.addEventListener('resize', staticFrame);
  } else {
    cycle();
    raf = requestAnimationFrame(tick);
    motionQuery.addEventListener('change', () => {
      if (motionQuery.matches) {
        cancelAnimationFrame(raf);
        timers.forEach(clearTimeout);
        if (typeTimer) clearInterval(typeTimer);
        staticFrame();
      }
    });
  }
})();

/* ── Checksum copy buttons (download page) ─────────────────────────── */
(() => {
  document.querySelectorAll('.copy-btn[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        const original = button.textContent;
        button.textContent = 'copied';
        setTimeout(() => { button.textContent = original; }, 1600);
      } catch (error) {
        // Clipboard API unavailable (http, older browser) — leave the
        // checksum selectable in the adjacent code block.
      }
    });
  });
})();
