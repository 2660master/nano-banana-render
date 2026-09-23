/* ==========================================================================
   LEAKESTAN — gallery logic
   Reads everything from data/packs.js (window.LEAKESTAN).
   ========================================================================== */
(function () {
  "use strict";

  var CFG = window.LEAKESTAN || {};
  var PACKS = Array.isArray(CFG.PACKS) ? CFG.PACKS.slice() : [];
  var BLANK = CFG.BLANK_DOWNLOAD || "assets/blank.txt";
  var INVITE = (CFG.DISCORD_INVITE || "").trim();

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
    category: "all",
    query: "",
    sort: "newest",
    view: readStored("leakestan:view") || "grid",
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

  /* A pack without a real link falls back to the blank placeholder file. */
  function hasRealDownload(pack) {
    return typeof pack.download === "string" && pack.download.trim() !== "";
  }

  function downloadHref(pack) {
    return hasRealDownload(pack) ? pack.download.trim() : BLANK;
  }

  function downloadName(pack) {
    return hasRealDownload(pack) ? "" : pack.id + "-blank.txt";
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
          toast("Discord invite is not set yet — add it in data/packs.js");
        });
      }
    });

    if (hint) { hint.hidden = Boolean(INVITE); }
  }

  /* ── Categories ───────────────────────────────────────────────────── */

  function buildCategories() {
    var counts = {};
    PACKS.forEach(function (pack) {
      var key = pack.category || "Other";
      counts[key] = (counts[key] || 0) + 1;
    });

    var entries = [{ key: "all", label: "All packs", count: PACKS.length }];
    Object.keys(counts).sort().forEach(function (key) {
      entries.push({ key: key, label: key, count: counts[key] });
    });

    catList.innerHTML = entries.map(function (entry) {
      return '<li><button class="nav__btn' + (entry.key === state.category ? " is-active" : "") +
        '" type="button" data-category="' + esc(entry.key) + '">' +
        '<span class="nav__dot"></span>' + esc(entry.label) +
        '<span class="nav__count">' + entry.count + "</span></button></li>";
    }).join("");

    return Object.keys(counts).length;
  }

  /* ── Filtering ────────────────────────────────────────────────────── */

  function visiblePacks() {
    var q = state.query.toLowerCase();

    var list = PACKS.filter(function (pack) {
      var matchesCategory = state.category === "all" || pack.category === state.category;
      if (!matchesCategory) { return false; }
      if (!q) { return true; }
      return (pack.name + " " + pack.category + " " + (pack.resolution || ""))
        .toLowerCase().indexOf(q) !== -1;
    });

    list.sort(function (a, b) {
      if (state.sort === "name") { return a.name.localeCompare(b.name); }
      if (state.sort === "popular") { return (b.hits || 0) - (a.hits || 0); }
      return new Date(b.added || 0) - new Date(a.added || 0);
    });

    return list;
  }

  /* ── Rendering ────────────────────────────────────────────────────── */

  function cardMarkup(pack) {
    var blank = !hasRealDownload(pack);

    return '<article class="card" id="pack-' + esc(pack.id) + '">' +
      '<button class="card__shot" type="button" data-open="' + esc(pack.id) + '">' +
        (pack.featured ? '<span class="card__flag">Hot</span>' : "") +
        '<img class="card__img" src="' + esc(pack.image) + '" alt="' + esc(pack.name) + ' preview" loading="lazy">' +
        (pack.resolution ? '<span class="card__res">' + esc(pack.resolution) + "</span>" : "") +
      "</button>" +
      '<div class="card__body">' +
        '<div class="card__head">' +
          '<h3 class="card__name">' + esc(pack.name) + "</h3>" +
          '<span class="card__cat">' + esc(pack.category) + "</span>" +
        "</div>" +
        '<div class="card__meta">' +
          "<span>" + esc(pack.size || "—") + "</span>" +
          "<span>" + esc(formatDate(pack.added)) + "</span>" +
          "<span>" + formatNumber(pack.hits || 0) + " grabs</span>" +
        "</div>" +
        '<div class="card__actions">' +
          '<a class="btn btn--primary" href="' + esc(downloadHref(pack)) + '"' +
            (blank ? ' download="' + esc(downloadName(pack)) + '"' : " download") +
            ' data-download="' + esc(pack.id) + '">Download</a>' +
          '<button class="icon-btn" type="button" data-copy="' + esc(pack.id) + '" title="Copy link">' +
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
    var list = visiblePacks();

    grid.classList.toggle("is-list", state.view === "list");
    grid.innerHTML = list.map(cardMarkup).join("");

    empty.hidden = list.length > 0;
    resultTitle.textContent = state.category === "all" ? "All packs" : state.category;
    resultCount.textContent = list.length + (list.length === 1 ? " result" : " results");
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

  function renderStats(categoryCount) {
    var hits = PACKS.reduce(function (sum, pack) { return sum + (pack.hits || 0); }, 0);
    countUp($("statPacks"), PACKS.length);
    countUp($("statCats"), categoryCount);
    countUp($("statHits"), hits);
  }

  /* ── Lightbox ─────────────────────────────────────────────────────── */

  var lightbox = $("lightbox");
  var lastFocus = null;

  function openLightbox(id) {
    var pack = PACKS.filter(function (p) { return p.id === id; })[0];
    if (!pack) { return; }

    lastFocus = document.activeElement;
    $("lbImg").src = pack.image;
    $("lbImg").alt = pack.name + " preview";
    $("lbTitle").textContent = pack.name;
    $("lbMeta").textContent = [
      pack.category, pack.resolution, pack.size, formatDate(pack.added),
    ].filter(Boolean).join(" · ");

    var link = $("lbDownload");
    link.href = downloadHref(pack);
    link.setAttribute("data-download", pack.id);
    if (hasRealDownload(pack)) {
      link.setAttribute("download", "");
    } else {
      link.setAttribute("download", downloadName(pack));
    }

    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    $("lbDownload").focus();
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
        var url = location.origin + location.pathname + "#pack-" + copy.getAttribute("data-copy");
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
    var pack = PACKS.filter(function (p) { return p.id === id; })[0];
    if (!pack) { return; }
    if (hasRealDownload(pack)) {
      toast("Downloading " + pack.name + "…");
    } else {
      toast("Placeholder — " + pack.name + " has no link yet (blank file).");
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

    var categoryCount = buildCategories();
    wireDiscord();
    wireEvents();
    renderStats(categoryCount);
    render();

    if (location.hash.indexOf("#pack-") === 0) {
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
