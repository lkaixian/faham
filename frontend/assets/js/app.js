/* FAHAM front end: vanilla JS, no build step.
   Flow: form or example -> POST /api/analyze (or local sample when offline) -> one result object -> renderResult. */
(function () {
  const D = window.FAHAM_DATA;
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
  const state = {
    lang: D.languages[store.get("lang", "bm")] ? store.get("lang", "bm") : "bm",
    theme: store.get("theme", "light"),
    learned: new Set(store.get("learned", [])),
    xp: store.get("xp", 0),
    api: false, busy: false,
    result: null, last: null, route: "online",
    practice: { items: D.practice, order: [], i: 0, score: 0, answered: false, results: [] }
  };
  const CONSENT_V = 1;
  const consented = () => (store.get("consent", null) || {}).v === CONSENT_V;
  const save = () => { store.set("lang", state.lang); store.set("learned", [...state.learned]); store.set("xp", state.xp); store.set("theme", state.theme); };
  const HTML_LANG = { bm: "ms", en: "en", zh: "zh", ta: "ta" };

  /* ---------- UI strings (zh and ta need native review) ---------- */
  const T = {
    en: { nav_check: "Check", nav_practice: "Practice", nav_dict: "My dictionary", nav_family: "Family", nav_about: "About and privacy", btn_check: "Check now",
      v_likely_scam: "Likely a scam. Do not pay or click.", v_caution: "Be careful. We could not confirm this.", v_no_signals: "No scam signs found. This does not prove it is real.",
      vs_likely_scam: "Do not pay, do not click, and do not call the number in it.", vs_caution: "Do not pay or share any code yet. Check it yourself using the steps below.", vs_no_signals: "Scammers can write convincing messages. Still check it yourself before you pay.",
      h_why: "Why we say this", h_verify: "Check it yourself", h_says: "What the letter says", h_todo: "What to do", online: "Online", office: "At the office", h_draft: "Reminder and draft reply",
      listen: "Read aloud", stop: "Stop reading", copy: "Copy", again: "Check another", add: "Add to my dictionary", added: "Added to my dictionary",
      rk_risk: "Warning", rk_ok: "Good sign", rk_info: "Note",
      fam_foot: "Check with the official agency before paying. Call NSRC 997 if you were scammed." },
    bm: { nav_check: "Semak", nav_practice: "Latihan", nav_dict: "Kamus saya", nav_family: "Keluarga", nav_about: "Tentang dan privasi", btn_check: "Semak sekarang",
      v_likely_scam: "Berkemungkinan scam. Jangan bayar atau klik.", v_caution: "Berhati-hati. Kami tidak dapat mengesahkannya.", v_no_signals: "Tiada tanda scam ditemui. Ini tidak membuktikan ia sahih.",
      vs_likely_scam: "Jangan bayar, jangan klik, jangan telefon nombor di dalamnya.", vs_caution: "Jangan bayar atau beri kod lagi. Semak sendiri dengan langkah di bawah.", vs_no_signals: "Penipu boleh menulis mesej yang meyakinkan. Tetap semak sendiri sebelum bayar.",
      h_why: "Kenapa kami kata begini", h_verify: "Semak sendiri", h_says: "Apa kata surat ini", h_todo: "Apa yang perlu dibuat", online: "Dalam talian", office: "Di pejabat", h_draft: "Peringatan dan draf balasan",
      listen: "Baca kuat-kuat", stop: "Henti baca", copy: "Salin", again: "Semak yang lain", add: "Tambah ke kamus saya", added: "Sudah ditambah ke kamus saya",
      rk_risk: "Amaran", rk_ok: "Tanda baik", rk_info: "Catatan",
      fam_foot: "Semak dengan agensi rasmi sebelum bayar. Hubungi NSRC 997 jika terkena scam." },
    zh: { nav_check: "检查", nav_practice: "练习", nav_dict: "我的词典", nav_family: "家人", nav_about: "关于与隐私", btn_check: "立即检查",
      v_likely_scam: "很可能是诈骗。请勿付款或点击链接。", v_caution: "请小心。我们无法确认这一点。", v_no_signals: "没有发现诈骗迹象。这并不证明它是真的。",
      vs_likely_scam: "不要付款、不要点击链接、不要拨打其中的号码。", vs_caution: "先不要付款或透露验证码。请按下面的步骤自行核实。", vs_no_signals: "骗子也能写出很像样的信息。付款前仍请自行核实。",
      h_why: "我们为什么这样判断", h_verify: "请自己核实", h_says: "信件内容", h_todo: "该怎么做", online: "线上", office: "到办事处", h_draft: "提醒和回复草稿",
      listen: "朗读", stop: "停止朗读", copy: "复制", again: "检查另一封", add: "加入我的词典", added: "已加入我的词典",
      rk_risk: "警告", rk_ok: "正面迹象", rk_info: "说明",
      fam_foot: "付款前请先向官方机构核实。如已受骗，请拨打 NSRC 997。" },
    ta: { nav_check: "சரிபார்", nav_practice: "பயிற்சி", nav_dict: "என் அகராதி", nav_family: "குடும்பம்", nav_about: "பற்றி மற்றும் தனியுரிமை", btn_check: "இப்போது சரிபார்",
      v_likely_scam: "இது மோசடியாக இருக்க வாய்ப்பு அதிகம். பணம் செலுத்தவோ கிளிக் செய்யவோ வேண்டாம்.", v_caution: "கவனமாக இருங்கள். இதை எங்களால் உறுதிப்படுத்த முடியவில்லை.", v_no_signals: "மோசடி அறிகுறிகள் எதுவும் இல்லை. இது உண்மையானது என்பதை நிரூபிக்காது.",
      vs_likely_scam: "பணம் செலுத்த வேண்டாம், கிளிக் செய்ய வேண்டாம், அதிலுள்ள எண்ணை அழைக்க வேண்டாம்.", vs_caution: "இப்போதைக்கு பணம் செலுத்தவோ குறியீடு தரவோ வேண்டாம். கீழே உள்ள படிகளால் நீங்களே சரிபார்க்கவும்.", vs_no_signals: "மோசடிக்காரர்கள் நம்பும்படி எழுதலாம். பணம் செலுத்தும் முன் நீங்களே சரிபார்க்கவும்.",
      h_why: "ஏன் இப்படிச் சொல்கிறோம்", h_verify: "நீங்களே சரிபார்க்கவும்", h_says: "கடிதம் என்ன சொல்கிறது", h_todo: "என்ன செய்ய வேண்டும்", online: "ஆன்லைன்", office: "அலுவலகத்தில்", h_draft: "நினைவூட்டல் மற்றும் பதில் வரைவு",
      listen: "உரக்கப் படிக்கவும்", stop: "படிப்பதை நிறுத்து", copy: "நகலெடு", again: "மற்றொன்றைச் சரிபார்", add: "என் அகராதியில் சேர்", added: "என் அகராதியில் சேர்க்கப்பட்டது",
      rk_risk: "எச்சரிக்கை", rk_ok: "நல்ல அறிகுறி", rk_info: "குறிப்பு",
      fam_foot: "பணம் செலுத்தும் முன் அதிகாரப்பூர்வ நிறுவனத்தில் சரிபார்க்கவும். ஏமாற்றப்பட்டிருந்தால் NSRC 997-ஐ அழைக்கவும்." }
  };
  const t = (k) => (T[state.lang] && T[state.lang][k]) || T.en[k] || k;
  function applyI18n() {
    document.documentElement.lang = HTML_LANG[state.lang];
    $$("[data-t]").forEach((el) => {
      const own = T[state.lang] && T[state.lang][el.dataset.t];
      el.textContent = own || T.en[el.dataset.t];
      if (own) el.removeAttribute("lang"); else el.lang = "en";
    });
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
    const ok = () => toast(done || "Copied");
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, () => toast("Could not copy. Select the text and copy it by hand."));
    else toast("Could not copy. Select the text and copy it by hand.");
  }
  function speak(text, lang, btn) {
    if (!("speechSynthesis" in window)) { toast("Read-aloud is not supported in this browser."); return; }
    if (speechSynthesis.speaking) { speechSynthesis.cancel(); if (btn) btn.querySelector("span").textContent = t("listen"); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = D.languages[lang].speech; u.rate = 0.9;
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.toLowerCase().startsWith(u.lang.slice(0, 2).toLowerCase()));
    if (v) u.voice = v; else toast("No " + D.languages[lang].name + " voice on this device. Using the default voice.");
    const reset = () => { if (btn) btn.querySelector("span").textContent = t("listen"); };
    u.onend = reset; u.onerror = reset;
    if (btn) btn.querySelector("span").textContent = t("stop");
    speechSynthesis.speak(u);
  }
  const stopSpeech = () => { try { speechSynthesis.cancel(); } catch (e) {} };

  /* ---------- verdict, reasons, verify: backend fields, with a defensive fallback ---------- */
  const VERDICTS = ["likely_scam", "caution", "no_signals"];
  const deriveVerdict = (s) => (VERDICTS.includes(s.verdict) ? s.verdict : s.genuine === false ? "likely_scam" : "caution");
  function reasonKind(x) {
    const k = String(x || "").toLowerCase();
    return /risk|bad|red|flag|warn|danger/.test(k) ? "risk" : /ok|good|pass|safe|positive/.test(k) ? "ok" : "info";
  }
  const INFO_DEFAULT = "FAHAM only reads the words. It cannot see who really sent this, open the link or check the phone number.";
  function normReasons(s) {
    let out = [];
    if (Array.isArray(s.reasons) && s.reasons.length) {
      out = s.reasons.map((x) => typeof x === "string" ? { k: "info", text: x } : { k: reasonKind(x.kind || x.type || x.level || x.status), text: x.text || x.message || x.reason || x.label || "" }).filter((x) => x.text);
    } else {
      out = [...(s.red_flags || []).map((x) => ({ k: "risk", text: x })), ...(s.good_signs || []).map((x) => ({ k: "ok", text: x }))];
    }
    if (!out.some((x) => x.k === "info")) out.push({ k: "info", text: INFO_DEFAULT });
    return out;
  }
  const VERIFY_DEFAULT = {
    likely_scam: ["Do not open the link or reply to the number in the message.", "Look up the agency's own website or phone number yourself and ask them.", "If you already paid or shared a code, call your bank, then NSRC 997."],
    caution: ["Do not use the links or phone numbers inside the message.", "Look up the agency's own website or phone number yourself and ask them.", "Show it to someone you trust before you pay. If in doubt, call NSRC 997."],
    no_signals: ["Check the sender on the agency's official website, not through the message.", "Only pay inside the agency's official app or website that you opened yourself.", "If anything feels wrong, ask the agency or call NSRC 997."]
  };
  function normVerify(s, v) {
    const a = Array.isArray(s.verify_yourself) ? s.verify_yourself.map((x) => typeof x === "string" ? x : (x && (x.text || x.message || x.step)) || "").filter(Boolean) : [];
    return a.length ? a : VERIFY_DEFAULT[v];
  }
  const applyScam = (r, s) => Object.assign(r, { verdict: deriveVerdict(s), reasons: normReasons(s), verify: normVerify(s, deriveVerdict(s)) });

  /* ---------- build one result object from the API or from a bundled sample ---------- */
  const STATUS = { think: "Thinking", tool: "Tool", ok: "OK", bad: "Problem", warn: "Note" };
  const mapTrace = (tr) => (tr || []).map((x) => ({ k: x.kind, t: x.tool, m: x.message, flag: x.flag }));
  function fromApi(d, lang) {
    const f = d.fields, r = d.route;
    return applyScam({
      sample: false, lang, explain: { [lang]: String(d.explanation || "").split(/\n+/).filter(Boolean) },
      fields: { issuer: f.issuer, type: f.letter_type, amount: f.amount, deadline: f.deadline, reference: f.reference },
      kenapa: { q: d.lesson.question, a: d.lesson.answer }, terms: d.lesson.terms || [],
      route: { url: r.source_url, label: String(r.source_url).replace(/^https?:\/\//, ""), date: r.retrieved_at, confidence: r.confidence,
        online: { steps: r.online_steps, prepare: r.prepare_online }, walkin: { steps: r.walkin_steps, prepare: r.prepare_walkin } },
      reminder: d.action.reminder, draft: d.action.draft, trace: mapTrace(d.trace), disclaimer: d.disclaimer
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
  const paras = (r) => r.explain[state.lang] || r.explain[r.lang] || Object.values(r.explain)[0] || [];
  const paraLang = (r) => (r.explain[state.lang] ? state.lang : r.explain[r.lang] ? r.lang : state.lang);

  /* ---------- API ---------- */
  async function post(body, ms) {
    try {
      const ctrl = new AbortController(); const to = setTimeout(() => ctrl.abort(), ms);
      const res = await fetch(CFG.API_BASE + "/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, signal: ctrl.signal, body: JSON.stringify(body) });
      clearTimeout(to);
      if (res.status === 422) {
        const d = await res.json().catch(() => ({}));
        return { error: (typeof d.detail === "string" ? d.detail : "We could not read this.") + " Try pasting the text instead." };
      }
      if (!res.ok) return { error: "The checker had a problem (" + res.status + "). Please try again, or try an example." };
      return { data: await res.json() };
    } catch (e) { return { error: "Could not reach the checker. Check your internet, or try an example." }; }
  }
  const readB64 = (f) => new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1]); r.onerror = () => no(r.error); r.readAsDataURL(f); });

  function setBusy(on, msg) {
    state.busy = on;
    $("#busy").hidden = !on; $("#busyTxt").textContent = msg || "";
    $("#checkBtn").disabled = on || !state.api; $$(".example").forEach((b) => (b.disabled = on));
  }
  const formErr = (m) => { $("#formErr").textContent = m || ""; };

  async function checkOwn(inp) {
    state.last = inp; formErr(""); stopSpeech();
    setBusy(true, "Checking. Reading a photo can take a few seconds. / Sedang menyemak.");
    const body = { language: state.lang };
    const pc = $("#postBox").value.trim(); if (/^\d{1,5}$/.test(pc)) body.postcode = pc;
    try { if (inp.text) body.text = inp.text; else body.image_b64 = await readB64(inp.file); } catch (e) { setBusy(false); formErr("Could not read that file. Try another photo or paste the text."); return; }
    const x = await post(body, 30000);
    setBusy(false);
    if (x.error) { formErr(x.error); return; }
    show(fromApi(x.data, state.lang));
  }
  async function checkSample(id) {
    const l = D.letters.find((z) => z.id === id); if (!l) return;
    state.last = null; formErr(""); stopSpeech();
    setBusy(true, "Checking the example...");
    const r = fromSample(l);
    if (state.api) {
      const text = [l.title, "Rujukan: " + l.ref, "Daripada: " + l.issuer + " " + l.issuerShort, "Kepada: " + l.to, ...l.body.map((b) => b.replace(/<[^>]+>/g, ""))].join("\n");
      const x = await post({ text, language: state.lang, sample_id: l.id }, 8000);
      if (x.data) { r.trace = mapTrace(x.data.trace); applyScam(r, x.data.scam); }
    }
    setBusy(false);
    show(r);
  }

  $("#form").addEventListener("submit", (e) => {
    e.preventDefault(); if (state.busy) return;
    const text = $("#pasteBox").value.trim(), file = $("#fileBox").files[0];
    if (!state.api) { formErr("The checker is offline. Please try an example below."); return; }
    if (!text && !file) { formErr("Paste a message or upload a photo first. Or try an example below."); $("#pasteBox").focus(); return; }
    if (text && text.length < 10) { formErr("That is too short. Please paste at least 10 characters."); $("#pasteBox").focus(); return; }
    if (!consented()) { formErr("Please tick the box below first (Sila tanda kotak di bawah)."); $("#consentBox").focus(); return; }
    checkOwn(text ? { text } : { file });
  });
  $("#pasteBox").addEventListener("input", () => { if ($("#pasteBox").value) $("#fileBox").value = ""; formErr(""); });
  $("#fileBox").addEventListener("change", () => {
    const f = $("#fileBox").files[0]; formErr("");
    if (!f) return;
    if (!/^image\/(png|jpeg)$/.test(f.type)) { $("#fileBox").value = ""; formErr("Only PNG or JPEG photos work. You can paste the text instead."); return; }
    if (f.size > 4 * 1024 * 1024) { $("#fileBox").value = ""; formErr("That photo is over 4 MB. Use a smaller photo or paste the text."); return; }
    $("#pasteBox").value = "";
  });
  $("#clearInput").addEventListener("click", () => { $("#pasteBox").value = ""; $("#fileBox").value = ""; $("#postBox").value = ""; formErr(""); });
  $("#consentBox").checked = consented();
  $("#consentBox").addEventListener("change", (e) => {
    if (e.target.checked) { store.set("consent", { v: CONSENT_V }); formErr(""); } else { try { localStorage.removeItem("faham_consent"); } catch (x) {} }
  });

  function renderChips() {
    $("#langChips").innerHTML = Object.entries(D.languages).map(([k, v]) => `<button type="button" class="chip" data-l="${esc(k)}" lang="${HTML_LANG[k]}" aria-pressed="${k === state.lang}">${esc(v.label)}</button>`).join("");
  }
  $("#langChips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-l]"); if (!b || b.dataset.l === state.lang) return;
    state.lang = b.dataset.l; save(); renderChips(); applyI18n(); stopSpeech();
    if (!$("#result").hidden && state.result) {
      if (state.result.sample || !state.last) renderResult(state.result); else checkOwn(state.last);
    }
    if (location.hash === "#family") renderFamily();
  });
  function renderExamples() {
    $("#examples").innerHTML = D.letters.map((l) => `<button type="button" class="example" data-id="${esc(l.id)}"><b>${esc(l.short)}</b><span>${esc(l.kind)}</span></button>`).join("");
  }
  $("#examples").addEventListener("click", (e) => { const b = e.target.closest("[data-id]"); if (b && !state.busy) checkSample(b.dataset.id); });

  /* ---------- result screen ---------- */
  function show(r) {
    state.result = r; state.route = "online";
    renderResult(r);
    $("#checker").hidden = true; $("#result").hidden = false;
    window.scrollTo(0, 0);
    const h = $("#vHead"); if (h) h.focus();
  }
  function backToChecker() {
    stopSpeech();
    $("#result").hidden = true; $("#checker").hidden = false;
    window.scrollTo(0, 0); $("#checker h1").focus();
  }
  function routeHtml(r) {
    const o = r.route[state.route === "online" ? "online" : "walkin"];
    const src = /^https:\/\//.test(r.route.url || "") ? `<a href="${esc(r.route.url)}" target="_blank" rel="noopener noreferrer">${esc(r.route.label)}</a>` : esc(r.route.label);
    return `<ol class="steps">${(o.steps || []).map((s) => `<li>${esc(clean(s))}</li>`).join("")}</ol>
      ${(o.prepare || []).length ? `<p class="muted">Have ready:</p><div class="facts">${o.prepare.map((p) => `<span class="fact">${esc(p)}</span>`).join("")}</div>` : ""}
      <p class="src">Source: ${src}. Saved copy dated: ${esc(r.route.date)}. Confidence: ${esc(r.route.confidence)}. Check the official site before you act.</p>`;
  }
  function renderResult(r) {
    const v = r.verdict, f = r.fields, ps = paras(r), lg = paraLang(r);
    const chip = (k, val) => `<span class="fact"><span>${k}</span><b>${esc(val || "Not found")}</b></span>`;
    const learnable = r.terms.filter((x) => D.glossary[x]);
    const allIn = learnable.length && learnable.every((x) => state.learned.has(x));
    $("#result").innerHTML = `
      <button class="btn btn-secondary" type="button" data-act="again">&larr; <span>${esc(t("again"))}</span></button>
      <div class="verdict v-${v}">${svg(v)}<div><h2 id="vHead" tabindex="-1">${esc(t("v_" + v))}</h2><p>${esc(t("vs_" + v))}</p></div></div>
      ${r.sample ? '<p class="note">This is a fictional example, not a real letter.</p>' : ""}

      <h2>${esc(t("h_why"))}</h2>
      <div class="card"><ul class="reasons">${r.reasons.map((x) => `<li class="r-${x.k}">${svg(x.k)}<div><span class="rk">${esc(t("rk_" + x.k))}</span>${esc(clean(x.text))}</div></li>`).join("")}</ul></div>

      <h2>${esc(t("h_verify"))}</h2>
      <div class="card"><ol class="steps">${r.verify.map((x) => `<li>${esc(clean(x))}</li>`).join("")}</ol></div>

      <h2>${esc(t("h_says"))}</h2>
      <div class="card">
        <div lang="${HTML_LANG[lg]}">${ps.map((p) => `<p>${esc(clean(p))}</p>`).join("")}</div>
        <button class="btn btn-secondary" type="button" data-act="speak">${svg("speaker")}<span>${esc(t("listen"))}</span></button>
        <div class="facts">${chip("From", f.issuer)}${chip("Amount", f.amount)}${chip("Deadline", f.deadline)}${chip("Reference", f.reference)}</div>
      </div>

      <h2>${esc(t("h_todo"))}</h2>
      <div class="card">
        <div class="seg" role="group" aria-label="${esc(t("h_todo"))}">
          <button type="button" class="chip" data-route="online" aria-pressed="true">${esc(t("online"))}</button>
          <button type="button" class="chip" data-route="walkin" aria-pressed="false">${esc(t("office"))}</button>
        </div>
        <div id="routePanel">${routeHtml(r)}</div>
      </div>

      <h2>${esc(t("h_draft"))}</h2>
      <div class="card">
        <p><b>Reminder:</b> ${esc(r.reminder || "No reminder needed.")}</p>
        <p class="muted">Draft reply (edit the [brackets] before you use it):</p>
        <pre class="draft" id="draftTxt">${esc(r.draft)}</pre>
        <button class="btn btn-primary" type="button" data-act="copy"><span>${esc(t("copy"))}</span></button>
        <p class="note"><b>Nothing is sent automatically.</b> FAHAM cannot send, pay or contact anyone. Copy the words and send them yourself.</p>
      </div>

      <div class="card">
        <h2 class="h3">${esc(r.kenapa.q)}</h2>
        <p>${esc(clean(r.kenapa.a))}</p>
        ${learnable.length ? `<p class="muted">Words in this letter: ${learnable.map(esc).join(", ")}</p>
        <button class="btn btn-secondary" type="button" data-act="add" ${allIn ? "disabled" : ""}><span>${esc(allIn ? t("added") : t("add"))}</span></button>` : ""}
      </div>

      <details class="trace"><summary>How the agent worked</summary>
        <ol class="trace-list">${(r.trace || []).map((x) => `<li class="${x.flag ? "flag" : ""}"><span class="tag">${esc(STATUS[x.k] || "Step")}${x.t ? " " + esc(x.t) : ""}</span>${esc(clean(x.m))}</li>`).join("") || "<li>No trace available.</li>"}</ol>
      </details>
      <p class="muted">${esc(clean(r.disclaimer || "FAHAM gives guidance, not legal advice."))}</p>
      <button class="btn btn-secondary" type="button" data-act="again">&larr; <span>${esc(t("again"))}</span></button>`;
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
    if (a.dataset.act === "again") backToChecker();
    else if (a.dataset.act === "copy") copyText(r.draft, "Draft copied. Nothing was sent.");
    else if (a.dataset.act === "speak") speak(paras(r).map(clean).join(" "), paraLang(r), a);
    else if (a.dataset.act === "add") {
      const fresh = r.terms.filter((x) => D.glossary[x] && !state.learned.has(x));
      fresh.forEach((x) => state.learned.add(x));
      addXP(fresh.length * 5); save();
      a.disabled = true; a.querySelector("span").textContent = t("added");
      toast(fresh.length + " new word" + (fresh.length === 1 ? "" : "s") + " in My dictionary");
    }
  });

  /* ---------- levels and dictionary ---------- */
  const levelFor = (xp) => D.levels.reduce((l, x) => (xp >= x.min ? x : l), D.levels[0]);
  function addXP(n) {
    if (!n) return;
    const before = levelFor(state.xp).name; state.xp += n; save(); renderLevel();
    const after = levelFor(state.xp).name; if (after !== before) toast("New level: " + after);
  }
  function renderLevel() {
    const cur = levelFor(state.xp), next = D.levels[D.levels.indexOf(cur) + 1];
    $("#lvlName").textContent = cur.name;
    $("#lvlBar").style.width = (next ? ((state.xp - cur.min) / (next.min - cur.min)) * 100 : 100) + "%";
    $("#lvlNext").textContent = next ? `${state.xp} points. ${next.min - state.xp} more to reach ${next.name}.` : `${state.xp} points. Top level reached.`;
  }
  function renderGlossary() {
    const q = ($("#glossSearch").value || "").trim().toLowerCase();
    const list = Object.entries(D.glossary).filter(([k, v]) => !q || k.toLowerCase().includes(q) || v.def.toLowerCase().includes(q))
      .sort((a, b) => state.learned.has(b[0]) - state.learned.has(a[0]));
    $("#glossGrid").innerHTML = list.map(([k, v]) => state.learned.has(k)
      ? `<div class="term"><small>${esc(v.src)}</small><b>${esc(k)}</b><p>${esc(v.def)}</p></div>`
      : `<div class="term locked"><b>${esc(k)}</b><p>Not added yet. Check a letter with this word and press "Add to my dictionary".</p></div>`).join("")
      || `<p class="muted">No word matches "${esc(q)}".</p>`;
    $("#glossCount").textContent = state.learned.size ? `${state.learned.size} of ${Object.keys(D.glossary).length} words added.` : "Nothing added yet. Check a letter, then press Add to my dictionary.";
  }
  $("#glossSearch").addEventListener("input", renderGlossary);

  /* ---------- practice ---------- */
  const verdictHead = (s) => t("v_" + deriveVerdict(s));
  async function newRound() {
    const my = (newRound.n = (newRound.n || 0) + 1);
    let items = D.practice, note = "";
    $("#pFeedback").innerHTML = "";
    if (state.api) {
      $("#pCard").textContent = "Loading messages..."; $("#pChoices").hidden = true;
      try {
        const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 6000);
        const res = await fetch(CFG.API_BASE + "/api/practice?n=6", { signal: ctrl.signal });
        if (!res.ok) throw new Error(res.status);
        const got = await res.json(); if (!got.length) throw new Error("empty");
        items = got.map((x) => ({ from: x.sender, kind: x.channel, text: x.text, scam: x.is_scam, clues: x.clues, agent: x.agent }));
      } catch (e) { note = "Could not load new messages. Using the saved ones."; }
      if (my !== newRound.n) return;
    }
    const order = items.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
    state.practice = { items, order, i: 0, score: 0, answered: false, results: [] };
    renderPractice(); if (note) toast(note);
  }
  function renderPractice() {
    const p = state.practice;
    $("#pFeedback").innerHTML = "";
    if (!p.order.length) { $("#pCard").textContent = "No messages available right now."; $("#pChoices").hidden = true; return; }
    if (p.i >= p.order.length) {
      const msg = p.score >= 5 ? "Very good. You spot scams well." : p.score >= 3 ? "Good. Read the clues again and try another round." : "Scammers are tricky. Try another round; the clues will stick.";
      $("#pCard").innerHTML = `<b>Round finished: ${p.score} of ${p.order.length}</b><br />${esc(msg)}`;
      $("#pChoices").hidden = true; $("#pCount").textContent = "Done";
    } else {
      const it = p.items[p.order[p.i]];
      $("#pCard").innerHTML = `<div class="from">From: <b>${esc(it.from)}</b> (${esc(it.kind)}, fictional)</div>${esc(it.text)}`;
      $("#pChoices").hidden = false; p.answered = false;
      $("#pCount").textContent = `Message ${p.i + 1} of ${p.order.length}`;
    }
    $("#pScore").textContent = `${p.score} / ${p.results.length}`;
  }
  function agentLine(a) {
    if (!a) return "";
    const flags = (a.red_flags || []).map((x) => `<li>${esc(clean(x))}</li>`).join("");
    return `<p><b>What FAHAM's check says:</b> ${esc(verdictHead(a))}</p>${flags ? `<ul>${flags}</ul>` : ""}`;
  }
  $("#pChoices").addEventListener("click", (e) => {
    const b = e.target.closest("[data-a]"), p = state.practice; if (!b || p.answered) return;
    p.answered = true;
    const it = p.items[p.order[p.i]], right = (b.dataset.a === "scam") === it.scam;
    p.results.push(right); if (right) { p.score++; addXP(10); }
    $("#pFeedback").innerHTML = `<div class="fb ${right ? "right" : "wrong"}"><h3>${right ? "Correct." : "Not quite."} This one is ${it.scam ? "a scam" : "a normal message"}.</h3>
      <p>Clues:</p><ul>${it.clues.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>${agentLine(it.agent)}
      <button class="btn btn-primary" type="button" id="pNext">${p.i + 1 < p.order.length ? "Next message" : "See my score"}</button></div>`;
    $("#pChoices").hidden = true; $("#pScore").textContent = `${p.score} / ${p.results.length}`;
    $("#pNext").addEventListener("click", () => { p.i++; renderPractice(); });
    $("#pNext").focus();
  });
  $("#pRestart").addEventListener("click", newRound);

  /* ---------- family ---------- */
  function fillFamily() {
    $("#fLang").innerHTML = Object.entries(D.languages).map(([k, v]) => `<option value="${esc(k)}">${esc(v.name)}</option>`).join("");
    $("#fLang").value = state.lang;
    $("#fLetter").addEventListener("change", renderFamily); $("#fLang").addEventListener("change", renderFamily);
  }
  let famText = "", famLang = "bm";
  function renderFamily() {
    const sel = $("#fLetter"), keep = sel.value;
    sel.innerHTML = D.letters.map((l) => `<option value="${esc(l.id)}">${esc(l.short)}: ${esc(l.kind)}</option>`).join("") + (state.result && !state.result.sample ? '<option value="mine">The letter I just checked</option>' : "");
    sel.value = [...sel.options].some((o) => o.value === keep) ? keep : D.letters[0].id;
    const lang = $("#fLang").value, saved = sel.value === "mine";
    const r = saved ? state.result : fromSample(D.letters.find((l) => l.id === sel.value));
    const ps = r.explain[lang] || r.explain[r.lang];
    famLang = r.explain[lang] ? lang : r.lang;
    $("#fNote").textContent = r.explain[lang] ? "" : "Your letter was checked in " + D.languages[r.lang].name + ". Check it again in " + D.languages[lang].name + " to get this language.";
    famText = (saved ? "" : (D.letters.find((l) => l.id === sel.value).short + "\n\n")) + ps.map(clean).join("\n\n") + "\n\n" + ((T[famLang] || T.en).fam_foot);
    $("#fMsg").lang = HTML_LANG[famLang]; $("#fMsg").textContent = famText;
  }
  $("#fCopy").addEventListener("click", () => copyText(famText, "Message copied. FAHAM did not send it."));
  $("#fSpeak").addEventListener("click", () => speak(famText, famLang, null));

  /* ---------- pages, theme, data ---------- */
  const VIEWS = ["check", "practice", "dictionary", "family", "about"];
  function route(first) {
    const v = VIEWS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "check";
    VIEWS.forEach((n) => ($("#view-" + n).hidden = n !== v));
    $$(".top nav a").forEach((a) => (a.getAttribute("href") === "#" + v ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    const sec = $("#view-" + v); document.title = "FAHAM: " + sec.dataset.title;
    stopSpeech();
    if (v === "dictionary") { renderGlossary(); renderLevel(); }
    if (v === "family") renderFamily();
    if (!first) { window.scrollTo(0, 0); const h = $("h1", sec); if (h) h.focus(); }
  }
  window.addEventListener("hashchange", () => route(false));
  function setTheme() {
    document.documentElement.dataset.theme = state.theme;
    $("#themeBtn").setAttribute("aria-pressed", state.theme === "dark");
    $("#themeLbl").textContent = state.theme === "dark" ? "Light" : "Dark";
    $('meta[name="theme-color"]').setAttribute("content", state.theme === "dark" ? "#0e1719" : "#0b5c63");
  }
  $("#themeBtn").addEventListener("click", () => { state.theme = state.theme === "dark" ? "light" : "dark"; save(); setTheme(); });
  $("#clearData").addEventListener("click", () => {
    if (state.busy) { toast("Wait for the check to finish first."); return; }
    try { Object.keys(localStorage).filter((k) => k.startsWith("faham_")).forEach((k) => localStorage.removeItem(k)); } catch (e) {}
    Object.assign(state, { lang: "bm", theme: "light", learned: new Set(), xp: 0, result: null, last: null });
    $("#consentBox").checked = false; $("#pasteBox").value = ""; $("#fileBox").value = ""; $("#postBox").value = ""; formErr("");
    $("#result").hidden = true; $("#result").innerHTML = ""; $("#checker").hidden = false;
    renderChips(); applyI18n(); setTheme(); renderLevel(); renderGlossary(); fillFamily(); newRound();
    $("#clearMsg").textContent = "Done. Your dictionary, points, language choice and tick were removed from this browser.";
  });

  /* ---------- API status ---------- */
  function setMode(online) {
    state.api = online;
    $("#mode").innerHTML = online ? "<b>Checker online</b>" : "<b>Sample mode</b>: checker offline, examples only";
    $("#offlineNote").hidden = online;
    ["pasteBox", "fileBox", "postBox", "clearInput"].forEach((id) => ($("#" + id).disabled = !online));
    $("#checkBtn").disabled = !online || state.busy;
  }
  async function checkApi() {
    if (!CFG.API_BASE) { setMode(false); return; }
    try {
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 2500);
      const r = await fetch(CFG.API_BASE + "/api/health", { signal: ctrl.signal });
      setMode(r.ok);
    } catch (e) { setMode(false); }
    if (state.api) newRound();
  }

  /* ---------- init ---------- */
  setTheme(); renderChips(); renderExamples(); applyI18n(); renderLevel(); fillFamily();
  state.practice.order = D.practice.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
  renderPractice(); route(true); checkApi();
})();
