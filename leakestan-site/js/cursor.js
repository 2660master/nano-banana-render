/* ==========================================================================
   LEAKESTAN — custom cursor
   A red dot that sits exactly on the pointer and a ring that trails it.
   The ring reacts to what is underneath:
     hover  → links, buttons, selects: ring grows, dot shrinks
     view   → previews (and the lightbox backdrop): filled ring with a label
     text   → inputs: the dot becomes a caret
   Only runs for a real mouse. Touch devices and pens keep their own cursor,
   and if this script never runs the native cursor is untouched.
   ========================================================================== */
(function () {
  "use strict";

  if (!window.matchMedia) { return; }
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) { return; }

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement;

  /* Selectors per state, most specific first. An element can also opt in
     explicitly with data-cursor="view|hover" and data-cursor-label="…". */
  var TEXT = "input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, [contenteditable=true]";
  var VIEW = "[data-cursor=view], [data-open]";
  var HOVER = "[data-cursor=hover], a, button, select, label, summary, [role=button]";

  function build(className, inner) {
    var el = document.createElement("div");
    el.className = "cursor " + className;
    el.setAttribute("aria-hidden", "true");
    el.innerHTML = inner;
    document.body.appendChild(el);
    return el;
  }

  var ring = build("cursor--ring", '<div class="cursor__ring"><span class="cursor__label"></span></div>');
  var dot = build("cursor--dot", '<div class="cursor__dot"></div>');
  var label = ring.querySelector(".cursor__label");

  root.classList.add("has-cursor");

  var x = -200, y = -200;      // pointer
  var rx = x, ry = y;          // ring, eased toward the pointer
  var seen = false;
  var raf = 0;
  var EASE = reduced ? 1 : 0.2;

  function place(el, px, py) {
    el.style.transform = "translate3d(" + px + "px," + py + "px,0)";
  }

  function frame() {
    rx += (x - rx) * EASE;
    ry += (y - ry) * EASE;
    place(dot, x, y);
    place(ring, rx, ry);

    if (Math.abs(x - rx) > 0.1 || Math.abs(y - ry) > 0.1) {
      raf = window.requestAnimationFrame(frame);
    } else {
      raf = 0;
    }
  }

  function kick() {
    if (!raf) { raf = window.requestAnimationFrame(frame); }
  }

  /* The live state goes on its own attribute. It must not share a name with
     the data-cursor opt-in, or closest() would match <html> itself and the
     cursor would stick in whatever state it entered first. */
  function setState(state, text) {
    if (state) {
      root.setAttribute("data-cursor-state", state);
    } else {
      root.removeAttribute("data-cursor-state");
    }
    label.textContent = text || "";
  }

  function stateFor(target) {
    if (!target || !target.closest) { return null; }

    if (target.closest(TEXT)) { return { state: "text" }; }

    var view = target.closest(VIEW);
    if (view) {
      return { state: "view", label: view.getAttribute("data-cursor-label") || "View" };
    }

    var hover = target.closest(HOVER);
    if (hover && !hover.disabled) { return { state: "hover" }; }

    return null;
  }

  document.addEventListener("pointermove", function (event) {
    if (event.pointerType && event.pointerType !== "mouse") { return; }
    x = event.clientX;
    y = event.clientY;

    if (!seen) {
      /* First sighting: start the ring on the pointer instead of flying in. */
      seen = true;
      rx = x;
      ry = y;
    }
    root.classList.add("cursor-on");
    kick();
  }, { passive: true });

  document.addEventListener("pointerover", function (event) {
    var hit = stateFor(event.target);
    setState(hit && hit.state, hit && hit.label);
  }, { passive: true });

  /* Leaving the window (or the iframe the page lives in). */
  document.addEventListener("mouseout", function (event) {
    if (!event.relatedTarget) { root.classList.remove("cursor-on"); }
  });

  document.addEventListener("pointerdown", function () {
    root.classList.add("cursor-down");
  }, { passive: true });

  document.addEventListener("pointerup", function () {
    root.classList.remove("cursor-down");
  }, { passive: true });

  /* Content under a still pointer can change (a card re-renders, a dialog
     opens), so re-read the state after clicks and keyboard actions. */
  function recheck() {
    if (!seen) { return; }
    var under = document.elementFromPoint(x, y);
    var hit = stateFor(under);
    setState(hit && hit.state, hit && hit.label);
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
