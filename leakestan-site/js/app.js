/* ==========================================================================
   LEAKESTAN — gallery logic
   Reads everything from data/content.js (window.LEAKESTAN).
   Visual effects live in fx.js, the cursor in cursor.js.
   ========================================================================== */
(function () {
  "use strict";

  var CFG = window.LEAKESTAN || {};
  var ITEMS = Array.isArray(CFG.ITEMS) ? CFG.ITEMS.slice() : [];
  var CATEGORIES = Array.isArray(CFG.CATEGORIES) ? CFG.CATEGORIES.slice() : [];
  var BLANK = CFG.BLANK_DOWNLOAD || "assets/blank.txt";
  var INVITE = (CFG.DISCORD_INVITE || "").trim();

  /* "home" is the catch-all tab — it lists every entry. */
  var HOME = "home";

  var $ = function (id) { return document.getElementById(id); };

  var grid = $("grid");
  var empty = $("empty");
  var search = $("search");
  var sortSel = $("sort");
  var catList = $("categoryList");
  var resultTitle = $("resultTitle");
  var resultCount = $("resultCount");
  var sidebar = $("sidebar");
  var backdrop = $("backdrop");
  var toastEl = $("toast");
  var toastMsg = $("toastMsg");

  var state = {
    category: CATEGORIES.length ? CATEGORIES[0].key : HOME,
    query: "",
    sort: "newest",
    view: readStored("leakestan:view") || "grid",
  };

  /* What the grid currently shows, in order — the lightbox walks this. */
  var shown = [];

  /* Catalogue number per entry, fixed by its position in content.js. */
  var catalogue = {};
  ITEMS.forEach(function (item, i) { catalogue[item.id] = i + 1; });

  /* Minimal stroke icons for the sidebar, keyed by the category's icon field. */
  var ICONS = {
    home: '<path d="M4 11 12 4l8 7"/><path d="M6 10v9h12v-9"/>',
    file: '<path d="M14 3H7v18h10V6z"/><path d="M13 3v4h4"/>',
    tool: '<path d="M15 3a5 5 0 0 0-4.6 7L3 17.4 6.6 21l7.4-7.4A5 5 0 0 0 21 9l-3 3-3-3 3-3a5 5 0 0 0-3-3z"/>',
    bug: '<rect x="8" y="8" width="8" height="11" rx="4"/><path d="M8 12H4M20 12h-4M8 17l-3 2M16 17l3 2M8 9 6 6M16 9l2-3"/>',
    warn: '<path d="M12 4 2.8 20h18.4z"/><path d="M12 10v4M12 17.2v.1"/>',
    dot: '<circle cx="12" cy="12" r="4"/>',
  };

  var SVG_DOWNLOAD =
    '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 20h14"/></svg>';

  /* ── helpers ──────────────────────────────────────────────────────── */

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function readStored(key) {
    try { return window.localStorage.getItem(key); } catch (err) { return null; }
  }

  function writeStored(key, value) {
    try { window.localStorage.setItem(key, value); } catch (err) { /* private mode */ }
  }

  function pad(n) { return n < 10 ? "0" + n : String(n); }

  function formatNumber(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function formatDate(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) { return iso || "—"; }
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  }

  function categoryLabel(key) {
    for (var i = 0; i < CATEGORIES.length; i++) {
      if (CATEGORIES[i].key === key) { return CATEGORIES[i].label; }
    }
    return key;
  }

  function byId(id) {
    for (var i = 0; i < ITEMS.length; i++) {
      if (ITEMS[i].id === id) { return ITEMS[i]; }
    }
    return null;
  }

  function newestFirst(list) {
    return list.slice().sort(function (a, b) {
      return new Date(b.added || 0) - new Date(a.added || 0);
    });
  }

  function iconMarkup(name) {
    var body = ICONS[name] || ICONS.dot;
    return '<svg class="nav__icon" viewBox="0 0 24 24" width="17" height="17" fill="none" ' +
      'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true">' + body + "</svg>";
  }

  var toastTimer;
  function toast(message) {
    if (!toastEl) { return; }
    toastMsg.textContent = message;
    toastEl.classList.remove("is-on");
    /* Force a reflow so the timer bar restarts on back-to-back toasts. */
    void toastEl.offsetWidth;
    toastEl.classList.add("is-on");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toastEl.classList.remove("is-on");
    }, 2600);
  }

  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
    } else {
      done(false);
    }
  }

  /* An entry without a real link falls back to the blank placeholder file. */
  function hasRealDownload(item) {
    return typeof item.download === "string" && item.download.trim() !== "";
  }

  function downloadHref(item) {
    return hasRealDownload(item) ? item.download.trim() : BLANK;
  }

  /* ── Discord buttons ──────────────────────────────────────────────── */

  function wireDiscord() {
    var links = ["discordSidebar", "discordTop", "discordFooter"].map($).filter(Boolean);
    var hint = $("discordHint");

    links.forEach(function (link) {
      if (INVITE) {
        link.href = INVITE;
        link.target = "_blank";
        link.classList.remove("is-empty");
      } else {
        link.href = "#";
        link.removeAttribute("target");
        link.classList.add("is-empty");
        link.addEventListener("click", function (event) {
          event.preventDefault();
          toast("Discord invite is not set yet — add it in data/content.js");
        });
      }
    });

    if (hint) { hint.hidden = Boolean(INVITE); }
  }

  /* ── Categories ───────────────────────────────────────────────────── */

  function countFor(key) {
    if (key === HOME) { return ITEMS.length; }
    return ITEMS.filter(function (item) { return item.category === key; }).length;
  }

  function buildCategories() {
    catList.innerHTML = CATEGORIES.map(function (cat) {
      var count = countFor(cat.key);
      return '<li><button class="nav__btn' + (cat.key === state.category ? " is-active" : "") +
        '" type="button" data-category="' + esc(cat.key) + '">' +
        iconMarkup(cat.icon) +
        '<span class="nav__name">' + esc(cat.label) + "</span>" +
        '<span class="nav__count' + (count ? "" : " is-zero") + '">' + count + "</span>" +
        "</button></li>";
    }).join("");

    var footerCats = $("footerCats");
    if (footerCats) {
      footerCats.innerHTML = CATEGORIES.map(function (cat) {
        return '<li><button class="footer__link" type="button" data-category="' + esc(cat.key) + '">' +
          esc(cat.label) + "</button></li>";
      }).join("");
    }
  }

  /* The highlight glides between categories instead of jumping. */
  function moveIndicator() {
    var indicator = $("navIndicator");
    var active = catList.querySelector(".nav__btn.is-active");
    if (!indicator || !active) { return; }
    indicator.style.transform = "translateY(" + active.offsetTop + "px)";
    indicator.style.height = active.offsetHeight + "px";
    indicator.classList.add("is-ready");
  }

  function selectCategory(key) {
    state.category = key;
    Array.prototype.forEach.call(catList.querySelectorAll(".nav__btn"), function (el) {
      el.classList.toggle("is-active", el.getAttribute("data-category") === key);
    });
    moveIndicator();
    setSidebar(false);
    render();
  }

  /* ── Filtering ────────────────────────────────────────────────────── */

  function visibleItems() {
    var q = state.query.toLowerCase();

    var list = ITEMS.filter(function (item) {
      if (state.category !== HOME && item.category !== state.category) { return false; }
      if (!q) { return true; }
      return (item.name + " " + item.category).toLowerCase().indexOf(q) !== -1;
    });

    if (state.sort === "name") {
      return list.sort(function (a, b) { return a.name.localeCompare(b.name); });
    }
    return newestFirst(list);
  }

  /* ── Rendering ────────────────────────────────────────────────────── */

  function cardMarkup(item, position) {
    var blank = !hasRealDownload(item);
    var number = "#" + pad(catalogue[item.id] || position + 1);

    return '<article class="card" id="item-' + esc(item.id) + '" style="--i:' + position + '">' +
      '<button class="card__shot" type="button" data-open="' + esc(item.id) + '" ' +
        'aria-label="Open ' + esc(item.name) + ' preview">' +
        '<img class="card__img" src="' + esc(item.image) + '" alt="' + esc(item.name) + ' preview" ' +
          'loading="lazy" decoding="async">' +
        '<span class="card__index">' + number + "</span>" +
      "</button>" +
      '<div class="card__body">' +
        '<h3 class="card__name">' + esc(item.name) + "</h3>" +
        '<div class="card__actions">' +
          '<a class="btn btn--primary" href="' + esc(downloadHref(item)) + '"' +
            (blank ? ' download="' + esc(item.id) + '-blank.txt"' : " download") +
            ' data-download="' + esc(item.id) + '">' + SVG_DOWNLOAD + "<span>Download</span></a>" +
        "</div>" +
      "</div>" +
    "</article>";
  }

  function render() {
    var list = visibleItems();
    var label = categoryLabel(state.category);
    shown = list;

    grid.classList.toggle("is-list", state.view === "list");
    grid.innerHTML = list.map(cardMarkup).join("");

    resultTitle.textContent = label;
    resultCount.textContent = list.length + (list.length === 1 ? " result" : " results");

    empty.hidden = list.length > 0;
    if (!empty.hidden) {
      var searching = state.query !== "";
      $("emptyTitle").textContent = searching ? "No matches" : "Nothing here yet";
      $("emptyText").textContent = searching
        ? 'Nothing matches "' + state.query + '".'
        : label + " is still empty.";
    }

    /* fx.js hooks reveal, tilt and image fade-in onto the fresh cards. */
    document.dispatchEvent(new CustomEvent("leakestan:render"));
  }

  /* ── Hero extras ──────────────────────────────────────────────────── */

  function countUp(el, target) {
    if (!el) { return; }
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || target === 0) { el.textContent = formatNumber(target); return; }

    var start = performance.now();
    var duration = 900;

    (function step(now) {
      var progress = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = formatNumber(Math.round(target * eased));
      if (progress < 1) { window.requestAnimationFrame(step); }
    })(start);
  }

  /* Hold an animation until the intro has cleared, so it isn't played to
     nobody. Falls through on a timer in case fx.js never reports back. */
  function whenIntroDone(fn) {
    if (document.documentElement.classList.contains("intro-skip")) { fn(); return; }
    var fired = false;
    function go() {
      if (fired) { return; }
      fired = true;
      fn();
    }
    document.addEventListener("leakestan:intro-done", go);
    window.setTimeout(go, 1800);
  }

  function renderHero() {
    /* Home is a view of everything, not a category of its own. */
    var cats = CATEGORIES.filter(function (c) { return c.key !== HOME; }).length;
    whenIntroDone(function () {
      countUp($("statItems"), ITEMS.length);
      countUp($("statCats"), cats);
    });

    var latest = newestFirst(ITEMS);

    var updated = $("updated");
    if (updated && latest[0]) {
      updated.textContent = formatDate(latest[0].added);
      updated.setAttribute("datetime", latest[0].added);
    }

    /* Three newest previews, fanned out on the right. */
    var stack = $("heroStack");
    if (stack) {
      stack.innerHTML = latest.slice(0, 3).map(function (item, i) {
        return '<img class="hero__shot hero__shot--' + (i + 1) + '" src="' + esc(item.image) + '" alt="" ' +
          'decoding="async">';
      }).join("");
    }

    /* Ticker: the list twice, so the loop has no visible seam. */
    var ticker = $("ticker");
    if (ticker && ITEMS.length) {
      var run = latest.map(function (item) {
        return '<span class="ticker__item">' + esc(item.name) + "</span>";
      }).join('<span class="ticker__sep">◆</span>');
      ticker.innerHTML = '<div class="ticker__run">' + run + '<span class="ticker__sep">◆</span></div>' +
        '<div class="ticker__run">' + run + '<span class="ticker__sep">◆</span></div>';
      ticker.style.setProperty("--ticker-duration", Math.max(20, ITEMS.length * 3.2) + "s");
    }

    var footerCount = $("footerCount");
    if (footerCount) {
      footerCount.textContent = ITEMS.length + (ITEMS.length === 1 ? " entry" : " entries") + " indexed";
    }

    var year = $("year");
    if (year) { year.textContent = String(new Date().getFullYear()); }

    /* Show the right modifier key for the search shortcut. */
    var kbd = $("searchKbd");
    if (kbd && /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent)) {
      kbd.textContent = "⌘ K";
    }
  }

  /* ── Lightbox ─────────────────────────────────────────────────────── */

  var lightbox = $("lightbox");
  var lastFocus = null;
  var lbIndex = -1;

  function showInLightbox(index) {
    if (!shown.length) { return; }
    lbIndex = (index + shown.length) % shown.length;
    var item = shown[lbIndex];

    var img = $("lbImg");
    img.classList.remove("is-in");
    img.src = item.image;
    img.alt = item.name + " preview";
    /* Restart the swap animation even when the image is cached. */
    void img.offsetWidth;
    img.classList.add("is-in");

    $("lbTitle").textContent = item.name;
    $("lbMeta").textContent = [
      "#" + pad(catalogue[item.id] || lbIndex + 1),
      categoryLabel(item.category),
      formatDate(item.added),
    ].filter(Boolean).join(" · ");
    $("lbCount").textContent = (lbIndex + 1) + " / " + shown.length;

    var single = shown.length < 2;
    $("lbPrev").hidden = single;
    $("lbNext").hidden = single;

    var link = $("lbDownload");
    link.href = downloadHref(item);
    link.setAttribute("data-download", item.id);
    link.setAttribute("download", hasRealDownload(item) ? "" : item.id + "-blank.txt");
  }

  function openLightbox(id) {
    var index = -1;
    for (var i = 0; i < shown.length; i++) {
      if (shown[i].id === id) { index = i; break; }
    }
    if (index === -1) { return; }

    lastFocus = document.activeElement;
    showInLightbox(index);
    lightbox.hidden = false;
    document.body.classList.add("is-locked");
    $("lbDownload").focus({ preventScroll: true });
  }

  function closeLightbox() {
    if (lightbox.hidden) { return; }
    lightbox.hidden = true;
    document.body.classList.remove("is-locked");
    if (lastFocus && lastFocus.focus) { lastFocus.focus({ preventScroll: true }); }
  }

  /* Keep Tab inside the dialog while it is open. */
  function trapFocus(event) {
    var focusable = Array.prototype.filter.call(
      lightbox.querySelectorAll("button, a[href]"),
      function (el) { return !el.hidden && el.offsetParent !== null; }
    );
    if (!focusable.length) { return; }
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  /* ── Mobile sidebar ───────────────────────────────────────────────── */

  function setSidebar(open) {
    sidebar.classList.toggle("is-open", open);
    backdrop.hidden = !open;
    var toggle = $("menuToggle");
    if (toggle) { toggle.setAttribute("aria-expanded", String(open)); }
  }

  /* ── Events ───────────────────────────────────────────────────────── */

  function announceDownload(id) {
    var item = byId(id);
    if (!item) { return; }
    if (hasRealDownload(item)) {
      toast("Downloading " + item.name + "…");
    } else {
      toast("Placeholder — " + item.name + " has no link yet.");
    }
  }

  function wireEvents() {
    catList.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-category]");
      if (btn) { selectCategory(btn.getAttribute("data-category")); }
    });

    var footerCats = $("footerCats");
    if (footerCats) {
      footerCats.addEventListener("click", function (event) {
        var btn = event.target.closest("[data-category]");
        if (!btn) { return; }
        selectCategory(btn.getAttribute("data-category"));
        resultTitle.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }

    search.addEventListener("input", function () {
      state.query = search.value.trim();
      render();
    });

    sortSel.addEventListener("change", function () {
      state.sort = sortSel.value;
      render();
    });

    Array.prototype.forEach.call(document.querySelectorAll("[data-view]"), function (btn) {
      btn.addEventListener("click", function () {
        state.view = btn.getAttribute("data-view");
        writeStored("leakestan:view", state.view);
        Array.prototype.forEach.call(document.querySelectorAll("[data-view]"), function (el) {
          var on = el === btn;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-pressed", String(on));
        });
        render();
      });
    });

    grid.addEventListener("click", function (event) {
      var shot = event.target.closest("[data-open]");
      if (shot) { openLightbox(shot.getAttribute("data-open")); return; }

      var dl = event.target.closest("[data-download]");
      if (dl) { announceDownload(dl.getAttribute("data-download")); }
    });

    var copySite = $("copySite");
    if (copySite) {
      copySite.addEventListener("click", function () {
        copyText(location.origin + location.pathname, function (ok) {
          toast(ok ? "Site link copied" : "Could not copy link");
        });
      });
    }

    $("lbDownload").addEventListener("click", function () {
      announceDownload(this.getAttribute("data-download"));
    });
    $("lbPrev").addEventListener("click", function () { showInLightbox(lbIndex - 1); });
    $("lbNext").addEventListener("click", function () { showInLightbox(lbIndex + 1); });

    Array.prototype.forEach.call(lightbox.querySelectorAll("[data-close]"), function (el) {
      el.addEventListener("click", closeLightbox);
    });

    $("menuToggle").addEventListener("click", function () {
      setSidebar(!sidebar.classList.contains("is-open"));
    });
    backdrop.addEventListener("click", function () { setSidebar(false); });

    document.addEventListener("keydown", function (event) {
      var open = !lightbox.hidden;
      var cmdK = (event.metaKey || event.ctrlKey) && (event.key === "k" || event.key === "K");

      if (event.key === "Escape") {
        closeLightbox();
        setSidebar(false);
        return;
      }

      /* Search wins over an open preview: close it and jump to the field. */
      if (open && cmdK) { closeLightbox(); }

      if (open && !cmdK) {
        if (event.key === "ArrowLeft") { event.preventDefault(); showInLightbox(lbIndex - 1); }
        if (event.key === "ArrowRight") { event.preventDefault(); showInLightbox(lbIndex + 1); }
        if (event.key === "Tab") { trapFocus(event); }
        return;
      }

      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement && document.activeElement.tagName);

      if (cmdK || (event.key === "/" && !typing)) {
        event.preventDefault();
        search.focus();
        search.select();
      }
    });

    window.addEventListener("resize", moveIndicator);
  }

  /* ── Boot ─────────────────────────────────────────────────────────── */

  function init() {
    if (!grid) { return; }

    Array.prototype.forEach.call(document.querySelectorAll("[data-view]"), function (el) {
      var on = el.getAttribute("data-view") === state.view;
      el.classList.toggle("is-active", on);
      el.setAttribute("aria-pressed", String(on));
    });

    buildCategories();
    wireDiscord();
    wireEvents();
    renderHero();
    render();
    moveIndicator();

    if (location.hash.indexOf("#item-") === 0) {
      var target = document.getElementById(location.hash.slice(1));
      if (target) { target.scrollIntoView({ block: "center" }); }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
