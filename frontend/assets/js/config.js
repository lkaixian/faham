/* Tulen frontend config.
   API_BASE is where /api/... lives:
   - localhost: the API container on :8000 directly
   - github.io: "" (no API; the site runs in sample mode)
   - anywhere else (a Cloudflare Tunnel, a LAN address, your own domain): the same address the page was opened from,
     because nginx forwards /api/ to the API container.
   If the API is unreachable, the site runs in sample mode (examples only). */
(function () {
  var h = window.location.hostname;
  window.FAHAM_CONFIG = {
    API_BASE: h === "localhost" || h === "127.0.0.1" ? "http://localhost:8000"
      : /\.github\.io$/.test(h) ? ""
      : window.location.origin
  };
})();
