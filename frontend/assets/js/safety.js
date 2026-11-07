/* FAHAM safety tools that must work with no server and no internet:
   1. "I already paid" emergency card, 2. "Someone just called me" guided mode, 3. voice input.
   All text comes from i18n.js (bm, en, zh, ta). Nothing here sends data anywhere. */
(function () {
  const A = window.FAHAM_APP;
  if (!A) return;
  const { t, state, toast, esc, readAloud } = A;
  const $ = (s, r = document) => r.querySelector(s);

  /* ---------- 1. I already paid ---------- */
  const paid = $("#paid");
  let opener = null;
  function renderPaid() {
    paid.innerHTML = `<div class="wrap">
      <section class="card paidcard" aria-labelledby="pdH">
        <h2 id="pdH" tabindex="-1">${esc(t("pd_h"))}</h2>
        <div class="pstep"><h3 class="h3">${esc(t("pd_s1_h"))}</h3><p>${esc(t("pd_s1_b"))}</p></div>
        <div class="pstep"><h3 class="h3">${esc(t("pd_s2_h"))}</h3><p>${esc(t("pd_s2_b"))}</p>
          <a class="btn btn-primary btn-big call" href="tel:997">${esc(t("pd_call997"))}</a></div>
        <div class="pstep"><h3 class="h3">${esc(t("pd_s3_h"))}</h3>
          <blockquote class="script" id="pdScript" lang="${A.htmlLang[state.lang]}">${esc(t("pd_script"))}</blockquote>
          <div class="rowbtns">
            <button class="btn btn-secondary" type="button" id="pdCopy">${esc(t("pd_copy"))}</button>
            <button class="btn btn-secondary speak" type="button" id="pdSpeak"><span>${esc(t("pd_read"))}</span></button>
          </div>
          <p class="muted vnote" id="pdNote" role="status"></p></div>
        <div class="pstep"><h3 class="h3">${esc(t("pd_s4_h"))}</h3>
          <ul class="ob-list">${t("pd_ready").map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
        <p class="muted">${esc(t("pd_off"))}</p>
        <button class="btn btn-quiet btn-big" type="button" id="pdClose">${esc(t("pd_close"))}</button>
      </section></div>`;
  }
  function openPaid(from) {
    opener = from || document.activeElement;
    renderPaid(); paid.hidden = false;
    [...document.body.children].forEach((el) => { if (el !== paid && !["SCRIPT"].includes(el.tagName) && el.id !== "toast") el.inert = true; });
    document.documentElement.style.overflow = "hidden";
    $("#pdH").focus();
  }
  function closePaid() {
    A.stopSpeak(); paid.hidden = true; paid.innerHTML = "";
    [...document.body.children].forEach((el) => { if (el !== paid) el.inert = false; });
    document.documentElement.style.overflow = "";
    if (opener && opener.focus) opener.focus();
  }
  paid.addEventListener("click", (e) => {
    if (e.target.closest("#pdClose")) closePaid();
    else if (e.target.closest("#pdCopy")) A.copyText(t("pd_script"), t("copy_ok"));
    else if (e.target.closest("#pdSpeak")) readAloud(t("pd_script"), state.lang, $("#pdSpeak"), $("#pdNote"));
  });
  paid.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closePaid(); return; }
    if (e.key !== "Tab") return;
    const f = [...paid.querySelectorAll("a[href], button:not(:disabled)")].filter((x) => x.offsetParent);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  });
  $("#paidBtn").addEventListener("click", (e) => openPaid(e.currentTarget));

  /* ---------- 2. Someone just called me ---------- */
  const call = { i: 0, a: [] };
  // Moving money or giving a TAC (q2), or secrecy (q3), is a scam call on its own. Two or more "yes" answers also is.
  function callVerdict(a) {
    const n = a.filter(Boolean).length;
    return a[1] || a[2] || n >= 2 ? "scam" : n === 1 ? "caution" : "ok";
  }
  function renderCall() {
    const box = $("#callBody"); if (!box) return;
    const Q = t("cl_q");
    if (call.i < Q.length) {
      box.innerHTML = `<section class="card callcard" aria-live="polite">
        <p class="muted">${esc(t("cl_n", { n: call.i + 1 }))}</p>
        <h2 class="callq" id="callQ" tabindex="-1">${esc(Q[call.i])}</h2>
        <div class="yn">
          <button class="btn btn-big yes" type="button" data-yn="1">${esc(t("cl_yes"))}</button>
          <button class="btn btn-big no" type="button" data-yn="0">${esc(t("cl_no"))}</button>
        </div>
        ${call.i ? `<button class="btn btn-quiet" type="button" data-yn="back">&larr; ${esc(t("cl_back"))}</button>` : ""}
      </section>`;
      return;
    }
    const v = callVerdict(call.a);
    box.innerHTML = `<section class="card callres c-${v}" aria-live="assertive">
        <h2 class="hangup" id="callQ" tabindex="-1">${esc(t(v === "scam" ? "cl_scam_h" : v === "caution" ? "cl_caut_h" : "cl_ok_h"))}</h2>
        <p class="lead">${esc(t(v === "scam" ? "cl_scam_p" : v === "caution" ? "cl_caut_p" : "cl_ok_p"))}</p>
        <ol class="steps">${t("cl_steps").map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
        <button class="btn btn-primary btn-big" type="button" data-yn="paid">${esc(t("pd_btn"))}</button>
        <button class="btn btn-quiet" type="button" data-yn="again">${esc(t("cl_again"))}</button>
      </section>`;
  }
  $("#callBody").addEventListener("click", (e) => {
    const b = e.target.closest("[data-yn]"); if (!b) return;
    const k = b.dataset.yn;
    if (k === "back") { call.i = Math.max(0, call.i - 1); call.a.pop(); }
    else if (k === "again") { call.i = 0; call.a = []; }
    else if (k === "paid") { openPaid(b); return; }
    else { call.a[call.i] = k === "1"; call.i++; }
    renderCall(); const h = $("#callQ"); if (h) h.focus({ preventScroll: true });
  });

  /* ---------- 3. Voice input (Web Speech API) ---------- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const SPEECH = { bm: "ms-MY", en: "en-MY", zh: "zh-CN", ta: "ta-IN" };
  const mic = $("#micBtn"), box = $("#pasteBox");
  let rec = null, base = "";
  function micLabel() { mic.querySelector("span").textContent = t(rec ? "vi_stop" : "vi_btn"); mic.setAttribute("aria-pressed", !!rec); }
  function stopMic() { if (rec) { const r = rec; rec = null; try { r.stop(); } catch (e) {} } micLabel(); $("#vhint").textContent = ""; }
  mic.addEventListener("click", () => {
    if (rec) { stopMic(); return; }
    if (!SR) { toast(t("vi_none")); return; }
    const r = new SR();
    r.lang = SPEECH[state.xl] || SPEECH[state.lang] || "ms-MY"; r.interimResults = true; r.continuous = true;
    base = box.value ? box.value.replace(/\s+$/, "") + " " : "";
    r.onresult = (ev) => {
      let s = ""; for (let i = 0; i < ev.results.length; i++) s += ev.results[i][0].transcript;
      box.value = base + s; box.dispatchEvent(new Event("input", { bubbles: true }));
    };
    r.onerror = () => { stopMic(); toast(t("vi_err")); };
    r.onend = () => { if (rec) stopMic(); };
    rec = r; try { r.start(); } catch (e) { rec = null; toast(t("vi_err")); return; }
    micLabel(); $("#vhint").textContent = t("vi_on");
  });

  window.FAHAM_SAFETY = { openPaid, closePaid, renderCall, refresh() { micLabel(); renderCall(); if (!paid.hidden) renderPaid(); }, callVerdict };
  micLabel(); renderCall();
})();
