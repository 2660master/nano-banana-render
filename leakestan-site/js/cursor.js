/* ==========================================================================
   LEAKESTAN — cursor + click explosion
   A standard pointer, in red: an arrow, a hand over anything clickable and a
   caret in text fields. Every click sets off a small red explosion where you
   clicked (on phones too, on tap).

   Size: CURSOR_SIZE in data/content.js, 1 (small) … 5 (big). The explosion
   grows with it.

   Self-contained: this file brings its own styles, so any page can include
   it (the 404 page does). With no mouse the pointer stays native; if this
   file never loads, nothing on the page depends on it.
   ========================================================================== */
(function () {
  "use strict";

  /* Visible height of the pointer in CSS pixels, for sizes 1–5. */
  var SIZES = [16, 20, 24, 30, 36];

  var root = document.documentElement;
  var CFG = window.LEAKESTAN || {};
  var mq = function (q) { return window.matchMedia ? window.matchMedia(q).matches : false; };
  var reduced = mq("(prefers-reduced-motion: reduce)");
  var fine = mq("(hover: hover) and (pointer: fine)");

  var size = SIZES[2];

  /* ── Styles ───────────────────────────────────────────────────────── */

  var css =
    ".has-cursor,.has-cursor *{cursor:none!important}" +
    ".lk-cursor{position:fixed;top:0;left:0;z-index:2147483000;width:0;height:0;pointer-events:none;" +
      "opacity:0;transition:opacity .15s ease;will-change:transform}" +
    ".cursor-on .lk-cursor{opacity:1}" +
    ".lk-cursor svg{position:absolute;overflow:visible;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.6));" +
      "transition:transform .12s cubic-bezier(.16,1,.3,1)}" +
    ".lk-cursor__hand,.lk-cursor__caret{display:none}" +
    "html[data-cursor-state=hover] .lk-cursor__arrow{display:none}" +
    "html[data-cursor-state=hover] .lk-cursor__hand{display:block}" +
    "html[data-cursor-state=text] .lk-cursor__arrow{display:none}" +
    "html[data-cursor-state=text] .lk-cursor__caret{display:block}" +
    ".lk-cursor__caret{position:absolute;border-radius:1px;background:#ff3b50;" +
      "box-shadow:0 0 0 1px rgba(10,7,8,.85)}" +
    ".cursor-down .lk-cursor svg{transform:scale(.88)}" +
    ".lk-boom{position:fixed;left:0;top:0;z-index:2147483001;width:0;height:0;pointer-events:none}" +
    ".lk-boom span{position:absolute;left:0;top:0;border-radius:50%;pointer-events:none;will-change:transform,opacity}" +
    ".lk-boom__ring{border:2px solid #ff5464;box-shadow:0 0 14px rgba(245,37,59,.85),inset 0 0 10px rgba(245,37,59,.55)}" +
    ".lk-boom__flash{background:radial-gradient(circle,#fff 0%,#ffd0d4 22%,#ff5464 48%,rgba(245,37,59,0) 72%)}" +
    ".lk-boom__spark{border-radius:2px!important;transform-origin:50% 0;" +
      "background:linear-gradient(180deg,#fff,#ff5464 45%,rgba(245,37,59,0))}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  /* ── Explosion ────────────────────────────────────────────────────── */

  var COLORS = ["#ff5464", "#f5253b", "#ff2a3d", "#ff9aa4", "#ffd0d4"];
  var EASE_OUT = "cubic-bezier(.16,1,.3,1)";
  var live = [];

  function boom(x, y) {
    if (!document.body || !document.body.animate) { return; }

    /* Rapid clicking: keep at most six going at once. */
    if (live.length >= 6) {
      var old = live.shift();
      if (old.parentNode) { old.parentNode.removeChild(old); }
    }

    var s = size / 24;                       // explosion scales with the pointer
    var R = 26 * s;                          // blast radius
    var host = document.createElement("div");
    host.className = "lk-boom";
    host.style.transform = "translate(" + x + "px," + y + "px)";
    document.body.appendChild(host);
    live.push(host);

    function piece(cls, w, h) {
      var el = document.createElement("span");
      el.className = cls;
      el.style.width = w + "px";
      el.style.height = h + "px";
      el.style.marginLeft = -w / 2 + "px";
      el.style.marginTop = -h / 2 + "px";
      host.appendChild(el);
      return el;
    }

    var ring = piece("lk-boom__ring", R * 2, R * 2);
    ring.style.borderWidth = Math.max(1.5, 2 * s) + "px";
    ring.animate(
      [{ transform: "scale(.15)", opacity: 1 }, { transform: "scale(1)", opacity: 0 }],
      { duration: reduced ? 260 : 520, easing: EASE_OUT, fill: "forwards" }
    );

    var F = 14 * s;
    piece("lk-boom__flash", F * 2, F * 2).animate(
      [{ transform: "scale(.5)", opacity: 1 }, { transform: "scale(1.35)", opacity: 0 }],
      { duration: 300, easing: "ease-out", fill: "forwards" }
    );

    if (!reduced) {
      /* Embers flying outward: white-hot centres, red glow, and they stay
         bright for the first half of the flight before burning out. */
      var n = 16;
      for (var i = 0; i < n; i++) {
        var ang = (i / n) * Math.PI * 2 + (Math.random() - 0.5) * 0.55;
        var dist = R * (0.9 + Math.random() * 0.65);
        var d = (3.4 + Math.random() * 3.2) * s;
        var c = COLORS[i % COLORS.length];
        var bit = piece("lk-boom__bit", d, d);
        bit.style.background = "radial-gradient(circle, #fff 0 28%, " + c + " 62%)";
        bit.style.boxShadow = "0 0 " + 8 * s + "px " + 1.5 * s + "px " + c;
        bit.animate(
          [
            { transform: "translate(0,0) scale(1)", opacity: 1 },
            { opacity: 1, offset: 0.5 },
            { transform: "translate(" + Math.cos(ang) * dist + "px," + Math.sin(ang) * dist + "px) scale(.25)", opacity: 0 }
          ],
          { duration: 460 + Math.random() * 260, easing: "cubic-bezier(.12,.8,.3,1)", fill: "forwards" }
        );
      }

      /* A few bright streaks. */
      for (var j = 0; j < 6; j++) {
        var a = j * 60 + Math.random() * 30;
        var w = Math.max(1.5, 2 * s);
        var spark = document.createElement("span");
        spark.className = "lk-boom__spark";
        spark.style.width = w + "px";
        spark.style.height = R * (0.55 + Math.random() * 0.3) + "px";
        spark.style.marginLeft = -w / 2 + "px";
        host.appendChild(spark);
        spark.animate(
          [
            { transform: "rotate(" + a + "deg) translateY(" + R * 0.15 + "px) scaleY(.2)", opacity: 1 },
            { transform: "rotate(" + a + "deg) translateY(" + R * 0.9 + "px) scaleY(1)", opacity: 0 }
          ],
          { duration: 380, easing: EASE_OUT, fill: "forwards" }
        );
      }
    }

    window.setTimeout(function () {
      if (host.parentNode) { host.parentNode.removeChild(host); }
      var k = live.indexOf(host);
      if (k !== -1) { live.splice(k, 1); }
    }, 900);
  }

  /* Mouse: explode on press, for instant feedback. Touch/pen: on the tap's
     click, so scrolling a page doesn't set anything off. Keyboard-triggered
     clicks (detail 0) have no position and are skipped. */
  var lastType = "mouse";
  document.addEventListener("pointerdown", function (e) {
    lastType = e.pointerType || "mouse";
    if (lastType === "mouse" && e.button === 0) { boom(e.clientX, e.clientY); }
  }, { passive: true, capture: true });
  document.addEventListener("click", function (e) {
    if (lastType !== "mouse" && e.detail > 0) { boom(e.clientX, e.clientY); }
  }, true);

  /* ── Pointer (mouse only) ─────────────────────────────────────────── */

  var cursor = null;
  var arrow, hand, caret;

  /* Arrow: tip at (2,2) in a 20×28 box, 23.6 units tall.
     Hand: fingertip at (9.5,1.5) in a 24×24 box, 21.5 units tall. */
  var ARROW =
    '<svg class="lk-cursor__arrow" viewBox="0 0 20 28" aria-hidden="true">' +
      '<defs><linearGradient id="lkArrowFill" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="#ff5a6a"/><stop offset="1" stop-color="#d60f28"/>' +
      "</linearGradient></defs>" +
      '<path d="M2 2L2 22.5L7.4 17.4L11 25.6L14.4 24.1L10.9 16L18 16Z" fill="url(#lkArrowFill)" ' +
        'stroke="#0a0708" stroke-width="2.4" stroke-linejoin="round" paint-order="stroke"/>' +
    "</svg>";

  var HAND =
    '<svg class="lk-cursor__hand" viewBox="0 0 24 24" aria-hidden="true">' +
      '<defs><linearGradient id="lkHandFill" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="#ff5a6a"/><stop offset="1" stop-color="#d60f28"/>' +
      "</linearGradient></defs>" +
      '<path d="M9.5 1.5C10.6 1.5 11.5 2.4 11.5 3.5L11.5 10.2C11.9 9.6 12.6 9.3 13.3 9.4C14.3 9.5 14.9 10.2 15 11' +
        "C15.4 10.5 16.1 10.2 16.8 10.4C17.7 10.7 18.2 11.5 18.2 12.3C18.6 11.9 19.3 11.8 19.9 12.1" +
        "C20.6 12.5 21 13.2 21 14L21 17.5C21 20.5 18.6 23 15.6 23L12.4 23C10.6 23 9 22.2 7.9 20.8" +
        'L4.4 16.3C3.8 15.5 3.9 14.4 4.7 13.8C5.4 13.3 6.4 13.4 7 14L7.5 14.6L7.5 3.5C7.5 2.4 8.4 1.5 9.5 1.5Z" ' +
        'fill="url(#lkHandFill)" stroke="#0a0708" stroke-width="2.2" stroke-linejoin="round" paint-order="stroke"/>' +
      '<path d="M11.5 10.2V14M15 11V14.5M18.2 12.3V15" fill="none" stroke="#0a0708" stroke-width="1.1" ' +
        'stroke-linecap="round" opacity=".75"/>' +
    "</svg>";

  function place(el, box, hotX, hotY, unit) {
    el.style.width = box[0] * unit + "px";
    el.style.height = box[1] * unit + "px";
    el.style.left = -hotX * unit + "px";
    el.style.top = -hotY * unit + "px";
    /* Press feedback shrinks toward the hotspot, not the middle. */
    el.style.transformOrigin = hotX * unit + "px " + hotY * unit + "px";
  }

  function setSize(n) {
    var pick = parseInt(n, 10);
    if (!(pick >= 1 && pick <= SIZES.length)) { pick = 3; }
    size = SIZES[pick - 1];
    if (!cursor) { return pick; }
    place(arrow, [20, 28], 2, 2, size / 23.6);
    place(hand, [24, 24], 9.5, 1.5, size / 21.5);
    var cw = Math.max(2, size / 12);
    var ch = Math.round(size * 1.05);
    caret.style.width = cw + "px";
    caret.style.height = ch + "px";
    caret.style.left = -cw / 2 + "px";
    caret.style.top = -ch / 2 + "px";
    return pick;
  }

  /* Exposed so a page can switch sizes live (used by the size picker). */
  window.LeakestanCursor = { setSize: setSize, boom: boom, sizes: SIZES.slice() };

  if (!fine) {
    setSize(CFG.CURSOR_SIZE);
    return;
  }

  var TEXT = "input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, [contenteditable=true]";
  var HOVER = "[data-cursor], [data-open], a, button, select, label, summary, [role=button]";

  cursor = document.createElement("div");
  cursor.className = "lk-cursor";
  cursor.setAttribute("aria-hidden", "true");
  cursor.innerHTML = ARROW + HAND + '<span class="lk-cursor__caret"></span>';
  document.body.appendChild(cursor);
  arrow = cursor.querySelector(".lk-cursor__arrow");
  hand = cursor.querySelector(".lk-cursor__hand");
  caret = cursor.querySelector(".lk-cursor__caret");
  setSize(CFG.CURSOR_SIZE);
  root.classList.add("has-cursor");

  var x = -200, y = -200;
  var seen = false;
  var queued = false;

  function paint() {
    queued = false;
    cursor.style.transform = "translate3d(" + x + "px," + y + "px,0)";
  }

  function setState(state) {
    if (state) {
      root.setAttribute("data-cursor-state", state);
    } else {
      root.removeAttribute("data-cursor-state");
    }
  }

  function stateFor(target) {
    if (!target || !target.closest) { return null; }
    if (target.closest(TEXT)) { return "text"; }
    var hover = target.closest(HOVER);
    if (hover && !hover.disabled) { return "hover"; }
    return null;
  }

  document.addEventListener("pointermove", function (e) {
    if (e.pointerType && e.pointerType !== "mouse") { return; }
    x = e.clientX;
    y = e.clientY;
    seen = true;
    root.classList.add("cursor-on");
    if (!queued) { queued = true; window.requestAnimationFrame(paint); }
  }, { passive: true });

  document.addEventListener("pointerover", function (e) {
    setState(stateFor(e.target));
  }, { passive: true });

  /* Leaving the window (or the iframe the page lives in). */
  document.addEventListener("mouseout", function (e) {
    if (!e.relatedTarget) { root.classList.remove("cursor-on"); }
  });

  document.addEventListener("pointerdown", function () { root.classList.add("cursor-down"); }, { passive: true });
  document.addEventListener("pointerup", function () { root.classList.remove("cursor-down"); }, { passive: true });

  /* Content under a still pointer can change (a card re-renders, a dialog
     opens), so re-read the state after clicks, keys and scrolling. */
  function recheck() {
    if (!seen) { return; }
    setState(stateFor(document.elementFromPoint(x, y)));
  }
  document.addEventListener("click", function () { window.setTimeout(recheck, 30); });
  document.addEventListener("keyup", function () { window.setTimeout(recheck, 30); });

  var scrollQueued = false;
  window.addEventListener("scroll", function () {
    if (!seen || scrollQueued) { return; }
    scrollQueued = true;
    window.requestAnimationFrame(function () {
      scrollQueued = false;
      recheck();
    });
  }, { passive: true });
})();
