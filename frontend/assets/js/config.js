/* FAHAM frontend config.
   Set API_BASE to your backend (e.g. "http://localhost:8000").
   If the API is unreachable, the site runs in sample mode (examples only). */
window.FAHAM_CONFIG = {
  API_BASE: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : ""
};
