/* Google Analytics 4 loader, shared by every page.
 *
 * Set MEASUREMENT_ID to your GA4 id (looks like G-XXXXXXXXXX) to turn it on.
 * Until a real id is set this is a no-op: no Google script is loaded and no
 * data is sent, so it is safe to ship before the property exists. */
(function () {
  var MEASUREMENT_ID = "G-XXXXXXXXXX";
  if (!MEASUREMENT_ID || MEASUREMENT_ID.indexOf("XXXX") !== -1) return;

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
  document.head.appendChild(s);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", MEASUREMENT_ID);
})();
