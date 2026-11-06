/* FAHAM frontend config.
   Set API_BASE to your backend (e.g. "http://localhost:8000").
   If the API is unreachable, the dashboard runs in demo mode in the browser. */
window.FAHAM_CONFIG = {
  API_BASE: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : "",
  INTRO_ONCE_PER_SESSION: true
};
