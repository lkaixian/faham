/* Phone menu. On a narrow screen the header controls (pages, language, easy mode, theme, voice, status) move into ONE
   full-screen sheet behind a single big "Menu" button; on a wide screen they go back to the header.
   The nodes are moved, not copied, so every existing handler and id keeps working. No data leaves the page. */
(function () {
  const $ = (s) => document.querySelector(s);
  const btn = $("#menuBtn"), sheet = $("#menuSheet"), closeBtn = $("#menuClose"), strip = $("#paidStrip");
  const header = $("header.top"), bar = $(".top .bar"), nav = $(".top nav"), ctrls = $(".top .ctrls"), mode = $("#mode");
  if (!btn || !sheet || !header || !bar || !nav || !ctrls) return;
  const mq = matchMedia("(max-width: 960px)");
  const behind = () => [header, $("#main"), $(".foot"), strip && strip.parentElement].filter(Boolean);

  function place() {  // phone: everything in the sheet. Desktop: back where it was.
    if (mq.matches) { $("#slotNav").append(nav); $("#slotCtrls").append(ctrls); if (mode) $("#slotMode").append(mode); }
    else { bar.append(ctrls); if (mode) bar.append(mode); header.append(nav); close(false); }
  }

  function open() {
    sheet.hidden = false; btn.setAttribute("aria-expanded", "true");
    behind().forEach((e) => (e.inert = true));
    document.documentElement.style.overflow = "hidden";
    sheet.scrollTop = 0; closeBtn.focus();
  }
  function close(refocus = true) {
    if (sheet.hidden) return;
    sheet.hidden = true; btn.setAttribute("aria-expanded", "false");
    behind().forEach((e) => (e.inert = false));
    document.documentElement.style.overflow = "";
    if (refocus) btn.focus();
  }

  btn.addEventListener("click", () => (sheet.hidden ? open() : close()));
  closeBtn.addEventListener("click", () => close());
  sheet.addEventListener("click", (e) => {
    if (e.target === sheet) close();
    else if (e.target.closest("nav a")) close(false);                // the page changes through the hash; the router moves focus
    else if (e.target.closest("#paidBtn")) close(false);             // the emergency card opens on top
  });
  sheet.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { close(); return; }
    if (e.key !== "Tab") return;
    const f = [...sheet.querySelectorAll("a[href], button:not(:disabled)")].filter((x) => x.offsetParent);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  });
  addEventListener("hashchange", () => close(false));
  if (strip) strip.addEventListener("click", () => { const p = $("#paidBtn"); if (p) p.click(); });
  mq.addEventListener("change", place);
  place();
})();
