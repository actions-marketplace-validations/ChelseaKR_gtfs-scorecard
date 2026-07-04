// @ts-check
/* Mobile menu toggle for the primary nav. On wide screens the nav cluster is
 * always visible and this does nothing; on narrow screens it opens/closes the
 * drop panel. The button carries aria-expanded; Escape and an outside click
 * close it. Keyboard users tab straight into the links when open. */
(function () {
  "use strict";
  var header = document.querySelector(".site-header");
  var btn = header && header.querySelector(".nav-menu-btn");
  if (!header || !(btn instanceof HTMLElement)) return;

  function isOpen() {
    return header.classList.contains("nav-open");
  }
  function close() {
    header.classList.remove("nav-open");
    btn.setAttribute("aria-expanded", "false");
  }
  function open() {
    header.classList.add("nav-open");
    btn.setAttribute("aria-expanded", "true");
  }

  btn.addEventListener("click", function () {
    isOpen() ? close() : open();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen()) {
      close();
      btn.focus();
    }
  });
  document.addEventListener("click", function (e) {
    if (isOpen() && e.target instanceof Node && !header.contains(e.target)) close();
  });
})();
