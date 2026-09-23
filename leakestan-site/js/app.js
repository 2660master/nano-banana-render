/* ==========================================================================
   LEAKESTAN — gallery logic
   Reads everything from data/content.js (window.LEAKESTAN).
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

  var state = {
    category: CATEGORIES.length ? CATEGORIES[0].key : HOME,
    query: "",
    sort: "newest",
    view: readStored("leakestan:view") || "grid",
  };

  /* Minimal stroke icons for the sidebar, keyed by the category's icon field. */
  var ICONS = {
    home: '<path d="M4 11 12 4l8 7"/><path d="M6 10v9h12v-9"/>',
    file: '<path d="M14 3H7v18h10V6z"/><path d="M13 3v4h4"/>',
    tool: '<path d="M15 3a5 5 0 0 0-4.6 7L3 17.4 6.6 21l7.4-7.4A5 5 0 0 0 21 9l-3 3-3-3 3-3a5 5 0 0 0-3-3z"/>',
    bug: '<rect x="8" y="8" width="8" height="11" rx="4"/><path d="M8 12H4M20 12h-4M8 17l-3 2M16 17l3 2M8 9 6 6M16 9l2-3"/>',
    warn: '<path d="M12 4 2.8 20h18.4z"/><path d="M12 10v4M12 17.2v.1"/>',
    dot: '<circle cx="12" cy="12" r="4"/>',
  };

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

  function iconMarkup(name) {
    var body = ICONS[name] || ICONS.dot;
    return '<svg class="nav__icon" viewBox="0 0 24 24" width="17" height="17" fill="none" ' +
      'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true">' + body + "</svg>";
  }

  var toastTimer;
  function toast(message) {
    if (!toastEl) { return; }
    toastEl.textContent = message;
    toastEl.classList.add("is-on");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toastEl.classList.remove("is-on");
    }, 2600);
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
    var buttons = ["discordSidebar", "discordTop", "discordFooter"].map($).filter(Boolean);
    var hint = $("discordHint");

    buttons.forEach(function (btn) {
      if (INVITE) {
        btn.href = INVITE;
        btn.target = "_blank";
        btn.classList.remove("is-empty");
      } else {
        btn.href = "#";
        btn.removeAttribute("target");
        btn.classList.add("is-empty");
        btn.addEventListener("click", function (event) {
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
  }

  /* ── Filtering ────────────────────────────────────────────────────── */

  function visibleItems() {
    var q = state.query.toLowerCase();

    var list = ITEMS.filter(function (item) {
      if (state.category !== HOME && item.category !== state.category) { return false; }
      if (!q) { return true; }
      return (item.name + " " + item.category).toLowerCase().indexOf(q) !== -1;
    });

    list.sort(function (a, b) {
      if (state.sort === "name") { return a.name.localeCompare(b.name); }
      return new Date(b.added || 0) - new Date(a.added || 0);
    });

    return list;
  }

  /* ── Rendering ────────────────────────────────────────────────────── */

  function cardMarkup(item) {
    var blank = !hasRealDownload(item);

    return '<article class="card" id="item-' + esc(item.id) + '">' +
      '<button class="card__shot" type="button" data-open="' + esc(item.id) + '">' +
        '<img class="card__img" src="' + esc(item.image) + '" alt="' + esc(item.name) + ' preview" loading="lazy">' +
      "</button>" +
      '<div class="card__body">' +
        '<h3 class="card__name">' + esc(item.name) + "</h3>" +
        '<div class="card__actions">' +
          '<a class="btn btn--primary" href="' + esc(downloadHref(item)) + '"' +
            (blank ? ' download="' + esc(item.id) + '-blank.txt"' : " download") +
            ' data-download="' + esc(item.id) + '">Download</a>' +
          '<button class="icon-btn" type="button" data-copy="' + esc(item.id) + '" title="Copy link">' +
            '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
            '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/>' +
            '<path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>' +
            '<span class="sr-only">Copy link</span>' +
          "</button>" +
        "</div>" +
      "</div>" +
    "</article>";
  }

  function render() {
    var list = visibleItems();
    var label = categoryLabel(state.category);

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
  }

  /* ── Stats ────────────────────────────────────────────────────────── */

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

  function renderStats() {
    /* Home is a view of everything, not a category of its own. */
    var cats = CATEGORIES.filter(function (c) { return c.key !== HOME; }).length;
    countUp($("statItems"), ITEMS.length);
    countUp($("statCats"), cats);
  }

  /* ── Lightbox ─────────────────────────────────────────────────────── */

  var lightbox = $("lightbox");
  var lastFocus = null;

  function openLightbox(id) {
    var item = ITEMS.filter(function (p) { return p.id === id; })[0];
    if (!item) { return; }

    lastFocus = document.activeElement;
    $("lbImg").src = item.image;
    $("lbImg").alt = item.name + " preview";
    $("lbTitle").textContent = item.name;
    $("lbMeta").textContent = [
      categoryLabel(item.category), formatDate(item.added),
    ].filter(Boolean).join(" · ");

    var link = $("lbDownload");
    link.href = downloadHref(item);
    link.setAttribute("data-download", item.id);
    link.setAttribute("download", hasRealDownload(item) ? "" : item.id + "-blank.txt");

    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    link.focus();
  }

  function closeLightbox() {
    lightbox.hidden = true;
    document.body.style.overflow = "";
    if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
  }

  /* ── Mobile sidebar ───────────────────────────────────────────────── */

  function setSidebar(open) {
    sidebar.classList.toggle("is-open", open);
    backdrop.hidden = !open;
    var toggle = $("menuToggle");
    if (toggle) { toggle.setAttribute("aria-expanded", String(open)); }
  }

  /* ── Events ───────────────────────────────────────────────────────── */

  function wireEvents() {
    catList.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-category]");
      if (!btn) { return; }
      state.category = btn.getAttribute("data-category");
      Array.prototype.forEach.call(catList.querySelectorAll(".nav__btn"), function (el) {
        el.classList.toggle("is-active", el === btn);
      });
      setSidebar(false);
      render();
    });

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

      var copy = event.target.closest("[data-copy]");
      if (copy) {
        var url = location.origin + location.pathname + "#item-" + copy.getAttribute("data-copy");
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            toast("Link copied");
          }, function () {
            toast("Could not copy link");
          });
        } else {
          toast("Clipboard not available");
        }
        return;
      }

      var dl = event.target.closest("[data-download]");
      if (dl) { announceDownload(dl.getAttribute("data-download")); }
    });

    $("lbDownload").addEventListener("click", function () {
      announceDownload(this.getAttribute("data-download"));
    });

    Array.prototype.forEach.call(lightbox.querySelectorAll("[data-close]"), function (el) {
      el.addEventListener("click", closeLightbox);
    });

    $("menuToggle").addEventListener("click", function () {
      setSidebar(!sidebar.classList.contains("is-open"));
    });
    backdrop.addEventListener("click", function () { setSidebar(false); });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        if (!lightbox.hidden) { closeLightbox(); }
        setSidebar(false);
      }
      if (event.key === "/" && document.activeElement !== search) {
        event.preventDefault();
        search.focus();
      }
    });
  }

  function announceDownload(id) {
    var item = ITEMS.filter(function (p) { return p.id === id; })[0];
    if (!item) { return; }
    if (hasRealDownload(item)) {
      toast("Downloading " + item.name + "…");
    } else {
      toast("Placeholder — " + item.name + " has no link yet (blank file).");
    }
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
    renderStats();
    render();

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
