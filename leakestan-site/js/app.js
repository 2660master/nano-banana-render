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
  var NEW_DAYS = typeof CFG.NEW_DAYS === "number" ? CFG.NEW_DAYS : 7;

  /* "home" is the catch-all tab — it lists every entry. */
  var HOME = "home";

  var $ = function (id) { return document.getElementById(id); };

  var grid = $("grid");
  var empty = $("empty");
  var search = $("search");
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

  function formatNumber(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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

  /* "New" = added today or within the NEW_DAYS days before it. Both sides
     are compared as whole UTC days, since `added` is a plain YYYY-MM-DD. */
  function isNew(item) {
    var added = new Date(item.added);
    if (isNaN(added.getTime())) { return false; }
    var now = new Date();
    var today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    var days = Math.floor((today - added.getTime()) / 86400000);
    return days >= 0 && days < NEW_DAYS;
  }

  function tagsFor(item) {
    return Array.isArray(item.tags) ? item.tags.filter(Boolean) : [];
  }

  function labelsMarkup(item) {
    var chips = [];
    if (isNew(item)) { chips.push('<span class="chip chip--new">New</span>'); }
    tagsFor(item).forEach(function (tag) {
      chips.push('<span class="chip">' + esc(tag) + "</span>");
    });
    return chips.length ? '<span class="card__labels">' + chips.join("") + "</span>" : "";
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
      /* Tags are searchable too, so "1.21" finds every client tagged with it. */
      return (item.name + " " + item.category + " " + tagsFor(item).join(" "))
        .toLowerCase().indexOf(q) !== -1;
    });

    return newestFirst(list);
  }

  /* ── Rendering ────────────────────────────────────────────────────── */

  function cardMarkup(item, position) {
    var blank = !hasRealDownload(item);

    /* The preview is just a picture — the Download button is the only
       thing on a card you can click. */
    return '<article class="card" id="item-' + esc(item.id) + '" style="--i:' + position + '">' +
      '<div class="card__shot">' +
        '<img class="card__img" src="' + esc(item.image) + '" alt="' + esc(item.name) + ' preview" ' +
          (item.focus ? 'style="object-position:' + esc(item.focus) + '" ' : "") +
          'loading="lazy" decoding="async">' +
        labelsMarkup(item) +
      "</div>" +
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

  /* Odometer: each digit is a column of numbers that rolls upward and stops
     on its place in the target. Every column starts at 0; the further right,
     the more laps it runs and the later it settles, like a real counter. */
  var ODO_LINE = 1.15;   // em — must match .odo line-height in styles.css

  function rollUp(el, target) {
    if (!el) { return; }
    var text = formatNumber(target);
    el.setAttribute("aria-label", text);

    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !el.animate) { el.textContent = text; return; }

    el.textContent = "";
    el.classList.add("odo");

    var place = 0;
    text.split("").forEach(function (ch) {
      if (!/\d/.test(ch)) {
        var sep = document.createElement("span");
        sep.className = "odo__sep";
        sep.setAttribute("aria-hidden", "true");
        sep.textContent = ch;
        el.appendChild(sep);
        return;
      }

      place += 1;
      var steps = place * 10 + Number(ch);   // `place` full laps, then the digit
      var column = [];
      for (var k = 0; k <= steps; k++) { column.push(k % 10); }

      var box = document.createElement("span");
      box.className = "odo__digit";
      box.setAttribute("aria-hidden", "true");
      var strip = document.createElement("span");
      strip.className = "odo__strip";
      strip.textContent = column.join("\n");
      box.appendChild(strip);
      el.appendChild(box);

      strip.animate(
        [{ transform: "translateY(0)" }, { transform: "translateY(" + (-steps * ODO_LINE) + "em)" }],
        { duration: 1300 + place * 220, easing: "cubic-bezier(.15,.85,.25,1)", fill: "forwards" }
      );
    });
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

  /* Deterministic 32-bit hash: the same day number always gives the same
     "random" value, so every visitor sees an identical total. */
  function dayHash(n) {
    var x = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b) >>> 0;
    x ^= x >>> 13;
    x = Math.imul(x, 0xc2b2ae35) >>> 0;
    x ^= x >>> 16;
    return x >>> 0;
  }

  /* start on `since`, then + a per-day amount in [min, max] for every UTC
     midnight that has passed since. Never decreases. */
  function downloadTotal() {
    var cfg = CFG.DOWNLOADS || {};
    var total = Number(cfg.start) || 0;
    var since = Date.parse(cfg.since);
    if (isNaN(since)) { return total; }
    var min = Number(cfg.min) || 0;
    var max = Math.max(Number(cfg.max) || 0, min);
    var now = new Date();
    var today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    var days = Math.floor((today - since) / 86400000);
    for (var d = 1; d <= days; d++) {
      total += min + (dayHash(d) % (max - min + 1));
    }
    return total;
  }

  function renderHero() {
    var clients = ITEMS.filter(function (item) { return item.category === "clients"; }).length;
    var downloads = downloadTotal();
    whenIntroDone(function () {
      rollUp($("statClients"), clients);
      rollUp($("statDownloads"), downloads);
    });

    var latest = newestFirst(ITEMS);

    /* Three newest previews, fanned out on the right. */
    var stack = $("heroStack");
    if (stack) {
      stack.innerHTML = latest.slice(0, 3).map(function (item, i) {
        return '<img class="hero__shot hero__shot--' + (i + 1) + '" src="' + esc(item.image) + '" alt="" ' +
          'decoding="async">';
      }).join("");
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

    grid.addEventListener("click", function (event) {
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

    $("menuToggle").addEventListener("click", function () {
      setSidebar(!sidebar.classList.contains("is-open"));
    });
    backdrop.addEventListener("click", function () { setSidebar(false); });

    document.addEventListener("keydown", function (event) {
      var cmdK = (event.metaKey || event.ctrlKey) && (event.key === "k" || event.key === "K");

      if (event.key === "Escape") {
        setSidebar(false);
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
