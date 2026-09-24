/* ==========================================================================
   LEAKESTAN — custom cursor
   The LK logo is the pointer. The top-left tip of the L is the click point,
   like a normal arrow, and it follows the mouse exactly (no trailing).
     hover → over anything clickable the logo grows a little and turns white
     text  → in text fields it becomes a thin caret
     down  → squeezes while the button is held
   Only runs for a real mouse. Touch devices and pens keep their own cursor,
   and if this script never runs the native cursor is untouched.
   ========================================================================== */
(function () {
  "use strict";

  if (!window.matchMedia) { return; }
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) { return; }

  var root = document.documentElement;

  var TEXT = "input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, [contenteditable=true]";
  var HOVER = "[data-cursor], [data-open], a, button, select, label, summary, [role=button]";

  /* Same outlines as assets/wordmark.svg, inlined so CSS can recolour them. */
  var LOGO =
    '<svg class="cursor__logo" viewBox="0 0 188.93 100" aria-hidden="true">' +
      '<polygon points="24.93,0 50.93,0 32.48,74 66.48,74 60,100 0,100"/>' +
      '<polygon points="96.93,0 122.93,0 111.96,44 154.93,0 188.93,0 135.97,52 167,100 132,100 108.47,58 98,100 72,100"/>' +
    "</svg>";

  var cursor = document.createElement("div");
  cursor.className = "cursor";
  cursor.setAttribute("aria-hidden", "true");
  cursor.innerHTML = LOGO + '<span class="cursor__caret"></span>';
  document.body.appendChild(cursor);

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

  document.addEventListener("pointermove", function (event) {
    if (event.pointerType && event.pointerType !== "mouse") { return; }
    x = event.clientX;
    y = event.clientY;
    seen = true;
    root.classList.add("cursor-on");
    if (!queued) { queued = true; window.requestAnimationFrame(paint); }
  }, { passive: true });

  document.addEventListener("pointerover", function (event) {
    setState(stateFor(event.target));
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
