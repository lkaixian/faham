/* FAHAM front end: vanilla JS, no build step.
   Flow: form or example -> POST /api/analyze (or local sample when offline) -> one result object -> renderResult.
   UI strings live in i18n.js (window.FAHAM_T); t() and data-i18n attributes read from it. */
(function () {
  const D = window.FAHAM_DATA;
  const T = window.FAHAM_T;
  const CFG = window.FAHAM_CONFIG || {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // the product never calls a message "genuine"; scrub it from any text that comes back from outside
  const clean = (s) => String(s ?? "").replace(/\blikely genuine\b/gi, "no scam signs found").replace(/\bgenuine\b/gi, "official-looking");

  const store = {
    get(k, d) { try { const v = localStorage.getItem("faham_" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("faham_" + k, JSON.stringify(v)); } catch (e) {} }
  };
  const LANGS = Object.keys(D.languages);
  const state = {
    lang: LANGS.includes(store.get("lang", "bm")) ? store.get("lang", "bm") : "bm",
    xl: "bm", xlManual: false,           // xl = language of the explanation; follows the UI language unless detected or chosen
    theme: store.get("theme", "light"),
    learned: new Set(store.get("learned", [])),
    xp: store.get("xp", 0),
    voice: store.get("voice", true), all: store.get("all", false), step: 0,   // voice: auto-read on by default; all: whole result on one page
    api: false, mode: "wait", busy: false, tts: { available: false, langs: [] },
    result: null, last: null, route: "online", retry: null,
    practice: { items: D.practice, order: [], i: 0, score: 0, answered: false, results: [] }
  };
  state.xl = state.lang;
  const CONSENT_V = 1;
  const consented = () => (store.get("consent", null) || {}).v === CONSENT_V;
  const save = () => { store.set("lang", state.lang); store.set("learned", [...state.learned]); store.set("xp", state.xp); store.set("theme", state.theme); };
  const HTML_LANG = { bm: "ms", en: "en", zh: "zh", ta: "ta" };

  /* ---------- i18n ---------- */
  const t = (k, v) => {
    let s = (T[state.lang] && T[state.lang][k]) ?? T.en[k] ?? k;
    if (v && typeof s === "string") s = s.replace(/\{(\w+)\}/g, (m, x) => (v[x] ?? m));
    return s;
  };
  // translate a string from the sample data (keyed by its original text); unknown strings pass through
  const tr = (s) => { const a = D.tr[s] || D.tr[String(s).charAt(0).toUpperCase() + String(s).slice(1)]; return (a && a[LANGS.indexOf(state.lang)]) || s; };
  const langName = (l) => D.languages[l].name;
  function applyI18n() {
    document.documentElement.lang = HTML_LANG[state.lang];
    $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
    $$("[data-i18n-aria]").forEach((el) => el.setAttribute("aria-label", t(el.dataset.i18nAria)));
    $("#aboutReview").hidden = !["zh", "ta"].includes(state.lang);
    if (!cur) $$(".speak").forEach((b) => setSpeakBtn(b, "idle"));
  }

  /* ---------- icons (inline SVG, no emoji) ---------- */
  const ICON = {
    likely_scam: '<path d="M12 2 4 5v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V5l-8-3z"/><path d="m9.5 9.5 5 5m0-5-5 5"/>',
    caution: '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4m0 3h.01"/>',
    no_signals: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    risk: '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4m0 3h.01"/>',
    ok: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
    speaker: '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/>',
    doc: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
    device: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    phone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    scale: '<path d="M12 3v18M6 21h12M5 7h14"/><path d="m5 7-3 7a3.5 3.5 0 0 0 6 0L5 7zm14 0-3 7a3.5 3.5 0 0 0 6 0l-3-7z"/>'
  };
  const svg = (n) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICON[n]}</svg>`;

  /* ---------- small helpers ---------- */
  function toast(msg) {
    const el = $("#toast"); el.textContent = msg; el.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(() => el.classList.remove("show"), 3000);
  }
  function copyText(text, done) {
    const ok = () => toast(done || t("copy_ok"));
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, () => toast(t("copy_fail")));
    else toast(t("copy_fail"));
  }

  /* ---------- read aloud: ILMU via POST /api/tts, browser voice as fallback ----------
     Only text that came back in the API result (already redacted) is sent, never the pasted input. */
  let cur = null;                    // the read-aloud in progress: { btn, note, ctrl?, audio?, url? }
  const ttsCache = new Map();        // "lang\ntext" -> Blob, so the same text is not paid for twice
  const ttsOk = (l) => state.api && state.tts.available && state.tts.langs.includes(l);
  function setSpeakBtn(btn, mode) {
    if (!btn) return;
    btn.querySelector("span").textContent = t(mode === "loading" ? "loading" : mode === "playing" ? "stop" : btn.dataset.idle || "listen");
    btn.setAttribute("aria-busy", mode === "loading");
  }
  function stopSpeak() {
    try { speechSynthesis.cancel(); } catch (e) {}
    if (cur) {
      const c = cur; cur = null;
      if (c.ctrl) c.ctrl.abort();
      if (c.audio) { c.audio.onended = c.audio.onerror = null; c.audio.pause(); }
      if (c.url) URL.revokeObjectURL(c.url);
    }
    $$(".speak").forEach((b) => setSpeakBtn(b, "idle"));
  }
  // browsers refuse audio without a recent tap: show a big button instead of failing silently
  function blocked() { stopSpeak(); const b = $("#tapListen"); if (b) b.hidden = false; }
  function browserSpeak(text, lang, me) {
    if (!("speechSynthesis" in window)) { toast(t("no_speech")); stopSpeak(); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = D.languages[lang].speech; u.rate = 0.9;
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.toLowerCase().startsWith(u.lang.slice(0, 2).toLowerCase()));
    if (v) u.voice = v; else toast(t("no_voice", { n: langName(lang) }));
    u.onend = () => { if (cur === me) stopSpeak(); };
    u.onerror = (ev) => { if (cur === me) (ev.error === "not-allowed" ? blocked() : stopSpeak()); };
    me.note.textContent = t("vnote");
    setSpeakBtn(me.btn, "playing");
    speechSynthesis.speak(u);
  }
  async function readAloud(text, lang, btn, note) {
    if (cur) { stopSpeak(); return; }                 // second tap = stop (also cancels a download)
    note.textContent = "";
    const me = (cur = { btn, note });
    if (ttsOk(lang)) {
      setSpeakBtn(btn, "loading");
      try {
        const body = text.slice(0, 3000), key = lang + "\n" + body;
        let blob = ttsCache.get(key);
        if (!blob) {
          me.ctrl = new AbortController(); const to = setTimeout(() => me.ctrl.abort(), 25000);
          const res = await fetch(CFG.API_BASE + "/api/tts", { method: "POST", headers: { "Content-Type": "application/json" }, signal: me.ctrl.signal, body: JSON.stringify({ text: body, language: lang }) });
          clearTimeout(to);
          if (!res.ok) throw new Error(res.status);
          blob = await res.blob();
          if (!blob.size) throw new Error("empty");
          if (ttsCache.size >= 8) ttsCache.delete(ttsCache.keys().next().value);
          ttsCache.set(key, blob);
        }
        if (cur !== me) return;                        // stopped while loading
        me.url = URL.createObjectURL(blob); me.audio = new Audio(me.url);
        me.audio.onended = me.audio.onerror = () => { if (cur === me) stopSpeak(); };
        await me.audio.play();
        if (cur === me) setSpeakBtn(btn, "playing");
        return;
      } catch (e) {
        if (cur !== me) return;
        if (e.name === "NotAllowedError") { blocked(); return; }
        if (me.url) { URL.revokeObjectURL(me.url); me.url = null; }
        me.audio = null; me.ctrl = null;
      }
    }
    browserSpeak(text, lang, me);
  }

  /* ---------- verdict, reasons, verify: backend fields, with a defensive fallback ---------- */
  const VERDICTS = ["likely_scam", "caution", "no_signals"];
  const deriveVerdict = (s) => (VERDICTS.includes(s.verdict) ? s.verdict : s.genuine === false ? "likely_scam" : "caution");
  function reasonKind(x) {
    const k = String(x || "").toLowerCase();
    return /risk|bad|red|flag|warn|danger/.test(k) ? "risk" : /ok|good|pass|safe|positive/.test(k) ? "ok" : "info";
  }
  // reasons and verify steps are kept as raw data; texts are resolved at render time so a language switch updates them
  function normReasons(s) {
    let out = [];
    if (Array.isArray(s.reasons) && s.reasons.length) {
      out = s.reasons.map((x) => typeof x === "string" ? { k: "info", text: x } : { k: reasonKind(x.kind || x.type || x.level || x.status), text: x.text || x.message || x.reason || x.label || "" }).filter((x) => x.text);
    } else {
      out = [...(s.red_flags || []).map((x) => ({ k: "risk", text: x })), ...(s.good_signs || []).map((x) => ({ k: "ok", text: x }))];
    }
    if (!out.some((x) => x.k === "info")) out.push({ k: "info", text: null });
    return out;
  }
  const normVerify = (s) => (Array.isArray(s.verify_yourself) ? s.verify_yourself.map((x) => typeof x === "string" ? x : (x && (x.text || x.message || x.step)) || "").filter(Boolean) : []);
  const applyScam = (r, s) => Object.assign(r, { verdict: deriveVerdict(s), reasons: normReasons(s), verify: normVerify(s) });
  const verifyOf = (r) => (r.verify.length ? r.verify : t("vd_" + r.verdict));

  /* ---------- build one result object from the API or from a bundled sample ---------- */
  const mapTrace = (tr0) => (tr0 || []).map((x) => ({ k: x.kind, t: x.tool, m: x.message, flag: x.flag }));
  function fromApi(d, lang) {
    const f = d.fields, r = d.route;
    return applyScam({
      sample: false, lang, explain: { [lang]: String(d.explanation || "").split(/\n+/).filter(Boolean) },
      fields: { issuer: f.issuer, type: f.letter_type, amount: f.amount, deadline: f.deadline, reference: f.reference },
      kenapa: { q: d.lesson.question, a: d.lesson.answer }, terms: d.lesson.terms || [],
      route: { url: r.source_url, label: String(r.source_url).replace(/^https?:\/\//, ""), date: r.retrieved_at, confidence: r.confidence,
        online: { steps: r.online_steps, prepare: r.prepare_online }, walkin: { steps: r.walkin_steps, prepare: r.prepare_walkin } },
      reminder: d.action.reminder, draft: d.action.draft, trace: mapTrace(d.trace)
    }, d.scam);
  }
  function fromSample(l) {
    const bad = l.scam.checks.filter((c) => c.startsWith("x|")).map((c) => c.slice(2)), good = l.scam.checks.filter((c) => !c.startsWith("x|"));
    const dom = l.route.source.split(" ")[0];
    return applyScam({
      sample: true, id: l.id, lang: "en", explain: l.explain,
      fields: { issuer: l.fields.Issuer, type: l.fields.Type, amount: l.fields.Amount, deadline: l.fields.Deadline, reference: l.fields.Reference },
      kenapa: { q: l.kenapa.q, a: l.kenapa.a }, terms: l.terms,
      route: { url: "https://" + dom, label: l.route.source, date: "example data, not live", confidence: l.route.confidence, online: l.route.online, walkin: l.route.walkin },
      reminder: l.reminder, draft: l.draft, trace: localTrace(l)
    }, { verdict: l.scam.genuine ? "no_signals" : "likely_scam", red_flags: bad, good_signs: good });
  }
  function localTrace(l) {
    const f = l.fields, bad = !l.scam.genuine, T0 = [];
    T0.push({ k: "think", m: "Goal: help the user understand this letter, check for scam signs, and decide the next step." });
    T0.push({ k: "tool", t: "privacy.redact", m: "personal details masked before anything else" });
    T0.push({ k: "tool", t: "classify.issuer", m: "issuer = " + f.Issuer + ", type = " + f.Type });
    T0.push({ k: "tool", t: "extract.fields", m: "amount = " + f.Amount + ", deadline = " + f.Deadline });
    T0.push({ k: "tool", t: "scam.check", m: "domain list, red-flag rules, reference pattern" });
    l.scam.checks.forEach((c) => T0.push({ k: c.startsWith("x|") ? "bad" : "ok", m: c.replace("x|", "") }));
    T0.push({ k: bad ? "bad" : "ok", m: bad ? "result: likely a scam, so the plan switches to protect and report" : "result: no scam signs found (this does not prove it is real)", flag: bad });
    T0.push({ k: "tool", t: "teach.lesson", m: "lesson and " + l.terms.length + " dictionary words" });
    T0.push({ k: "tool", t: "gov.retrieve", m: "steps from " + l.route.source + ", confidence " + l.route.confidence });
    T0.push({ k: "tool", t: "act.draft", m: bad ? "scam report draft prepared" : "reply draft and reminder prepared" });
    T0.push({ k: "warn", m: "Waiting for you. Nothing is sent or paid automatically." });
    return T0;
  }
  // samples carry all four languages and follow the explanation chip; API results carry the one language they were asked for
  const paraLang = (r) => (r.sample ? (r.explain[state.xl] ? state.xl : "en") : r.lang);
  const paras = (r) => r.explain[paraLang(r)] || Object.values(r.explain)[0] || [];

  /* ---------- API ---------- */
  async function post(body, ms) {
    try {
      const ctrl = new AbortController(); const to = setTimeout(() => ctrl.abort(), ms);
      const res = await fetch(CFG.API_BASE + "/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, signal: ctrl.signal, body: JSON.stringify(body) });
      clearTimeout(to);
      if (res.status === 422) return { error: t("e_422") };
      if (!res.ok) return { error: t("e_server", { n: res.status }), retry: true };
      return { data: await res.json() };
    } catch (e) { return { error: t("e_net"), retry: true }; }
  }
  const readB64 = (f) => new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1]); r.onerror = () => no(r.error); r.readAsDataURL(f); });

  /* staged progress: the API answers in one go, so the four stages (Read, Check, Explain, Route) are paced on the client */
  const STAGES = ["s_read", "s_verify", "s_explain", "s_route"];
  let stageTimer = 0;
  function drawStage(i, photo) {
    $("#stages").innerHTML = STAGES.map((k, j) => `<li class="${j < i ? "done" : j === i ? "now" : ""}">${esc(t(k))}</li>`).join("");
    $("#busyTxt").textContent = t("busy_step", { n: i + 1, s: t(STAGES[i]) }) + (photo && i === 0 ? " " + t("busy_photo") : "");
  }
  function setBusy(on, o = {}) {
    state.busy = on; clearInterval(stageTimer);
    $("#busy").hidden = !on;
    $("#stages").hidden = !!o.sample;
    if (on && o.sample) $("#busyTxt").textContent = t("busy_ex");
    if (on && !o.sample) { let i = 0; drawStage(0, o.photo); stageTimer = setInterval(() => { if (i < STAGES.length - 1) drawStage(++i, o.photo); }, 1500); }
    $("#checkBtn").disabled = on || !state.api; $$(".example").forEach((b) => (b.disabled = on));
  }
  function formErr(m, retry) {
    $("#formErr").textContent = m || ""; state.retry = retry || null; $("#retryBtn").hidden = !retry;
    if (m && $("#checker").hidden) toast(m);
  }

  async function checkOwn(inp) {
    state.last = inp; formErr(""); stopSpeak();
    setBusy(true, { photo: !!inp.file });
    const body = { language: state.xl };
    const pc = $("#postBox").value.trim(); if (/^\d{1,5}$/.test(pc)) body.postcode = pc;
    try { if (inp.text) body.text = inp.text; else body.image_b64 = await readB64(inp.file); } catch (e) { setBusy(false); formErr(t("e_read")); return; }
    const x = await post(body, 30000);
    setBusy(false);
    if (x.error) { formErr(x.error, x.retry ? () => checkOwn(inp) : null); return; }
    show(fromApi(x.data, body.language));
  }
  async function checkSample(id) {
    const l = D.letters.find((z) => z.id === id); if (!l) return;
    state.last = null; formErr(""); stopSpeak();
    setBusy(true, { sample: true });
    const r = fromSample(l);
    if (state.api) {
      const text = [l.title, "Rujukan: " + l.ref, "Daripada: " + l.issuer + " " + l.issuerShort, "Kepada: " + l.to, ...l.body.map((b) => b.replace(/<[^>]+>/g, ""))].join("\n");
      const x = await post({ text, language: state.xl, sample_id: l.id }, 8000);
      if (x.data) r.trace = mapTrace(x.data.trace); // reasons stay local so they follow the UI language
    }
    setBusy(false);
    show(r);
  }

  /* ---------- the check form ---------- */
  const MIN = 10, MAX = 20000;
  let hintKey = "";
  function updateCount(force) {
    const box = $("#pasteBox"), n = box.value.trim().length, file = $("#fileBox").files[0];
    $("#cnt").textContent = t("f_count", { n: box.value.length.toLocaleString("en-US"), m: MAX.toLocaleString("en-US") });
    const key = n === 0 ? (file ? "f_file_sel" : "f_min") : n < MIN ? "f_short" : box.value.length >= MAX ? "f_full" : "f_ok";
    if (force || key !== hintKey) {
      hintKey = key;
      const v = $("#vhint"); v.textContent = t(key, { m: MAX.toLocaleString("en-US") });
      v.className = "vh" + (key === "f_short" ? " warn" : key === "f_ok" || key === "f_file_sel" ? " good" : "");
    }
    box.setAttribute("aria-invalid", n > 0 && n < MIN);
  }
  // pick the letter's language by script (Chinese, Tamil) or by common words (BM, English)
  const BMW = new Set("yang dan anda untuk kepada telah dalam atau tidak sila bayar akaun dengan akan ini itu jumlah kena tuan puan sebelum pada dari kami".split(" "));
  const ENW = new Set("the and you your to of is for will this that please pay account before with from has have are our".split(" "));
  function detect(s) {
    const letters = (s.match(/[A-Za-z一-鿿஀-௿]/g) || []).length;
    if (letters < 8) return null;
    if ((s.match(/[一-鿿]/g) || []).length / letters > 0.2) return "zh";
    if ((s.match(/[஀-௿]/g) || []).length / letters > 0.2) return "ta";
    const w = s.toLowerCase().match(/[a-z]+/g) || [];
    const bm = w.filter((x) => BMW.has(x)).length, en = w.filter((x) => ENW.has(x)).length;
    return bm + en < 2 ? null : bm >= en ? "bm" : "en";
  }
  function autoDetect() {
    if (state.xlManual) return;
    const d = detect($("#pasteBox").value);
    if (!d) return;
    if (d !== state.xl) { state.xl = d; syncChips(); }
    $("#detectNote").textContent = d === state.lang ? "" : t("f_detect", { n: langName(d) });
  }
  function onInput() {
    if ($("#pasteBox").value) $("#fileBox").value = "";
    formErr(""); updateCount(); autoDetect();
  }
  $("#pasteBox").addEventListener("input", onInput);
  $("#pasteBox").addEventListener("paste", () => setTimeout(() => $("#checkBtn").scrollIntoView({ block: "nearest" }), 0));
  $("#fileBox").addEventListener("change", () => {
    const f = $("#fileBox").files[0]; formErr("");
    if (f) {
      if (!/^image\/(png|jpeg)$/.test(f.type)) { $("#fileBox").value = ""; formErr(t("e_type")); }
      else if (f.size > 4 * 1024 * 1024) { $("#fileBox").value = ""; formErr(t("e_big")); }
      else $("#pasteBox").value = "";
    }
    updateCount();
  });
  $("#clearInput").addEventListener("click", () => {
    $("#pasteBox").value = ""; $("#fileBox").value = ""; $("#postBox").value = ""; formErr("");
    state.xl = state.lang; state.xlManual = false; $("#detectNote").textContent = ""; syncChips(); updateCount();
  });
  $("#retryBtn").addEventListener("click", () => { const f = state.retry; if (f) { formErr(""); f(); } });
  $("#form").addEventListener("submit", (e) => {
    e.preventDefault(); if (state.busy) return;
    const text = $("#pasteBox").value.trim(), file = $("#fileBox").files[0];
    if (!state.api) { formErr(t("e_offline")); return; }
    if (!text && !file) { formErr(t("e_empty")); $("#pasteBox").focus(); return; }
    if (text && text.length < MIN) { formErr(t("e_short")); $("#pasteBox").focus(); return; }
    if (!consented()) { $("#consentBlock").hidden = false; formErr(t("consent_need")); $("#consentBox").focus(); return; }
    checkOwn(text ? { text } : { file });
  });
  $("#consentBox").checked = consented();
  $("#consentBlock").hidden = true;
  $("#consentBox").addEventListener("change", (e) => {
    if (e.target.checked) { store.set("consent", { v: CONSENT_V }); formErr(""); } else { try { localStorage.removeItem("faham_consent"); } catch (x) {} }
  });

  /* language chips: header = whole UI, form = explanation language */
  const chipBtns = (attr) => Object.entries(D.languages).map(([k, v]) => `<button type="button" class="chip" ${attr}="${esc(k)}" lang="${HTML_LANG[k]}" aria-pressed="false">${esc(v.label)}</button>`).join("");
  function renderChips() { $("#uiChips").innerHTML = chipBtns("data-u"); $("#langChips").innerHTML = chipBtns("data-x"); }
  function syncChips() {
    $$("[data-u]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.u === state.lang));
    $$("[data-x]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.x === state.xl));
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-u]"); if (!b || b.dataset.u === state.lang) return;
    state.lang = b.dataset.u; state.xl = state.lang; state.xlManual = false; $("#detectNote").textContent = "";
    save(); refreshLang();
    if (!$("#ob").hidden) $(`#ob [data-u="${state.lang}"]`).focus();
  });
  $("#langChips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-x]"); if (!b) return;
    state.xl = b.dataset.x; state.xlManual = true; $("#detectNote").textContent = ""; syncChips();
  });
  function refreshLang() {
    stopSpeak(); $("#fLang").value = state.lang; applyI18n(); syncChips(); renderMode(); renderExamples(); setTheme(); setVoice();
    if (!$("#ob").hidden) renderOb(); updateCount(true); renderLevel();
    if (state.result && !$("#result").hidden) renderResult(state.result, true);
    if (!state.practice.answered) renderPractice();
    route(true);
  }
  function renderExamples() {
    $("#examples").innerHTML = D.letters.map((l) => `<button type="button" class="example" data-id="${esc(l.id)}"><b>${esc(l.short)}</b><span>${esc(tr(l.kind))}</span></button>`).join("");
  }
  $("#examples").addEventListener("click", (e) => { const b = e.target.closest("[data-id]"); if (b && !state.busy) checkSample(b.dataset.id); });

  /* ---------- result screen: one idea per step, or everything on one page ---------- */
  const cut = (s, n = 400) => { s = String(s).trim(); const a = s.slice(0, n), i = Math.max(a.lastIndexOf(". "), a.lastIndexOf("。")); return s.length <= n ? s : i > 80 ? a.slice(0, i + 1) : a; };
  const rl = (r) => (r.sample ? state.lang : r.lang);                       // language of the text that came with the result
  const sentences = (ps) => ps.join(" ").split(/(?<=[.!?。！？])\s*/).filter(Boolean);
  const more = (html, k) => `<details class="more"><summary>${esc(t(k || "show_all"))}</summary>${html}</details>`;
  let pages = [];                                                           // built by renderResult: { id, h, html, say() -> [text, lang] }
  const curPage = (manual) => (state.all ? (manual && pages.find((p) => p.id === "says")) || pages[0] : pages[Math.min(state.step, pages.length - 1)]);
  function speakStep(manual) {
    const p = curPage(manual), x = p && p.say(); if (!x || !x[0]) return;
    readAloud(cut(x[0]), x[1], $("[data-act=speak]", $("#result")), $("#vnote"));
  }
  function autoSay() {                                                      // called from a tap on Check, Next or Back, never on page load
    stopSpeak(); $("#tapListen").hidden = true;
    if (state.voice) speakStep(false);
  }
  function show(r) {
    state.result = r; state.route = "online"; state.step = 0;
    renderResult(r);
    $("#checker").hidden = true; $("#result").hidden = false;
    store.set("checked", true); $("#hint").hidden = true;
    $("#result").scrollIntoView();
    const h = $("#vHead"); if (h) h.focus({ preventScroll: true });
    autoSay();
  }
  function backToChecker() {
    stopSpeak(); state.step = 0;
    $("#result").hidden = true; $("#checker").hidden = false;
    window.scrollTo(0, 0); $("#checker h1").focus();
  }
  function routeHtml(r) {
    const o = r.route[state.route === "online" ? "online" : "walkin"], st = (o.steps || []).map(clean);
    const src = /^https:\/\//.test(r.route.url || "") ? `<a href="${esc(r.route.url)}" target="_blank" rel="noopener noreferrer">${esc(r.route.label)}</a>` : esc(r.route.label);
    const ol = (a, n) => `<ol class="steps" start="${n}" lang="en">${a.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>`;
    return `${ol(st.slice(0, 4), 1)}${st.length > 4 ? more(ol(st.slice(4), 5), "show_more") : ""}
      ${(o.prepare || []).length ? `<p class="muted">${esc(t("ready"))}</p><div class="facts">${o.prepare.map((p) => `<span class="fact">${esc(p)}</span>`).join("")}</div>` : ""}
      <p class="src">${t("src", { s: src, d: esc(tr(r.route.date)), c: esc(tr(r.route.confidence)) })}</p>`;
  }
  function reminderText(r) {
    if (!r.reminder) return t("rem_none");
    const m = String(r.reminder).match(/^(.+) · 7 days before deadline$/);
    return m ? t("rem", { d: m[1] }) : tr(r.reminder);
  }
  const STATUS = { think: "st_think", tool: "st_tool", ok: "st_ok", bad: "st_bad", warn: "st_warn" };
  function summaryText(r) {
    const f = r.fields, v = r.verdict;
    const line = (k, x) => (x ? `${t(k)}: ${tr(x)}` : "");
    return ["FAHAM", t("v_" + v), t("vs_" + v), "", line("f_from", f.issuer), line("f_amount", f.amount), line("f_deadline", f.deadline), line("f_ref", f.reference), "",
      t("h_verify") + ":", ...verifyOf(r).map((x, i) => `${i + 1}. ${clean(x)}`), "", ...paras(r).map(clean), "", t("disc")].filter((x, i, a) => x !== "" || a[i - 1] !== "").join("\n");
  }

  /* bodies shared by the step view and the one-page view */
  const reasonText = (x) => (x.text === null ? t("info_default") : tr(clean(x.text)));
  const reasonLi = (x) => `<li class="r-${x.k}">${svg(x.k)}<div><span class="rk">${esc(t("rk_" + x.k))}</span>${esc(reasonText(x))}</div></li>`;
  const whyHtml = (r, n = 99) => {
    const ul = (a) => `<ul class="reasons" lang="${HTML_LANG[rl(r)]}">${a.map(reasonLi).join("")}</ul>`;
    return ul(r.reasons.slice(0, n)) + (r.reasons.length > n ? more(ul(r.reasons.slice(n))) : "");
  };
  const stepsOl = (r, a, n) => `<ol class="steps" start="${n}" lang="${HTML_LANG[rl(r)]}">${a.map((x) => `<li>${esc(clean(x))}</li>`).join("")}</ol>`;
  const verifyHtml = (r) => stepsOl(r, verifyOf(r), 1);
  function nowHtml(r) {
    const s = verifyOf(r), lg = `lang="${HTML_LANG[rl(r)]}"`;
    return `<p class="next-step" ${lg}>${esc(clean(s[0]))}</p>${s[1] ? `<p class="muted">${esc(t("more_chk"))}</p><p ${lg}>${esc(clean(s[1]))}</p>` : ""}${s.length > 2 ? more(stepsOl(r, s.slice(2), 3)) : ""}`;
  }
  function saysHtml(r, short) {
    const f = r.fields, ps = paras(r).map(clean), sn = sentences(ps), lg = `lang="${HTML_LANG[paraLang(r)]}"`;
    const chip = (k, val) => `<span class="fact"><span>${esc(t(k))}</span><b>${esc(val ? tr(val) : t("not_found"))}</b></span>`;
    const facts = (a) => `<div class="facts">${a.map(([k, v]) => chip(k, v)).join("")}</div>`;
    const A = [["f_amount", f.amount], ["f_deadline", f.deadline]], B = [["f_from", f.issuer], ["f_ref", f.reference]];
    const reexplain = !r.sample && r.lang !== state.xl && state.last;
    const re = reexplain ? `<p class="muted">${esc(t("x_note", { a: langName(r.lang) }))}</p><button class="btn btn-secondary" type="button" data-act="reexplain"><span>${esc(t("x_btn", { b: langName(state.xl) }))}</span></button>` : "";
    return (short ? `${facts(A)}<p ${lg}>${esc(sn.slice(0, 3).join(" "))}</p>${more((sn.length > 3 ? `<p ${lg}>${esc(sn.slice(3).join(" "))}</p>` : "") + facts(B))}`
      : `<div ${lg}>${ps.map((p) => `<p>${esc(p)}</p>`).join("")}</div>${facts([...B.slice(0, 1), ...A, ...B.slice(1)])}`) + re;
  }
  const todoHtml = (r) => `<div class="seg" role="group" aria-label="${esc(t("h_todo"))}">
      <button type="button" class="chip" data-route="online" aria-pressed="${state.route === "online"}">${esc(t("online"))}</button>
      <button type="button" class="chip" data-route="walkin" aria-pressed="${state.route !== "online"}">${esc(t("office"))}</button>
    </div><div id="routePanel">${routeHtml(r)}</div>`;
  const draftHtml = (r) => `<p><b>${esc(t("rem_label"))}</b> ${esc(reminderText(r))}</p>
    <p class="muted">${esc(t("draft_hint"))}</p>
    <pre class="draft" lang="ms">${esc(r.draft)}</pre>
    <button class="btn btn-primary" type="button" data-act="copy"><span>${esc(t("copy"))}</span></button>
    <p class="note"><b>${esc(t("draft_note_b"))}</b> ${esc(t("draft_note"))}</p>`;
  function learnHtml(r) {
    const learnable = r.terms.filter((x) => D.glossary[x]), allIn = learnable.length && learnable.every((x) => state.learned.has(x));
    return `<h3 class="h3">${esc(tr(r.kenapa.q))}</h3><p>${esc(clean(r.kenapa.a))}</p>
      ${learnable.length ? `<p class="muted">${esc(t("words_in"))} ${learnable.map(esc).join(", ")}</p>
      <button class="btn btn-secondary" type="button" data-act="add" ${allIn ? "disabled" : ""}><span>${esc(allIn ? t("added") : t("add"))}</span></button>` : ""}`;
  }

  /* the steps; a step with nothing to show is left out. say() gives the short text to read aloud and its language */
  function buildPages(r) {
    const v = r.verdict, f = r.fields, vs = verifyOf(r).map(clean), ps = paras(r).map(clean);
    const route = () => ((r.route[state.route === "online" ? "online" : "walkin"].steps) || []).map(clean);
    const out = [
      { id: "verdict", say: () => [`${t("v_" + v)} ${t("vs_" + v)}`, state.lang] },
      { id: "now", h: "next_h", html: nowHtml(r), say: () => [vs.slice(0, 2).join(" "), rl(r)] },
      { id: "why", h: "h_why", html: whyHtml(r, 3), say: () => [r.reasons.slice(0, 3).map(reasonText).join(" "), rl(r)] }
    ];
    if (ps.length || f.amount || f.deadline) out.push({ id: "says", h: "h_says", html: saysHtml(r, true), say: () => [sentences(ps).slice(0, 3).join(" "), paraLang(r)] });
    if (["online", "walkin"].some((k) => (r.route[k].steps || []).length)) out.push({ id: "todo", h: "h_todo", html: todoHtml(r), say: () => [route().slice(0, 4).join(" "), "en"] });
    out.push({ id: "draft", h: "h_draft", html: draftHtml(r), say: () => [`${t("rem_label")} ${reminderText(r)}`, state.lang] });
    out.push({ id: "learn", h: "h_learn", html: learnHtml(r), say: () => [clean(r.kenapa.a), "en"] });
    return out;
  }
  function renderResult(r, keep) {
    const open = {};
    if (keep) $$("#result details[data-g]").forEach((d) => { open[d.dataset.g] = d.open; });
    const wide = matchMedia("(min-width: 700px)").matches;
    const grp = (id, title, body, dflt) => `<details class="grp" data-g="${id}"${(id in open ? open[id] : dflt || wide) ? " open" : ""}><summary><h2>${esc(title)}</h2></summary><div class="gbody">${body}</div></details>`;
    const v = r.verdict;
    const verdict = `<div class="verdict v-${v}${keep ? "" : " fresh"}">${svg(v)}<div><h1 id="vHead" tabindex="-1">${esc(t("v_" + v))}</h1><p>${esc(t("vs_" + v))}</p></div></div>`;
    const tail = `<details class="trace"><summary>${esc(t("tr_sum"))}</summary>
        <p class="muted">${esc(t("tr_note"))}</p>
        <ol class="trace-list" lang="en">${(r.trace || []).map((x) => `<li class="${x.flag ? "flag" : ""}"><span class="tag">${esc(STATUS[x.k] ? t(STATUS[x.k]) : t("st_step"))}${x.t ? " " + esc(x.t) : ""}</span>${esc(clean(x.m))}</li>`).join("") || `<li>${esc(t("tr_none"))}</li>`}</ol>
      </details>`;
    pages = buildPages(r);
    const head = `
      <div class="rbar">
        <button class="btn btn-secondary" type="button" data-act="again">&larr; <span>${esc(t("r_again"))}</span></button>
        <button class="btn btn-secondary speak" type="button" data-act="speak">${svg("speaker")}<span>${esc(t("listen"))}</span></button>
      </div>
      <p class="muted vnote" id="vnote" role="status"></p>
      <button class="btn btn-primary btn-big tap" type="button" id="tapListen" data-act="speak" hidden>${svg("speaker")}<span>${esc(t("tap"))}</span></button>
      ${r.sample ? `<p class="note">${esc(t("sample_note"))}${state.lang !== "en" ? " " + esc(t("sample_lang")) : ""}</p>` : ""}`;
    const allBtn = `<button class="btn btn-quiet alink" type="button" data-act="all">${esc(t(state.all ? "all_off" : "all_on"))}</button>`;
    let body;
    if (state.all) {
      body = `${allBtn}${verdict}
      <section class="card next" aria-labelledby="nextH">
        <h2 class="h3" id="nextH">${esc(t("next_h"))}</h2>
        <p class="next-step">${esc(clean(verifyOf(r)[0]))}</p>
        <button class="btn btn-secondary" type="button" data-act="sum"><span>${esc(t("r_copy_sum"))}</span></button>
      </section>
      ${grp("why", t("h_why"), whyHtml(r), true)}
      ${grp("verify", t("h_verify"), verifyHtml(r), true)}
      ${grp("says", t("h_says"), saysHtml(r, false))}
      ${grp("todo", t("h_todo"), todoHtml(r))}
      ${grp("draft", t("h_draft"), draftHtml(r))}
      ${grp("learn", t("h_learn"), learnHtml(r))}
      ${tail}`;
    } else {
      const i = (state.step = Math.min(state.step, pages.length - 1)), p = pages[i], last = i === pages.length - 1;
      body = `<div class="stepbar"><p>${esc(t("st_of", { n: i + 1, m: pages.length }))}</p><ol class="dots" aria-hidden="true">${pages.map((_, j) => `<li${j <= i ? ' class="on"' : ""}></li>`).join("")}</ol></div>
      ${p.id === "verdict" ? verdict : `<section class="card step"><h2 id="stepH" tabindex="-1">${esc(t(p.h))}</h2>${p.html}</section>`}
      <div class="snav">
        <button class="btn btn-secondary" type="button" data-act="prev"${i === 0 ? " disabled" : ""}>&larr; ${esc(t("bk"))}</button>
        ${last ? `<button class="btn btn-primary" type="button" data-act="again">${esc(t("st_done"))}</button>` : `<button class="btn btn-primary" type="button" data-act="next">${esc(t(p.id === "now" ? "st_got" : "nx"))}</button>`}
      </div>
      ${allBtn}
      ${last ? `<button class="btn btn-quiet" type="button" data-act="sum"><span>${esc(t("r_copy_sum"))}</span></button>${tail}` : ""}`;
    }
    $("#result").innerHTML = `${head}${body}<p class="muted">${esc(t("disc"))}</p>`;
  }
  $("#result").addEventListener("click", (e) => {
    const r = state.result; if (!r) return;
    const rt = e.target.closest("[data-route]");
    if (rt) {
      state.route = rt.dataset.route;
      $$("[data-route]").forEach((b) => b.setAttribute("aria-pressed", b === rt));
      $("#routePanel").innerHTML = routeHtml(r); return;
    }
    const a = e.target.closest("[data-act]"); if (!a) return;
    const act = a.dataset.act;
    if (act === "again") backToChecker();
    else if (act === "copy") copyText(r.draft, t("draft_copied"));
    else if (act === "sum") copyText(summaryText(r), t("sum_copied"));
    else if (act === "speak") { $("#tapListen").hidden = true; speakStep(true); }
    else if (act === "next" || act === "prev") {
      state.step += act === "next" ? 1 : -1; renderResult(r, true); $("#result").scrollIntoView();
      const h = $("#vHead, #stepH"); if (h) h.focus({ preventScroll: true });
      autoSay();
    }
    else if (act === "all") { state.all = !state.all; store.set("all", state.all); stopSpeak(); renderResult(r, true); $("#result").scrollIntoView(); }
    else if (act === "reexplain") { backToChecker(); checkOwn(state.last); }
    else if (act === "add") {
      const fresh = r.terms.filter((x) => D.glossary[x] && !state.learned.has(x));
      fresh.forEach((x) => state.learned.add(x));
      addXP(fresh.length * 5); save();
      a.disabled = true; a.querySelector("span").textContent = t("added");
      toast(t(fresh.length === 1 ? "w1" : "wn", { n: fresh.length }));
    }
  });

  /* ---------- voice switch ---------- */
  function setVoice() { $("#voiceBtn").setAttribute("aria-pressed", state.voice); $("#voiceLbl").textContent = t(state.voice ? "vc_on" : "vc_off"); }
  $("#voiceBtn").addEventListener("click", () => { state.voice = !state.voice; store.set("voice", state.voice); if (!state.voice) stopSpeak(); setVoice(); });

  /* ---------- welcome dialog (first visit) ----------
     faham_onboarded=<OB_V> is a first-party cookie that holds only this flag; localStorage mirrors it for browsers that block cookies.
     It is written only when the user taps Start on the last card. Bump OB_V to show the welcome again after the terms change. */
  const OB_V = "1";
  const OB = [["ob1", "doc"], ["ob2", "device"], ["ob3", "eye"], ["ob4", "phone"], ["ob5", "scale"]];
  const ckEnd = "; Path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : "");
  const onboarded = () => document.cookie.split("; ").includes("faham_onboarded=" + OB_V) || store.get("onboarded", "") === OB_V;
  const markOb = () => { document.cookie = "faham_onboarded=" + OB_V + "; Max-Age=31536000" + ckEnd; store.set("onboarded", OB_V); };
  const forgetOb = () => { document.cookie = "faham_onboarded=; Max-Age=0" + ckEnd; try { localStorage.removeItem("faham_onboarded"); } catch (e) {} };
  let obI = 0, obTick = false;
  function renderOb() {
    const [k, ico] = OB[obI], last = obI === OB.length - 1;
    const lis = (a) => `<ul class="ob-list">${a.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
    const extra = ["", `<p class="muted">${esc(t("ob2_n", { b: t("a_clear") }))}</p>`, "",
      `<a class="btn btn-primary btn-big call" href="tel:997">${esc(t("ob4_call"))}</a><p class="muted">${esc(t("ob4_n"))}</p>`,
      `${more(lis(t("ob_tc")), "ob_tc_sum")}${more(lis(t("ob_cc")), "ob_cc_sum")}
       <label class="tick"><input type="checkbox" id="obTick"${obTick ? " checked" : ""} /><span>${esc(t("ob_agree"))}</span></label><p class="muted">${esc(t("ob_draft"))}</p>`][obI];
    $("#ob").innerHTML = `<div class="wrap">
      <div class="chips" role="group" aria-label="${esc(t("ui_lang"))}">${chipBtns("data-u")}</div>
      <div class="stepbar"><p>${esc(t("st_of", { n: obI + 1, m: OB.length }))}</p><ol class="dots" aria-hidden="true">${OB.map((_, j) => `<li${j <= obI ? ' class="on"' : ""}></li>`).join("")}</ol></div>
      <section class="card">
        <div class="ob-ico">${svg(ico)}</div>
        <h2 id="obH" tabindex="-1">${esc(t(k + "_h"))}</h2>
        ${lis(t(k + "_b"))}${extra}
        <button class="btn btn-secondary speak" type="button" data-ob="hear" data-idle="ob_hear">${svg("speaker")}<span>${esc(t("ob_hear"))}</span></button>
        <p class="muted vnote" id="obNote" role="status"></p>
      </section>
      <div class="snav">
        <button class="btn btn-secondary" type="button" data-ob="back"${obI === 0 ? " disabled" : ""}>&larr; ${esc(t("bk"))}</button>
        ${last ? `<button class="btn btn-primary" type="button" data-ob="start" id="obStart"${obTick ? "" : " disabled"}>${esc(t("ob_start"))}</button>` : `<button class="btn btn-primary" type="button" data-ob="next">${esc(t("nx"))} &rarr;</button>`}
      </div></div>`;
    syncChips();
  }
  const setInert = (on) => [...document.body.children].forEach((el) => { if (el.id !== "ob" && el.id !== "toast" && el.tagName !== "SCRIPT") el.inert = on; });
  function obGo(d) {
    const n = obI + d; if (n < 0 || n >= OB.length) return;
    stopSpeak(); obI = n; renderOb(); $("#ob").scrollTop = 0; $("#obH").focus();
  }
  function showOb() { obI = 0; obTick = false; renderOb(); $("#ob").hidden = false; setInert(true); $("#obH").focus(); }
  function endOb() {
    markOb(); stopSpeak(); $("#ob").hidden = true; $("#ob").innerHTML = ""; setInert(false);
    const h = $(".view:not([hidden]) h1"); if (h) h.focus();
  }
  $("#ob").addEventListener("click", (e) => {
    const b = e.target.closest("[data-ob]"); if (!b) return;
    const a = b.dataset.ob, k = OB[obI][0];
    if (a === "next") obGo(1); else if (a === "back") obGo(-1);
    else if (a === "start" && obTick) endOb();
    else if (a === "hear") readAloud([t(k + "_h") + ".", ...t(k + "_b")].join(" "), state.lang, b, $("#obNote"));   // static text only, and only when asked
  });
  $("#ob").addEventListener("change", (e) => { if (e.target.id === "obTick") { obTick = e.target.checked; $("#obStart").disabled = !obTick; } });
  $("#ob").addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); return; }                                    // no way to skip
    if (e.key === "Tab") {                                                                       // focus trap
      const f = $$("a[href], button:not(:disabled), input, summary", $("#ob")).filter((x) => x.offsetParent), end = f[f.length - 1];
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); end.focus(); } else if (!e.shiftKey && document.activeElement === end) { e.preventDefault(); f[0].focus(); }
      return;
    }
    if (e.target.matches("input, summary")) return;
    if (e.key === "ArrowRight") obGo(1); else if (e.key === "ArrowLeft") obGo(-1);
    else if (e.key === "Enter" && !e.target.closest("button, a")) obGo(1);
  });
  $("#obAgain").addEventListener("click", () => { forgetOb(); showOb(); });

  /* ---------- levels and dictionary ---------- */
  const levelFor = (xp) => D.levels.reduce((l, x) => (xp >= x.min ? x : l), D.levels[0]);
  function addXP(n) {
    if (!n) return;
    const before = levelFor(state.xp).name; state.xp += n; save(); renderLevel();
    const after = levelFor(state.xp).name; if (after !== before) toast(t("d_newlevel", { n: tr(after) }));
  }
  function renderLevel() {
    const cur0 = levelFor(state.xp), next = D.levels[D.levels.indexOf(cur0) + 1];
    $("#lvlName").textContent = tr(cur0.name);
    $("#lvlBar").style.width = (next ? ((state.xp - cur0.min) / (next.min - cur0.min)) * 100 : 100) + "%";
    $("#lvlNext").textContent = next ? t("d_pts", { x: state.xp, m: next.min - state.xp, n: tr(next.name) }) : t("d_top", { x: state.xp });
  }
  function renderGlossary() {
    const q = ($("#glossSearch").value || "").trim().toLowerCase();
    const list = Object.entries(D.glossary).filter(([k, v]) => !q || k.toLowerCase().includes(q) || tr(v.def).toLowerCase().includes(q))
      .sort((a, b) => state.learned.has(b[0]) - state.learned.has(a[0]));
    $("#glossGrid").innerHTML = list.map(([k, v]) => state.learned.has(k)
      ? `<div class="term"><small>${esc(tr(v.src))}</small><b>${esc(k)}</b><p>${esc(tr(v.def))}</p></div>`
      : `<div class="term locked"><b>${esc(k)}</b><p>${esc(t("d_locked"))}</p></div>`).join("")
      || `<p class="muted">${esc(t("d_nomatch", { q }))}</p>`;
    $("#glossCount").textContent = state.learned.size ? t("d_count", { a: state.learned.size, b: Object.keys(D.glossary).length }) : t("d_none");
  }
  $("#glossSearch").addEventListener("input", renderGlossary);

  /* ---------- practice ---------- */
  const skel = '<div class="skel" aria-hidden="true"></div><div class="skel s2" aria-hidden="true"></div>';
  async function newRound() {
    const my = (newRound.n = (newRound.n || 0) + 1);
    let items = D.practice, note = "";
    $("#pFeedback").innerHTML = "";
    if (state.api) {
      $("#pCard").innerHTML = skel; $("#pChoices").hidden = true; $("#pCount").textContent = t("p_loading");
      try {
        const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 6000);
        const res = await fetch(CFG.API_BASE + "/api/practice?n=6&lang=" + state.lang, { signal: ctrl.signal });
        if (!res.ok) throw new Error(res.status);
        const got = await res.json(); if (!got.length) throw new Error("empty");
        items = got.map((x) => ({ from: x.sender, kind: x.channel, text: x.text, scam: x.is_scam, clues: x.clues, agent: x.agent }));
      } catch (e) { note = t("p_loadfail"); }
      if (my !== newRound.n) return;
    }
    const order = items.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
    state.practice = { items, order, i: 0, score: 0, answered: false, results: [] };
    renderPractice(); if (note) toast(note);
  }
  function renderPractice() {
    const p = state.practice;
    $("#pFeedback").innerHTML = "";
    if (!p.order.length) { $("#pCard").textContent = t("p_none"); $("#pChoices").hidden = true; return; }
    if (p.i >= p.order.length) {
      const msg = p.score >= 5 ? t("p_end_hi") : p.score >= 3 ? t("p_end_mid") : t("p_end_lo");
      $("#pCard").innerHTML = `<b>${esc(t("p_fin", { s: p.score, n: p.order.length }))}</b><br />${esc(msg)}`;
      $("#pChoices").hidden = true; $("#pCount").textContent = t("p_done");
    } else {
      const it = p.items[p.order[p.i]];
      $("#pCard").innerHTML = `<div class="from" lang="${HTML_LANG[state.lang]}">${esc(t("p_from"))}: <b>${esc(tr(it.from))}</b> (${esc(tr(it.kind))}, ${esc(t("p_fict"))})</div>${esc(it.text)}`;
      $("#pChoices").hidden = false; p.answered = false;
      $("#pCount").textContent = t("p_count", { i: p.i + 1, n: p.order.length });
    }
    $("#pScore").textContent = `${p.score} / ${p.results.length}`;
  }
  function agentLine(a) {
    if (!a) return "";
    const flags = (a.red_flags || []).map((x) => `<li>${esc(tr(clean(x)))}</li>`).join("");
    return `<p><b>${esc(t("p_agent"))}</b> ${esc(t("v_" + deriveVerdict(a)))}</p>${flags ? `<ul>${flags}</ul>` : ""}`;
  }
  $("#pChoices").addEventListener("click", (e) => {
    const b = e.target.closest("[data-a]"), p = state.practice; if (!b || p.answered) return;
    p.answered = true;
    const it = p.items[p.order[p.i]], right = (b.dataset.a === "scam") === it.scam;
    p.results.push(right); if (right) { p.score++; addXP(10); }
    $("#pFeedback").innerHTML = `<div class="fb ${right ? "right" : "wrong"}"><h3>${esc(t(right ? "p_right" : "p_wrong"))} ${esc(t(it.scam ? "p_is_scam" : "p_is_ok"))}</h3>
      <p>${esc(t("p_clues"))}</p><ul>${it.clues.map((c) => `<li>${esc(tr(c))}</li>`).join("")}</ul>${agentLine(it.agent)}
      <button class="btn btn-primary" type="button" id="pNext">${esc(t(p.i + 1 < p.order.length ? "p_next" : "p_see"))}</button></div>`;
    $("#pChoices").hidden = true; $("#pScore").textContent = `${p.score} / ${p.results.length}`;
    $("#pNext").addEventListener("click", () => { p.i++; renderPractice(); });
    $("#pNext").focus();
  });
  $("#pRestart").addEventListener("click", newRound);

  /* ---------- family ---------- */
  function fillFamily() {
    $("#fLang").innerHTML = Object.entries(D.languages).map(([k, v]) => `<option value="${esc(k)}">${esc(v.name)}</option>`).join("");
    $("#fLang").value = state.lang;
  }
  $("#fLetter").addEventListener("change", () => renderFamily()); $("#fLang").addEventListener("change", () => renderFamily());
  let famText = "", famLang = "bm";
  function renderFamily() {
    const sel = $("#fLetter"), keep = sel.value;
    sel.innerHTML = D.letters.map((l) => `<option value="${esc(l.id)}">${esc(l.short)}: ${esc(tr(l.kind))}</option>`).join("") + (state.result && !state.result.sample ? `<option value="mine">${esc(t("fa_mine"))}</option>` : "");
    sel.value = [...sel.options].some((o) => o.value === keep) ? keep : D.letters[0].id;
    const lang = $("#fLang").value, saved = sel.value === "mine";
    const r = saved ? state.result : fromSample(D.letters.find((l) => l.id === sel.value));
    const ps = r.explain[lang] || r.explain[r.lang];
    famLang = r.explain[lang] ? lang : r.lang;
    $("#fNote").textContent = r.explain[lang] ? "" : t("fa_note_lang", { a: langName(r.lang), b: langName(lang) });
    famText = (saved ? "" : (D.letters.find((l) => l.id === sel.value).short + "\n\n")) + ps.map(clean).join("\n\n") + "\n\n" + ((T[famLang] || T.en).fam_foot);
    $("#fMsg").lang = HTML_LANG[famLang]; $("#fMsg").textContent = famText;
  }
  $("#fCopy").addEventListener("click", () => copyText(famText, t("fa_copied")));
  $("#fSpeak").addEventListener("click", (e) => readAloud(famText, famLang, e.currentTarget, $("#fVnote")));

  /* ---------- pages, theme, data ---------- */
  const VIEWS = ["check", "practice", "dictionary", "family", "about"];
  function route(first) {
    const v = VIEWS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "check";
    VIEWS.forEach((n) => ($("#view-" + n).hidden = n !== v));
    $$(".top nav a").forEach((a) => (a.getAttribute("href") === "#" + v ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    document.title = "FAHAM: " + t("ti_" + v);
    if (!first) stopSpeak();
    if (v === "dictionary") { renderGlossary(); renderLevel(); }
    if (v === "family") renderFamily();
    if (!first) { window.scrollTo(0, 0); const h = $("h1", $("#view-" + v)); if (h) h.focus(); }
  }
  window.addEventListener("hashchange", () => route(false));
  function setTheme() {
    document.documentElement.dataset.theme = state.theme;
    $("#themeBtn").setAttribute("aria-pressed", state.theme === "dark");
    $("#themeLbl").textContent = t(state.theme === "dark" ? "th_light" : "th_dark");
    $('meta[name="theme-color"]').setAttribute("content", state.theme === "dark" ? "#0e1719" : "#0b5c63");
  }
  $("#themeBtn").addEventListener("click", () => { state.theme = state.theme === "dark" ? "light" : "dark"; save(); setTheme(); });
  $("#clearData").addEventListener("click", () => {
    if (state.busy) { toast(t("wait_check")); return; }
    try { Object.keys(localStorage).filter((k) => k.startsWith("faham_")).forEach((k) => localStorage.removeItem(k)); } catch (e) {}
    forgetOb();
    Object.assign(state, { lang: "bm", xl: "bm", xlManual: false, theme: "light", learned: new Set(), xp: 0, voice: true, all: false, step: 0, result: null, last: null });
    $("#consentBox").checked = false; $("#consentBlock").hidden = true; $("#pasteBox").value = ""; $("#fileBox").value = ""; $("#postBox").value = ""; formErr("");
    $("#detectNote").textContent = ""; $("#hint").hidden = false;
    $("#result").hidden = true; $("#result").innerHTML = ""; $("#checker").hidden = false;
    fillFamily(); refreshLang(); newRound();
    $("#clearMsg").textContent = t("a_cleared");
  });

  /* ---------- API status ---------- */
  function renderMode() {
    $("#mode").textContent = t("mode_" + state.mode); $("#mode").dataset.s = state.mode;
  }
  function setMode(online) {
    state.api = online; state.mode = online ? "on" : "off"; renderMode();
    $("#offlineNote").hidden = online;
    if (!online) $("#exBox").open = true;
    ["pasteBox", "fileBox", "postBox", "clearInput"].forEach((id) => ($("#" + id).disabled = !online));
    $("#checkBtn").disabled = !online || state.busy;
  }
  async function checkApi() {
    if (!CFG.API_BASE) { setMode(false); return; }
    try {
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 2500);
      const r = await fetch(CFG.API_BASE + "/api/health", { signal: ctrl.signal });
      setMode(r.ok);
      if (r.ok) {
        const h = await r.json().catch(() => ({}));
        state.tts = { available: h.tts_available === true, langs: Array.isArray(h.tts_languages) ? h.tts_languages : [] };
      }
    } catch (e) { setMode(false); }
    if (state.api) newRound();
  }

  /* ---------- init ---------- */
  renderChips(); setTheme(); setVoice(); applyI18n(); syncChips(); renderMode(); renderExamples(); updateCount(true); renderLevel(); fillFamily();
  $("#hint").hidden = !!store.get("checked", false);
  state.practice.order = D.practice.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
  renderPractice(); route(true); checkApi();
  if (!onboarded()) showOb();
})();
