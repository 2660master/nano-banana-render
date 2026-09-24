/* ==========================================================================
   LEAKESTAN — visual effects
   Intro, scroll progress, back-to-top, card reveal, card tilt + glare and
   image fade-in. (The click explosion lives in cursor.js.) Everything here
   is decoration: if this
   file fails to load, the site still works and nothing stays hidden.
   ========================================================================== */
(function () {
  "use strict";

  var root = document.documentElement;
  var $ = function (id) { return document.getElementById(id); };

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ── Intro ────────────────────────────────────────────────────────── */

  var introDone = root.classList.contains("intro-skip");
  var introWaiters = [];

  function afterIntro(fn) {
    if (introDone) { fn(); } else { introWaiters.push(fn); }
  }

  function finishIntro() {
    if (introDone) { return; }
    introDone = true;

    var loader = $("loader");
    if (loader) {
      loader.classList.add("is-done");
      window.setTimeout(function () {
        if (loader.parentNode) { loader.parentNode.removeChild(loader); }
      }, 800);
    }
    try { window.sessionStorage.setItem("leakestan:intro", "1"); } catch (err) { /* private mode */ }

    introWaiters.splice(0).forEach(function (fn) { fn(); });
    document.dispatchEvent(new CustomEvent("leakestan:intro-done"));
  }

  function setupIntro() {
    var loader = $("loader");
    if (introDone) {
      if (loader && loader.parentNode) { loader.parentNode.removeChild(loader); }
      return;
    }
    /* Give the bar a moment to fill, but never hold the page past 1.4s. */
    var start = Date.now();
    window.addEventListener("load", function () {
      window.setTimeout(finishIntro, Math.max(0, 900 - (Date.now() - start)));
    });
    window.setTimeout(finishIntro, 1400);
  }

  /* ── Scroll progress + back to top ────────────────────────────────── */

  function setupScroll() {
    var bar = $("progressBar");
    var toTop = $("toTop");
    var topbar = document.querySelector(".topbar");
    var queued = false;

    function update() {
      queued = false;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var ratio = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
      if (bar) { bar.style.transform = "scaleX(" + ratio + ")"; }
      if (topbar) { topbar.classList.toggle("is-scrolled", window.scrollY > 8); }
      if (toTop) {
        var show = window.scrollY > 520;
        if (show && toTop.hidden) { toTop.hidden = false; }
        toTop.classList.toggle("is-on", show);
      }
    }

    window.addEventListener("scroll", function () {
      if (!queued) { queued = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();

    if (toTop) {
      toTop.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
      });
    }
  }

  /* ── Card reveal ──────────────────────────────────────────────────── */

  var observer = null;

  function setupReveal() {
    if (reduced || !("IntersectionObserver" in window)) { return; }

    observer = new IntersectionObserver(function (entries) {
      var batch = 0;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) { return; }
        var card = entry.target;
        /* Cards arriving together cascade in, a beat apart. */
        card.style.setProperty("--reveal-delay", Math.min(batch, 6) * 70 + "ms");
        card.classList.add("is-in");
        batch += 1;
        observer.unobserve(card);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.08 });

    root.classList.add("reveal-ready");

    /* Safety net: if anything goes wrong, show every card anyway. */
    window.setTimeout(function () {
      Array.prototype.forEach.call(document.querySelectorAll(".card:not(.is-in)"), function (card) {
        var box = card.getBoundingClientRect();
        if (box.top < window.innerHeight) { card.classList.add("is-in"); }
      });
    }, 3200);
  }

  function observeCards() {
    if (!observer) { return; }
    afterIntro(function () {
      Array.prototype.forEach.call(document.querySelectorAll(".card:not(.is-in)"), function (card) {
        observer.observe(card);
      });
    });
  }

  /* ── Image fade-in ────────────────────────────────────────────────── */

  function markLoaded(img) {
    var holder = img.closest(".card__shot") || img;
    holder.classList.add("is-loaded");
  }

  function checkImages() {
    Array.prototype.forEach.call(document.querySelectorAll(".card__img, .hero__shot"), function (img) {
      if (img.complete && img.naturalWidth > 0) { markLoaded(img); }
    });
  }

  function setupImages() {
    /* load/error don't bubble, so listen in the capture phase. */
    document.addEventListener("load", function (event) {
      var t = event.target;
      if (t && t.tagName === "IMG") { markLoaded(t); }
    }, true);
    document.addEventListener("error", function (event) {
      var t = event.target;
      if (t && t.tagName === "IMG") {
        markLoaded(t);
        var holder = t.closest(".card__shot");
        if (holder) { holder.classList.add("is-broken"); }
      }
    }, true);
    checkImages();
  }

  /* ── Tilt + glare ─────────────────────────────────────────────────── */

  function setupTilt() {
    if (reduced || !finePointer) { return; }
    var grid = $("grid");
    if (!grid) { return; }

    var active = null;
    var pending = null;
    var queued = false;

    function apply() {
      queued = false;
      if (!pending) { return; }
      var card = pending.card;
      var box = card.getBoundingClientRect();
      var px = (pending.x - box.left) / box.width;
      var py = (pending.y - box.top) / box.height;
      card.style.setProperty("--rx", ((0.5 - py) * 7).toFixed(2) + "deg");
      card.style.setProperty("--ry", ((px - 0.5) * 9).toFixed(2) + "deg");
      card.style.setProperty("--gx", (px * 100).toFixed(1) + "%");
      card.style.setProperty("--gy", (py * 100).toFixed(1) + "%");
    }

    function reset(card) {
      card.classList.remove("is-tilting");
      card.style.removeProperty("--rx");
      card.style.removeProperty("--ry");
    }

    grid.addEventListener("pointermove", function (event) {
      if (event.pointerType !== "mouse" || grid.classList.contains("is-list")) { return; }
      var card = event.target.closest(".card");
      if (!card) { return; }
      if (active && active !== card) { reset(active); }
      active = card;
      card.classList.add("is-tilting");
      pending = { card: card, x: event.clientX, y: event.clientY };
      if (!queued) { queued = true; window.requestAnimationFrame(apply); }
    });

    grid.addEventListener("pointerout", function (event) {
      if (!active) { return; }
      if (event.relatedTarget && active.contains(event.relatedTarget)) { return; }
      reset(active);
      active = null;
      pending = null;
    });
  }

  /* ── Boot ─────────────────────────────────────────────────────────── */

  function onRender() {
    observeCards();
    checkImages();
  }

  function init() {
    /* Opt-in flag for effects that hide things until JS reveals them. */
    root.classList.add("fx-ready");
    setupIntro();
    setupScroll();
    setupReveal();
    setupImages();
    setupTilt();
    onRender();
    document.addEventListener("leakestan:render", onRender);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
