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
    speaker: '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/>'
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
    btn.querySelector("span").textContent = t(mode === "loading" ? "loading" : mode === "playing" ? "stop" : "listen");
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
  function browserSpeak(text, lang, me) {
    if (!("speechSynthesis" in window)) { toast(t("no_speech")); stopSpeak(); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = D.languages[lang].speech; u.rate = 0.9;
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.toLowerCase().startsWith(u.lang.slice(0, 2).toLowerCase()));
    if (v) u.voice = v; else toast(t("no_voice", { n: langName(lang) }));
    u.onend = u.onerror = () => { if (cur === me) stopSpeak(); };
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
          if (ttsCache.size >= 4) ttsCache.delete(ttsCache.keys().next().value);
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
  function renderChips() {
    const mk = (attr) => Object.entries(D.languages).map(([k, v]) => `<button type="button" class="chip" ${attr}="${esc(k)}" lang="${HTML_LANG[k]}" aria-pressed="false">${esc(v.label)}</button>`).join("");
    $("#uiChips").innerHTML = mk("data-u"); $("#langChips").innerHTML = mk("data-x");
  }
  function syncChips() {
    $$("[data-u]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.u === state.lang));
    $$("[data-x]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.x === state.xl));
  }
  $("#uiChips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-u]"); if (!b || b.dataset.u === state.lang) return;
    state.lang = b.dataset.u; state.xl = state.lang; state.xlManual = false; $("#detectNote").textContent = "";
    save(); refreshLang();
  });
  $("#langChips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-x]"); if (!b) return;
    state.xl = b.dataset.x; state.xlManual = true; $("#detectNote").textContent = ""; syncChips();
  });
  function refreshLang() {
    stopSpeak(); $("#fLang").value = state.lang; applyI18n(); syncChips(); renderMode(); renderExamples(); setTheme(); updateCount(true); renderLevel();
    if (state.result && !$("#result").hidden) renderResult(state.result, true);
    if (!state.practice.answered) renderPractice();
    route(true);
  }
  function renderExamples() {
    $("#examples").innerHTML = D.letters.map((l) => `<button type="button" class="example" data-id="${esc(l.id)}"><b>${esc(l.short)}</b><span>${esc(tr(l.kind))}</span></button>`).join("");
  }
  $("#examples").addEventListener("click", (e) => { const b = e.target.closest("[data-id]"); if (b && !state.busy) checkSample(b.dataset.id); });

  /* ---------- result screen ---------- */
  function show(r) {
    state.result = r; state.route = "online";
    renderResult(r);
    $("#checker").hidden = true; $("#result").hidden = false;
    store.set("checked", true); $("#hint").hidden = true;
    window.scrollTo(0, 0);
    const h = $("#vHead"); if (h) h.focus({ preventScroll: true });
  }
  function backToChecker() {
    stopSpeak();
    $("#result").hidden = true; $("#checker").hidden = false;
    window.scrollTo(0, 0); $("#checker h1").focus();
  }
  function routeHtml(r) {
    const o = r.route[state.route === "online" ? "online" : "walkin"];
    const src = /^https:\/\//.test(r.route.url || "") ? `<a href="${esc(r.route.url)}" target="_blank" rel="noopener noreferrer">${esc(r.route.label)}</a>` : esc(r.route.label);
    return `<ol class="steps">${(o.steps || []).map((s) => `<li>${esc(clean(s))}</li>`).join("")}</ol>
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
  function renderResult(r, keep) {
    const open = {};
    if (keep) $$("#result details[data-g]").forEach((d) => { open[d.dataset.g] = d.open; });
    const wide = matchMedia("(min-width: 700px)").matches;
    const grp = (id, title, body, dflt) => `<details class="grp" data-g="${id}"${(id in open ? open[id] : dflt || wide) ? " open" : ""}><summary><h2>${esc(title)}</h2></summary><div class="gbody">${body}</div></details>`;
    const v = r.verdict, f = r.fields, ps = paras(r), lg = paraLang(r), steps = verifyOf(r);
    const chip = (k, val) => `<span class="fact"><span>${esc(t(k))}</span><b>${esc(val ? tr(val) : t("not_found"))}</b></span>`;
    const learnable = r.terms.filter((x) => D.glossary[x]);
    const allIn = learnable.length && learnable.every((x) => state.learned.has(x));
    const reexplain = !r.sample && r.lang !== state.xl && state.last;
    $("#result").innerHTML = `
      <div class="rbar">
        <button class="btn btn-secondary" type="button" data-act="again">&larr; <span>${esc(t("r_again"))}</span></button>
        <button class="btn btn-secondary speak" type="button" data-act="speak">${svg("speaker")}<span>${esc(t("listen"))}</span></button>
      </div>
      <div class="verdict v-${v}${keep ? "" : " fresh"}">${svg(v)}<div><h1 id="vHead" tabindex="-1">${esc(t("v_" + v))}</h1><p>${esc(t("vs_" + v))}</p></div></div>
      <p class="muted vnote" id="vnote" role="status"></p>
      ${r.sample ? `<p class="note">${esc(t("sample_note"))}${state.lang !== "en" ? " " + esc(t("sample_lang")) : ""}</p>` : ""}

      <section class="card next" aria-labelledby="nextH">
        <h2 class="h3" id="nextH">${esc(t("next_h"))}</h2>
        <p class="next-step">${esc(clean(steps[0]))}</p>
        <button class="btn btn-secondary" type="button" data-act="sum"><span>${esc(t("r_copy_sum"))}</span></button>
      </section>

      ${grp("why", t("h_why"), `<ul class="reasons" lang="${HTML_LANG[r.sample ? state.lang : r.lang]}">${r.reasons.map((x) => `<li class="r-${x.k}">${svg(x.k)}<div><span class="rk">${esc(t("rk_" + x.k))}</span>${esc(x.text === null ? t("info_default") : tr(clean(x.text)))}</div></li>`).join("")}</ul>`, true)}
      ${grp("verify", t("h_verify"), `<ol class="steps" lang="${HTML_LANG[r.sample ? state.lang : r.lang]}">${steps.map((x) => `<li>${esc(clean(x))}</li>`).join("")}</ol>`, true)}
      ${grp("says", t("h_says"), `<div lang="${HTML_LANG[lg]}">${ps.map((p) => `<p>${esc(clean(p))}</p>`).join("")}</div>
        ${reexplain ? `<p class="muted">${esc(t("x_note", { a: langName(r.lang) }))}</p><button class="btn btn-secondary" type="button" data-act="reexplain"><span>${esc(t("x_btn", { b: langName(state.xl) }))}</span></button>` : ""}
        <div class="facts">${chip("f_from", f.issuer)}${chip("f_amount", f.amount)}${chip("f_deadline", f.deadline)}${chip("f_ref", f.reference)}</div>`)}
      ${grp("todo", t("h_todo"), `<div class="seg" role="group" aria-label="${esc(t("h_todo"))}">
          <button type="button" class="chip" data-route="online" aria-pressed="${state.route === "online"}">${esc(t("online"))}</button>
          <button type="button" class="chip" data-route="walkin" aria-pressed="${state.route !== "online"}">${esc(t("office"))}</button>
        </div><div id="routePanel">${routeHtml(r)}</div>`)}
      ${grp("draft", t("h_draft"), `<p><b>${esc(t("rem_label"))}</b> ${esc(reminderText(r))}</p>
        <p class="muted">${esc(t("draft_hint"))}</p>
        <pre class="draft" lang="ms">${esc(r.draft)}</pre>
        <button class="btn btn-primary" type="button" data-act="copy"><span>${esc(t("copy"))}</span></button>
        <p class="note"><b>${esc(t("draft_note_b"))}</b> ${esc(t("draft_note"))}</p>`)}
      ${grp("learn", t("h_learn"), `<h3 class="h3">${esc(tr(r.kenapa.q))}</h3>
        <p>${esc(clean(r.kenapa.a))}</p>
        ${learnable.length ? `<p class="muted">${esc(t("words_in"))} ${learnable.map(esc).join(", ")}</p>
        <button class="btn btn-secondary" type="button" data-act="add" ${allIn ? "disabled" : ""}><span>${esc(allIn ? t("added") : t("add"))}</span></button>` : ""}`)}

      <details class="trace"><summary>${esc(t("tr_sum"))}</summary>
        <p class="muted">${esc(t("tr_note"))}</p>
        <ol class="trace-list" lang="en">${(r.trace || []).map((x) => `<li class="${x.flag ? "flag" : ""}"><span class="tag">${esc(STATUS[x.k] ? t(STATUS[x.k]) : t("st_step"))}${x.t ? " " + esc(x.t) : ""}</span>${esc(clean(x.m))}</li>`).join("") || `<li>${esc(t("tr_none"))}</li>`}</ol>
      </details>
      <p class="muted">${esc(t("disc"))}</p>`;
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
    else if (act === "speak") readAloud(paras(r).map(clean).join(" "), paraLang(r), a, $("#vnote"));
    else if (act === "reexplain") { backToChecker(); checkOwn(state.last); }
    else if (act === "add") {
      const fresh = r.terms.filter((x) => D.glossary[x] && !state.learned.has(x));
      fresh.forEach((x) => state.learned.add(x));
      addXP(fresh.length * 5); save();
      a.disabled = true; a.querySelector("span").textContent = t("added");
      toast(t(fresh.length === 1 ? "w1" : "wn", { n: fresh.length }));
    }
  });

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
    Object.assign(state, { lang: "bm", xl: "bm", xlManual: false, theme: "light", learned: new Set(), xp: 0, result: null, last: null });
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
  renderChips(); setTheme(); applyI18n(); syncChips(); renderMode(); renderExamples(); updateCount(true); renderLevel(); fillFamily();
  $("#hint").hidden = !!store.get("checked", false);
  state.practice.order = D.practice.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
  renderPractice(); route(true); checkApi();
})();
