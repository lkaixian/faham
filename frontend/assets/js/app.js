/* =========================================================
   FAHAM dashboard — app logic (vanilla JS, no build step)
   ========================================================= */
(function () {
  const D = window.FAHAM_DATA;
  const CFG = window.FAHAM_CONFIG || {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------- state (in memory, light persistence) ---------- */
  const store = {
    get(k, d) { try { const v = localStorage.getItem("faham_" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("faham_" + k, JSON.stringify(v)); } catch (e) {} }
  };
  const state = {
    view: "overview",
    lang: store.get("lang", "bm"),
    letter: "lhdn",
    learned: new Set(store.get("learned", [])),
    fresh: new Set(),
    cleared: new Set(store.get("cleared", [])),
    xp: store.get("xp", 0),
    todo: store.get("todo", []),
    running: false,
    ran: false,
    route: "online",
    api: false,
    custom: null,
    practice: { items: D.practice, order: [], i: 0, score: 0, answered: false, results: [] }
  };
  const CONSENT_V = 1;
  const consented = () => (store.get("consent", null) || {}).v === CONSENT_V;
  const syncRun = () => { $("#runBtn").disabled = state.running || !consented(); };
  const save = () => {
    store.set("lang", state.lang); store.set("learned", [...state.learned]);
    store.set("cleared", [...state.cleared]); store.set("xp", state.xp); store.set("todo", state.todo);
  };

  /* ---------- helpers ---------- */
  function toast(msg) {
    const t = $("#toast"); t.innerHTML = msg; t.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }
  function speak(text, lang) {
    if (!("speechSynthesis" in window)) { toast("Read-aloud isn't supported in this browser."); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = D.languages[lang].speech; u.rate = 0.95;
    const voices = speechSynthesis.getVoices();
    const v = voices.find((x) => x.lang && x.lang.toLowerCase().startsWith(u.lang.slice(0, 2).toLowerCase()));
    if (v) u.voice = v; else toast(`No ${D.languages[lang].name} voice on this device — using the default voice.`);
    speechSynthesis.speak(u);
  }
  const letterById = (id) => (id === "custom" && state.custom) || D.letters.find((l) => l.id === id);

  /* ---------- navigation ---------- */
  function go(view) {
    if (!$("#view-" + view)) return;
    state.view = view;
    $$(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + view));
    $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    const title = $("#view-" + view).dataset.title;
    $("#viewTitle").textContent = title; $("#crumb").textContent = "FAHAM / " + title;
    $("#sidebar").classList.remove("open");
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (view === "learn") renderGlossary();
    if (view === "family") renderFamily();
    try { history.replaceState(null, "", "#" + view); } catch (e) {}
  }
  $$("#nav button").forEach((b) => (b.onclick = () => go(b.dataset.view)));
  document.addEventListener("click", (e) => {
    const g = e.target.closest("[data-goto]");
    if (g) { e.preventDefault(); go(g.dataset.goto); }
  });
  $("#menuBtn").onclick = () => $("#sidebar").classList.toggle("open");

  /* ---------- glass spotlight on cards ---------- */
  document.addEventListener("pointermove", (e) => {
    const c = e.target.closest(".card"); if (!c) return;
    const r = c.getBoundingClientRect();
    c.style.setProperty("--mx", e.clientX - r.left + "px");
    c.style.setProperty("--my", e.clientY - r.top + "px");
  });

  /* ---------- language switch ---------- */
  function renderLang() {
    $("#langSwitch").innerHTML = Object.entries(D.languages)
      .map(([k, v]) => `<button data-l="${k}" class="${k === state.lang ? "active" : ""}" title="${v.name}">${v.label}</button>`).join("");
    $$("#langSwitch button").forEach((b) => (b.onclick = () => {
      state.lang = b.dataset.l; save(); renderLang();
      if (state.ran) renderExplain();
      if (state.ran && state.letter === "custom") { toast("Your own letter was explained in " + D.languages[state.custom.lang].name + ". Run again to get this language."); return; }
      toast(`Explanations now in <b>${D.languages[state.lang].name}</b>`);
    }));
  }

  /* ---------- countdown ---------- */
  function tick() {
    const ms = new Date(D.event.date) - new Date();
    const d = Math.max(0, Math.floor(ms / 864e5)), h = Math.max(0, Math.floor((ms % 864e5) / 36e5)), m = Math.max(0, Math.floor((ms % 36e5) / 6e4));
    $("#cdD").textContent = String(d).padStart(2, "0");
    $("#cdH").textContent = String(h).padStart(2, "0");
    $("#cdM").textContent = String(m).padStart(2, "0");
    $("#topDays").textContent = ms > 0 ? d : "0";
  }

  /* ---------- overview ---------- */
  function renderOverview() {
    $("#themeGrid").innerHTML = D.themeFit.map((t) => `<div class="theme-item"><div class="t">${t.t}</div><div class="d">${esc(t.d)}</div></div>`).join("");
    $("#personas").innerHTML = D.personas.map((p) => `<div class="persona"><div class="avatar">${p.e}</div><div><b>${esc(p.t)}</b><p>${esc(p.d)}</p></div></div>`).join("");

    // agent loop ring
    const steps = ["Read", "Verify", "Explain", "Teach", "Route", "Act"];
    const R = 100, C = 130;
    const pts = steps.map((s, i) => { const a = (i / steps.length) * Math.PI * 2 - Math.PI / 2; return { s, x: C + R * Math.cos(a), y: C + R * Math.sin(a) }; });
    $("#loop").innerHTML = `
      <svg viewBox="0 0 260 260">
        <defs><linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#5a3b8c"/><stop offset="1" stop-color="#c9c2e3"/></linearGradient></defs>
        <circle cx="${C}" cy="${C}" r="${R}" fill="none" stroke="rgba(201,194,227,.12)" stroke-width="1.5"/>
        <circle id="loopPath" cx="${C}" cy="${C}" r="${R}" fill="none" stroke="url(#lg)" stroke-width="2" stroke-dasharray="60 568" stroke-linecap="round">
          <animate attributeName="stroke-dashoffset" from="0" to="-628" dur="6s" repeatCount="indefinite"/>
        </circle>
        ${pts.map((p, i) => `<g class="lp" style="animation-delay:${i}s">
          <circle cx="${p.x}" cy="${p.y}" r="21" fill="#2a1e4d" stroke="rgba(201,194,227,.3)"/>
          <circle cx="${p.x}" cy="${p.y}" r="21" fill="none" stroke="#c9c2e3" stroke-width="2" opacity="0">
            <animate attributeName="opacity" values="0;1;0" dur="6s" begin="${i}s" repeatCount="indefinite"/>
          </circle>
          <text x="${p.x}" y="${p.y + 3.5}" text-anchor="middle" font-size="9.5" font-weight="600" fill="#ece9f7" font-family="Inter">${p.s}</text></g>`).join("")}
      </svg>
      <div class="center"><div><b>Human</b><span>approves every action</span></div></div>`;

    // illustrative sparkline
    const help = [92, 85, 74, 66, 55, 47, 40, 34];
    const used = [10, 18, 27, 38, 46, 58, 66, 78];
    const path = (arr, lift) => arr.map((v, i) => `${i ? "L" : "M"}${(i / (arr.length - 1)) * 400},${105 - v * 1.0 + lift}`).join(" ");
    $("#spark").innerHTML = `
      <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9c2e3" stop-opacity=".35"/><stop offset="1" stop-color="#c9c2e3" stop-opacity="0"/></linearGradient></defs>
      <path d="${path(help, 0)} L400,110 L0,110 Z" fill="url(#sg)"/>
      <path d="${path(help, 0)}" fill="none" stroke="#c9c2e3" stroke-width="2.5" stroke-linecap="round" class="draw"/>
      <path d="${path(used, 0)}" fill="none" stroke="#8b7cc7" stroke-width="2" stroke-dasharray="5 5" opacity=".8"/>`;
  }
  function countUp() {
    $$("[data-count]").forEach((el) => {
      const target = +el.dataset.count;
      const small = el.querySelector("small");
      const unit = small ? small.outerHTML : "";
      let n = 0;
      const step = () => { el.innerHTML = ++n + unit; if (n < target) setTimeout(step, 140); };
      el.innerHTML = "0" + unit; setTimeout(step, 200);
    });
  }

  /* ---------- live agent ---------- */
  const STEPS = [
    { k: "Read", d: "OCR + fields", i: '<path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h5"/>' },
    { k: "Verify", d: "Scam check", i: '<path d="M12 2 4 5v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V5l-8-3z"/>' },
    { k: "Explain", d: "Your language", i: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' },
    { k: "Teach", d: "Lesson card", i: '<path d="M12 3 2 8l10 5 10-5-10-5z"/>' },
    { k: "Route", d: "Online / walk-in", i: '<path d="M3 12h18M12 3l9 9-9 9"/>' },
    { k: "Act", d: "Draft + remind", i: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>' }
  ];

  function renderPicker() {
    $("#letterPicker").innerHTML = D.letters.map((l) => `
      <button class="letter-opt ${l.id === state.letter ? "active" : ""}" data-id="${l.id}">
        <span class="lo-ic">${l.icon}</span><span><b>${esc(l.short)}</b><span>${esc(l.kind)}${state.cleared.has(l.id) ? " · ✓ cleared" : ""}</span></span>
      </button>`).join("");
    $$(".letter-opt").forEach((b) => (b.onclick = () => {
      if (state.running) return;
      state.letter = b.dataset.id; state.ran = false; clearInput();
      renderPicker(); renderLetter(); resetPipeline();
      $("#results").classList.add("empty");
      $("#console").innerHTML = `<div class="ln"><span class="t">[idle]</span> Letter loaded: ${esc(letterById(state.letter).title)}. Press Run agent.<span class="cursor"></span></div>`;
    }));
  }

  function renderLetter(redacted) {
    const l = letterById(state.letter);
    if (l.id === "custom") {
      $("#letterDoc").innerHTML = `<div class="lh"><div><b>Your letter</b><br/><span>${l.redacted ? "Redacted text" : "Text as entered"}</span></div></div><p style="white-space:pre-wrap">${esc(l.text)}</p>`;
      return;
    }
    const to = redacted ? `<span class="redact">${esc(l.to)}</span>` : esc(l.to);
    $("#letterDoc").innerHTML = `
      <div class="wm">SAMPEL · FIKTIF</div>
      <div class="lh"><div><b>${esc(l.issuer)}</b><br/><span>${esc(l.issuerShort)}</span></div><span>Ruj: ${esc(l.ref)}<br/>${esc(l.date)}</span></div>
      <div style="font-family:var(--font);font-size:11.5px;margin-bottom:6px">Kepada: ${to}</div>
      <h4>${esc(l.title)}</h4>
      ${l.body.map((p) => `<p style="margin-bottom:8px">${p}</p>`).join("")}`;
  }

  function resetPipeline() {
    $("#pipeline").innerHTML = STEPS.map((s, i) => `
      <div class="step" id="st${i}"><div class="si"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">${s.i}</svg></div><b>${s.k}</b><span>${s.d}</span></div>`).join("");
  }

  function localTrace(l) {
    const lang = D.languages[state.lang].name;
    const T = [];
    T.push({ s: 0, k: "think", m: "Goal: help the user understand this letter, confirm it is real, and decide the next action." });
    T.push({ s: 0, k: "tool", t: "ocr.read", m: `image → text · ${l.body.join(" ").replace(/<[^>]+>/g, "").split(/\s+/).length + 40} words · layout: letterhead, body, footer` });
    T.push({ s: 0, k: "tool", t: "privacy.redact", m: "masked: name ×1, address ×1, IC ×0 — model only sees redacted text", fx: "redact" });
    T.push({ s: 0, k: "tool", t: "classify.issuer", m: `issuer = ${l.fields.Issuer} · type = ${l.fields.Type}` });
    T.push({ s: 0, k: "tool", t: "extract.fields", m: `amount = ${l.fields.Amount} · deadline = ${l.fields.Deadline} · ref = ${l.fields.Reference}` });
    T.push({ s: 1, k: "think", m: "Before explaining anything, I must check this is not a scam." });
    T.push({ s: 1, k: "tool", t: "scam.check", m: "domain allowlist · red-flag rules · reference pattern · LLM judge" });
    l.scam.checks.forEach((c) => { const bad = c.startsWith("x|"); T.push({ s: 1, k: bad ? "bad" : "ok", m: (bad ? "✗ " : "✓ ") + c.replace("x|", "") }); });
    T.push({ s: 1, k: l.scam.genuine ? "ok" : "bad", m: l.scam.genuine ? `verdict: LIKELY GENUINE (${l.scam.score}/100)` : `verdict: LIKELY SCAM (${l.scam.score}/100) → switch plan: protect the user, do not pay`, flag: !l.scam.genuine });
    T.push({ s: 2, k: "think", m: `Explaining in ${lang}, short sentences, no jargon, amount + deadline first.` });
    T.push({ s: 2, k: "tool", t: "llm.explain", m: `plain-language explanation ready (${lang})` });
    T.push({ s: 3, k: "tool", t: "teach.lesson", m: `lesson card "Kenapa?" + ${l.terms.length} Kamus Surat terms: ${l.terms.join(", ")}` });
    T.push({ s: 4, k: "think", m: l.scam.genuine ? "Online is fastest if the user has online banking; prepare walk-in as backup." : "Route = verify through official channels and report. Never use the link in the message." });
    T.push({ s: 4, k: "tool", t: "gov.retrieve", m: `steps fetched from ${l.route.source} · confidence ${l.route.confidence}` });
    T.push({ s: 4, k: "tool", t: "office.locate", m: "nearest office from postcode · hours + booking/queue info (demo data)" });
    T.push({ s: 5, k: "tool", t: "act.draft", m: l.scam.genuine ? "reply draft prepared · reminder proposed" : "scam report draft prepared for NSRC / police" });
    T.push({ s: 5, k: "warn", m: "⏸ waiting for user approval — nothing is sent or paid automatically" });
    return T;
  }

  const STAGE = { read: 0, verify: 1, explain: 2, teach: 3, route: 4, act: 5 };
  const mapTrace = (tr) => tr.map((t) => ({ s: STAGE[t.stage] ?? 0, k: t.kind, t: t.tool, m: t.message, flag: t.flag, fx: t.tool === "privacy.redact" ? "redact" : undefined }));

  /* ---------- own letter (paste or upload), API only ---------- */
  const MAX_IMG = 4 * 1024 * 1024;
  function inputMsg(html, busy) {
    const m = $("#inputMsg"); m.innerHTML = html || ""; m.className = "input-msg" + (html ? " show" : "") + (busy ? " busy" : "");
  }
  function clearInput() { $("#pasteBox").value = ""; $("#fileBox").value = ""; inputMsg(""); }
  function renderInput() {
    const off = !state.api;
    $("#ownInput").classList.toggle("offline", off);
    $("#pasteBox").disabled = off; $("#fileBox").disabled = off; $("#clearInput").disabled = off;
    $("#pasteBox").title = off ? "Needs the API" : "";
  }
  $("#pasteBox").oninput = () => { if ($("#pasteBox").value) $("#fileBox").value = ""; inputMsg(""); };
  $("#fileBox").onchange = () => {
    const f = $("#fileBox").files[0]; inputMsg("");
    if (!f) return;
    if (!/^image\/(png|jpeg)$/.test(f.type)) { $("#fileBox").value = ""; inputMsg("Only PNG or JPEG images are accepted. You can paste the letter text instead."); return; }
    if (f.size > MAX_IMG) { $("#fileBox").value = ""; inputMsg("That image is over 4 MB. Use a smaller photo or paste the letter text instead."); return; }
    $("#pasteBox").value = "";
  };
  $("#clearInput").onclick = clearInput;
  const readB64 = (f) => new Promise((ok, no) => {
    const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1]); r.onerror = () => no(r.error); r.readAsDataURL(f);
  });
  // what the user entered, or null when a sample letter should run
  function ownInput() {
    if (!state.api) return null;
    const text = $("#pasteBox").value.trim(), file = $("#fileBox").files[0];
    return text ? { text } : file ? { file } : null;
  }
  // POST own text/image. Returns {data} or {error}. A 422 detail is shown with a paste hint.
  async function analyzeOwn(inp) {
    try {
      const body = { language: state.lang };
      if (inp.text) body.text = inp.text; else body.image_b64 = await readB64(inp.file);
      const ctrl = new AbortController(); const to = setTimeout(() => ctrl.abort(), 30000);
      const res = await fetch(CFG.API_BASE + "/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, signal: ctrl.signal, body: JSON.stringify(body) });
      clearTimeout(to);
      if (res.status === 422) {
        const d = await res.json().catch(() => ({}));
        return { error: (typeof d.detail === "string" ? d.detail : "The API could not read this input.") + " Try pasting the letter text instead." };
      }
      if (!res.ok) return { error: "The API returned an error (" + res.status + "). Try again, or use a sample letter." };
      return { data: await res.json() };
    } catch (e) { return { error: "Could not reach the API. Check your connection or use a sample letter." }; }
  }
  // map the API response to the bundled-sample shape so the existing renderers work
  function mapApi(d) {
    const f = d.fields, s = d.scam, r = d.route, lang = state.lang;
    return {
      id: "custom", lang, text: d.redacted_text, redacted: true, title: "Your letter",
      fields: { Issuer: f.issuer, Type: f.letter_type, Amount: f.amount || "Not found", Deadline: f.deadline || "Not found", Reference: f.reference || "Not found" },
      scam: { genuine: s.genuine, score: s.score, checks: [...s.good_signs, ...s.red_flags.map((x) => "x|" + x)] },
      explain: { [lang]: d.explanation.split(/\n+/).filter(Boolean) },
      terms: d.lesson.terms.filter((t) => D.glossary[t]),
      kenapa: { q: d.lesson.question, a: d.lesson.answer, rule: d.disclaimer },
      route: { source: r.source_url + " (" + r.retrieved_at + ")", confidence: r.confidence,
        online: { steps: r.online_steps, prepare: r.prepare_online }, walkin: { steps: r.walkin_steps, prepare: r.prepare_walkin } },
      reminder: d.action.reminder || "No reminder suggested", draft: d.action.draft
    };
  }

  async function fetchServerTrace(l) {
    if (!state.api) return null;
    try {
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 6000);
      const res = await fetch(CFG.API_BASE + "/api/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: ctrl.signal,
        body: JSON.stringify({ text: [l.title, "Rujukan: " + l.ref, "Daripada: " + l.issuer + " " + l.issuerShort, "Kepada: " + l.to, ...l.body.map((b) => b.replace(/<[^>]+>/g, ""))].join("\n"), language: state.lang, sample_id: l.id })
      });
      if (!res.ok) return null;
      const data = await res.json();
      state.serverScore = data.scam.score;
      return mapTrace(data.trace);
    } catch (e) { return null; }
  }

  async function runAgent() {
    if (state.running) return;
    if (!consented()) { go("agent"); toast("Tick “Saya faham / I understand” first."); $("#consentBox").focus(); return; }
    state.running = true; state.ran = false;
    const inp = ownInput();
    $("#results").classList.add("empty");
    resetPipeline();
    const con = $("#console"); con.innerHTML = "";
    state.serverScore = null;
    let trace;
    if (inp) {
      // loading state, then error state or the mapped result
      syncRun(); inputMsg("Sending to the agent API. Reading a photo can take a few seconds.", true);
      con.innerHTML = `<div class="ln"><span class="t">[wait]</span> Waiting for the API...<span class="cursor"></span></div>`;
      const r = await analyzeOwn(inp);
      if (r.error) {
        inputMsg(esc(r.error)); con.innerHTML = `<div class="ln"><span class="bad">${esc(r.error)}</span></div>`;
        state.running = false; syncRun(); return;
      }
      inputMsg("");
      state.custom = mapApi(r.data); state.letter = "custom"; state.serverScore = r.data.scam.score;
      renderPicker(); con.innerHTML = ""; trace = mapTrace(r.data.trace);
    }
    const l = letterById(state.letter);
    syncRun(); renderLetter();
    $("#letterDoc").classList.add("scanning");
    trace = trace || (await fetchServerTrace(l)) || localTrace(l);
    const t0 = performance.now();
    let cur = -1;
    for (const line of trace) {
      if (line.s !== cur) {
        if (cur >= 0) $("#st" + cur).className = "step done";
        cur = line.s; $("#st" + cur).className = "step running";
        if (cur === 1) $("#letterDoc").classList.remove("scanning");
      }
      if (line.fx === "redact") renderLetter(true);
      if (line.flag) $("#st1").classList.add("flag");
      const ts = ((performance.now() - t0) / 1000).toFixed(2).padStart(5, "0");
      const cls = { think: "th", tool: "tool", ok: "ok", bad: "bad", warn: "warn" }[line.k] || "";
      const label = line.k === "think" ? "think" : line.k === "tool" ? "call " + line.t : "  ";
      const div = document.createElement("div"); div.className = "ln";
      div.innerHTML = `<span class="t">[${ts}s]</span> <span class="${cls}">${esc(label)}</span>${line.k === "tool" ? " → " : " "}<span class="${line.k === "tool" ? "" : cls}">${esc(line.m)}</span>`;
      con.appendChild(div); con.scrollTop = con.scrollHeight;
      await sleep(line.k === "think" ? 650 : 360);
    }
    $("#st" + cur).className = "step done" + (cur === 1 && !l.scam.genuine ? " flag" : "");
    if (!l.scam.genuine) $("#st1").classList.add("flag");
    $("#letterDoc").classList.remove("scanning");
    con.insertAdjacentHTML("beforeend", `<div class="ln"><span class="ok">✓ plan complete</span> — see the results below<span class="cursor"></span></div>`);
    con.scrollTop = con.scrollHeight;

    // learning effects
    const newTerms = l.terms.filter((t) => !state.learned.has(t));
    newTerms.forEach((t) => { state.learned.add(t); state.fresh.add(t); });
    if (l.id !== "custom" && !state.cleared.has(l.id)) { state.cleared.add(l.id); addXP(20, "Letter cleared"); }
    save(); updateGlossCount(); renderPicker();
    if (newTerms.length) setTimeout(() => toast(`📘 +${newTerms.length} new in <b>Kamus Surat</b>: ${newTerms.join(", ")}`), 600);

    state.ran = true; state.running = false; syncRun();
    renderResults();
    $("#results").classList.remove("empty");
    setTimeout(() => $("#results").scrollIntoView({ behavior: "smooth", block: "start" }), 250);
  }
  $("#runBtn").onclick = runAgent;

  function renderResults() {
    const l = letterById(state.letter);
    $("#fields").innerHTML = Object.entries(l.fields).map(([k, v]) => `<div class="field"><span>${k}</span><b>${esc(v)}</b></div>`).join("");

    const ok = l.scam.genuine, score = state.serverScore ?? l.scam.score, circ = 2 * Math.PI * 40;
    $("#verdict").innerHTML = `
      <div class="verdict ${ok ? "ok" : "bad"}">
        <div class="gauge"><svg width="96" height="96"><circle cx="48" cy="48" r="40" stroke="rgba(201,194,227,.12)" stroke-width="8" fill="none"/>
          <circle cx="48" cy="48" r="40" stroke="${ok ? "#7fd1b9" : "#f08a9b"}" stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ}" id="gArc"/></svg>
          <div class="gv">${score}</div></div>
        <div><h4>${ok ? "Likely genuine" : "Likely SCAM — do not pay"}</h4><div class="small muted">Authenticity score out of 100 · ${ok ? "safe to follow official steps" : "agent switched to protect-and-report plan"}</div></div>
      </div>
      <ul class="checks">${l.scam.checks.map((c) => `<li class="${c.startsWith("x|") ? "x" : ""}">${esc(c.replace("x|", ""))}</li>`).join("")}</ul>`;
    requestAnimationFrame(() => setTimeout(() => { const a = $("#gArc"); if (a) { a.style.transition = "stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1)"; a.style.strokeDashoffset = circ * (1 - score / 100); } }, 50));

    renderExplain();

    $("#kenapa").innerHTML = `
      <span class="eyebrow">4 · Teach — 60-second lesson</span>
      <h3>${esc(l.kenapa.q)}</h3>
      <p class="explain-text" style="font-size:14px">${esc(l.kenapa.a)}</p>
      <div class="rule">📌 ${esc(l.kenapa.rule)}</div>
      <div class="prep" style="margin-top:14px">${l.terms.map((t) => `<span>📘 ${esc(t)}</span>`).join("")}</div>
      <button class="btn btn-ghost btn-sm" style="margin-top:14px" data-goto="learn">Open Kamus Surat →</button>`;

    renderRoute();
    $("#reminder").innerHTML = `⏰ Reminder proposed: <b style="color:#fff">${esc(l.reminder)}</b>`;
    $("#draft").textContent = l.draft;
    $("#approveRow").innerHTML = `
      <button class="btn btn-primary btn-sm" id="approveBtn">✓ Approve ${ok ? "draft & reminder" : "report draft"}</button>
      <button class="btn btn-ghost btn-sm" id="copyBtn">Copy</button>
      <span class="small muted">The agent never sends or pays on its own.</span>`;
    $("#approveBtn").onclick = () => { $("#approveRow").innerHTML = `<span class="approved">✓ Approved by you · ${new Date().toLocaleTimeString()} — saved to your reminders</span>`; toast("✓ Approved. FAHAM will remind you before the deadline."); };
    $("#copyBtn").onclick = () => { navigator.clipboard?.writeText(l.draft).then(() => toast("Draft copied")); };
  }

  function renderExplain() {
    const l = letterById(state.letter);
    $("#explain").innerHTML = (l.explain[state.lang] || l.explain[l.lang]).map((p) => `<p>${esc(p)}</p>`).join("") + `
      <div class="facts">
        <div class="fact"><span>From</span><b>${esc(l.fields.Issuer)}</b></div>
        <div class="fact"><span>How much</span><b>${esc(l.fields.Amount)}</b></div>
        <div class="fact"><span>By when</span><b>${esc(l.fields.Deadline)}</b></div>
        <div class="fact ${l.scam.genuine ? "good" : "bad"}"><span>Real?</span><b>${l.scam.genuine ? "Yes ✓" : "Scam ✗"}</b></div>
      </div>`;
    $("#explainLang").textContent = D.languages[l.explain[state.lang] ? state.lang : l.lang].name;
  }
  $("#speakBtn").onclick = () => { const l = letterById(state.letter), k = l.explain[state.lang] ? state.lang : l.lang; speak(l.explain[k].join(" "), k); };

  function renderRoute() {
    const l = letterById(state.letter), r = l.route[state.route];
    $$("#routeTabs button").forEach((b) => b.classList.toggle("active", b.dataset.r === state.route));
    $("#route").innerHTML = `
      <ol class="steps-list">${r.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
      <div class="small muted" style="margin-top:14px">Prepare:</div>
      <div class="prep" style="margin-top:6px">${r.prepare.map((p) => `<span>${esc(p)}</span>`).join("")}</div>
      <div class="source">Source: <b style="color:#fff">${esc(l.route.source)}</b> · retrieved at time of use <span class="conf">confidence: ${l.route.confidence}</span></div>`;
  }
  $$("#routeTabs button").forEach((b) => (b.onclick = () => { state.route = b.dataset.r; renderRoute(); }));

  /* ---------- glossary ---------- */
  function updateGlossCount() { $("#glossCount").textContent = state.learned.size; }
  function renderGlossary() {
    const q = ($("#glossSearch").value || "").toLowerCase();
    const all = Object.entries(D.glossary);
    const list = all.filter(([k, v]) => !q || k.toLowerCase().includes(q) || v.def.toLowerCase().includes(q))
      .sort((a, b) => (state.learned.has(b[0]) - state.learned.has(a[0])));
    $("#glossGrid").innerHTML = list.map(([k, v]) => {
      const on = state.learned.has(k);
      return `<div class="card term ${on ? "" : "locked"}">${state.fresh.has(k) ? '<span class="new">NEW</span>' : ""}
        <div class="src">${esc(v.src)}</div><div class="tw">${esc(k)}</div><p>${on ? esc(v.def) : "Run a letter that contains this term to unlock it."}</p></div>`;
    }).join("") || `<p class="muted">No terms match “${esc(q)}”.</p>`;
    $("#gLearned").textContent = state.learned.size;
    $("#gTotal").textContent = all.length;
    $("#gBar").style.width = (state.learned.size / all.length) * 100 + "%";
  }
  $("#glossSearch").oninput = renderGlossary;

  /* ---------- XP / levels ---------- */
  function levelFor(xp) { let l = D.levels[0]; for (const x of D.levels) if (xp >= x.min) l = x; return l; }
  function addXP(n, why) {
    const before = levelFor(state.xp);
    state.xp += n; save();
    const after = levelFor(state.xp);
    renderLevel();
    if (after.name !== before.name) {
      setTimeout(() => {
        $("#lmEmoji").textContent = after.emoji; $("#lmTitle").textContent = "Level up — " + after.name;
        $("#lmText").textContent = `${why}. You're getting better at reading official letters on your own.`;
        $("#levelModal").classList.add("show"); confetti();
      }, 500);
    }
  }
  $("#lmClose").onclick = () => $("#levelModal").classList.remove("show");
  function renderLevel() {
    const cur = levelFor(state.xp), idx = D.levels.indexOf(cur), next = D.levels[idx + 1];
    $("#lvlName").textContent = `${cur.emoji} ${cur.name}`;
    const pct = next ? ((state.xp - cur.min) / (next.min - cur.min)) * 100 : 100;
    $("#lvlBar").style.width = pct + "%";
    $("#lvlNext").textContent = next ? `${state.xp} XP · ${next.min - state.xp} XP to ${next.emoji} ${next.name}` : `${state.xp} XP · top level reached`;
  }

  /* ---------- practice ---------- */
  async function newRound() {
    const my = (newRound.n = (newRound.n || 0) + 1);
    let items = D.practice;
    if (state.api) {
      $("#pCard").textContent = "Loading messages from the agent..."; $("#pChoices").style.display = "none"; $("#pFeedback").className = "feedback";
      try {
        const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 6000);
        const res = await fetch(CFG.API_BASE + "/api/practice?n=6", { signal: ctrl.signal });
        if (!res.ok) throw new Error(res.status);
        const got = await res.json();
        if (!got.length) throw new Error("empty");
        items = got.map((x) => ({ from: x.sender, kind: x.channel, text: x.text, scam: x.is_scam, clues: x.clues, agent: x.agent }));
      } catch (e) { toast("Could not load messages from the API. Using the bundled ones."); }
      if (my !== newRound.n) return;
    }
    const idx = items.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, 6);
    state.practice = { items, order: idx, i: 0, score: 0, answered: false, results: [] };
    renderPractice();
  }
  function renderPractice() {
    const p = state.practice;
    if (p.i >= p.order.length) {
      $("#pCard").innerHTML = `<div style="text-align:center;padding:30px 10px"><div style="font-size:44px">🎉</div><h3 style="font-family:var(--display);font-size:22px;margin:8px 0">Round complete: ${p.score} / ${p.order.length}</h3><p>${p.score >= 5 ? "Excellent — you spot scams like a pro." : p.score >= 3 ? "Good! Review the clues and try again." : "Scammers are tricky. Try another round — the clues will stick."}</p></div>`;
      $("#pChoices").style.display = "none"; $("#pFeedback").className = "feedback";
      $("#pCount").textContent = "Done";
    } else {
      const it = p.items[p.order[p.i]];
      $("#pCard").innerHTML = `<div class="from"><span>From: <b>${esc(it.from)}</b></span><span class="kind">${esc(it.kind)} · FICTIONAL</span></div>${esc(it.text)}`;
      $("#pChoices").style.display = "flex"; $("#pFeedback").className = "feedback";
      $("#pCount").textContent = `Message ${p.i + 1} of ${p.order.length}`;
      p.answered = false;
    }
    $("#pScore").textContent = `${p.score} / ${p.results.length}`;
    $("#pDots").innerHTML = p.order.map((_, i) => `<i class="${p.results[i] === true ? "r" : p.results[i] === false ? "w" : i === p.i ? "c" : ""}"></i>`).join("");
  }
  function agentLine(a) {
    if (!a) return "";
    const list = (x) => (x && x.length ? x.map(esc).join("; ") : "none");
    return `<div class="small" style="margin-top:10px"><b>Agent verdict:</b> ${a.genuine ? "likely genuine" : "likely scam"}, score ${esc(a.score)}, flags: ${list(a.red_flags)}${a.good_signs && a.good_signs.length ? ", good signs: " + list(a.good_signs) : ""}</div>`;
  }
  $$("#pChoices .choice").forEach((b) => (b.onclick = () => {
    const p = state.practice; if (p.answered) return; p.answered = true;
    const it = p.items[p.order[p.i]];
    const right = (b.dataset.a === "scam") === it.scam;
    p.results.push(right); if (right) { p.score++; addXP(10, "Correct answer"); }
    const fb = $("#pFeedback");
    fb.className = "feedback show " + (right ? "right" : "wrong");
    fb.innerHTML = `<h4>${right ? "✓ Correct!" : "✗ Not quite."} This is ${it.scam ? "a SCAM" : "REAL"}.</h4>
      <div class="small">Clues the agent looks for:</div>
      <ul class="checks">${it.clues.map((c) => `<li class="${it.scam ? "x" : ""}">${esc(c)}</li>`).join("")}</ul>${agentLine(it.agent)}
      <button class="btn btn-primary btn-sm" style="margin-top:12px" id="pNext">Next →</button>`;
    $("#pChoices").style.display = "none";
    $("#pNext").onclick = () => { p.i++; renderPractice(); };
    $("#pNext").focus();
    $("#pScore").textContent = `${p.score} / ${p.results.length}`;
    $("#pDots").innerHTML = p.order.map((_, i) => `<i class="${p.results[i] === true ? "r" : p.results[i] === false ? "w" : ""}"></i>`).join("");
  }));
  $("#pRestart").onclick = newRound;

  /* ---------- family mode ---------- */
  function fillSelects() {
    $("#fLetter").innerHTML = D.letters.map((l) => `<option value="${l.id}">${l.icon} ${l.short} — ${l.kind}</option>`).join("");
    const opts = Object.entries(D.languages).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join("");
    $("#fChild").innerHTML = opts; $("#fParent").innerHTML = opts;
    $("#fChild").value = "en"; $("#fParent").value = "bm";
    ["fLetter", "fChild", "fParent"].forEach((id) => ($("#" + id).onchange = renderFamily));
  }
  function renderFamily() {
    const l = letterById($("#fLetter").value), c = $("#fChild").value, p = $("#fParent").value;
    $("#fChildLbl").textContent = D.languages[c].name; $("#fParentLbl").textContent = D.languages[p].name;
    $("#fChildText").innerHTML = `<div class="small muted" style="margin-bottom:8px">${esc(l.title)}</div>` + l.explain[c].map((x) => `<p>${esc(x)}</p>`).join("");
    $("#fBubble").innerHTML = `<b>${l.icon} ${esc(l.short)}</b><br/>` + l.explain[p].map((x) => esc(x)).join("<br/><br/>");
  }
  $("#fSpeak").onclick = () => { const l = letterById($("#fLetter").value), p = $("#fParent").value; speak(l.explain[p].join(" "), p); };
  $("#fSend").onclick = () => toast("✓ Approved — explanation sent to Mak/Ayah (demo, nothing actually sent)");

  /* ---------- architecture ---------- */
  function renderArch() {
    const layers = [
      { l: "Client", s: "PWA · browser", n: [["Camera / PDF scan", "capture"], ["Dashboard UI", "this site"], ["Read-aloud", "Web Speech"], ["Family share", "approve → send"]] },
      { l: "API", s: "FastAPI", n: [["POST /api/analyze", "full agent run"], ["GET /api/practice", "scam round"], ["GET /api/tools", "tool registry"], ["GET /api/health", "status"]] },
      { l: "Agent core", s: "orchestrator", n: [["Planner", "decides next tool"], ["Agent state", "fields · verdict · plan"], ["Reasoning trace", "shown to user"], ["Approval gate", "human-in-the-loop"]] },
      { l: "Tools", s: "typed registry", n: D.tools.map((t) => [t.name, t.d, t.id]) },
      { l: "Knowledge", s: "grounding", n: [["Official source registry", ".gov.my URLs"], ["Office directory", "hours · booking"], ["LLM provider", "pluggable / offline"], ["No letter storage", "session only"]] }
    ];
    $("#arch").innerHTML = layers.map((ly, i) => `
      ${i ? '<div class="connector"></div>' : ""}
      <div class="layer"><div class="layer-label"><b>${ly.l}</b><span>${ly.s}</span></div>
      <div class="layer-items ${ly.n.length === 8 ? "cols-4" : ""}">${ly.n.map((n) => `<div class="node"><b>${esc(n[0])}</b><span>${esc(n[1])}</span>${n[2] ? `<br/><code>${n[2]}</code>` : ""}</div>`).join("")}</div></div>`).join("");
  }

  /* ---------- trust ---------- */
  function renderTrust() {
    $("#risks").innerHTML = D.risks.map((r) => `
      <div class="card span-6 risk"><span class="eyebrow">${esc(r.r)}</span><div class="q">“${esc(r.q)}”</div><div class="m">${esc(r.m)}</div></div>`).join("");
  }

  /* ---------- plan ---------- */
  function renderPlan() {
    const total = D.video.reduce((a, v) => a + v.s, 0);
    const shades = ["#2a1e4d", "#3a2a63", "#4a3277", "#5a3b8c", "#7462ad", "#8b7cc7"];
    $("#timeline").innerHTML = D.video.map((v, i) => `<div data-i="${i}" style="flex:${v.s / total};background:${shades[i]}"><b>${esc(v.name)}</b><span>${v.t}–${v.e}</span></div>`).join("");
    const show = (i) => { const v = D.video[i]; $("#sceneDetail").innerHTML = `<b style="color:#fff">${v.t}–${v.e} · ${esc(v.name)}</b> — ${esc(v.shows)}`; };
    $$("#timeline div").forEach((d) => (d.onclick = () => show(+d.dataset.i))); show(0);

    const renderTodo = () => {
      $("#todo").innerHTML = D.nextSteps.map((s, i) => `<li><label><input type="checkbox" data-i="${i}" ${state.todo.includes(i) ? "checked" : ""}/><span>${esc(s)}</span></label></li>`).join("");
      $("#todoProg").textContent = `${state.todo.length} / ${D.nextSteps.length} done`;
      $("#todoBar").style.width = (state.todo.length / D.nextSteps.length) * 100 + "%";
      $$("#todo input").forEach((c) => (c.onchange = () => {
        const i = +c.dataset.i; state.todo = c.checked ? [...new Set([...state.todo, i])] : state.todo.filter((x) => x !== i); save(); renderTodo();
      }));
    };
    renderTodo();
    $("#team").innerHTML = D.team.map((m) => `<div class="member"><div class="avatar">${esc(m.n.split(" ").map((x) => x[0]).slice(0, 2).join(""))}</div><b>${esc(m.n)}</b><span>${esc(m.r)}</span></div>`).join("");
    $("#pitchLine").textContent = "“" + D.event.pitch + "”";
  }

  /* ---------- confetti ---------- */
  function confetti() {
    const c = $("#confetti"), x = c.getContext("2d");
    c.width = innerWidth; c.height = innerHeight;
    const cols = ["#c9c2e3", "#8b7cc7", "#5a3b8c", "#ffffff", "#7fd1b9"];
    const ps = Array.from({ length: 140 }, () => ({ x: innerWidth / 2, y: innerHeight / 2.4, vx: (Math.random() - 0.5) * 14, vy: Math.random() * -12 - 3, r: Math.random() * 5 + 3, c: cols[(Math.random() * cols.length) | 0], a: Math.random() * 6 }));
    let f = 0;
    (function loop() {
      x.clearRect(0, 0, c.width, c.height);
      ps.forEach((p) => { p.vy += 0.35; p.x += p.vx; p.y += p.vy; p.a += 0.2; x.save(); x.translate(p.x, p.y); x.rotate(p.a); x.fillStyle = p.c; x.fillRect(-p.r / 2, -p.r / 4, p.r, p.r / 2); x.restore(); });
      if (++f < 150) requestAnimationFrame(loop); else x.clearRect(0, 0, c.width, c.height);
    })();
  }

  /* ---------- API health ---------- */
  async function checkApi() {
    if (!CFG.API_BASE) return;
    try {
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 1500);
      const r = await fetch(CFG.API_BASE + "/api/health", { signal: ctrl.signal });
      if (r.ok) {
        state.api = true;
        $("#apiDot").classList.remove("demo"); $("#apiText").textContent = "Agent API online";
        $("#apiSub").textContent = CFG.API_BASE.replace(/^https?:\/\//, "");
        renderInput();
        if (!state.practice.results.length) newRound();
      }
    } catch (e) { /* stay in demo mode */ }
  }

  /* ---------- consent and clear my data ---------- */
  $("#consentBox").checked = consented();
  $("#consentBox").onchange = (e) => {
    if (e.target.checked) store.set("consent", { v: CONSENT_V }); else { try { localStorage.removeItem("faham_consent"); } catch (x) {} }
    syncRun();
  };
  $("#clearData").onclick = () => {
    if (state.running) { toast("Wait for the agent to finish, then clear your data."); return; }
    try { Object.keys(localStorage).filter((k) => k.startsWith("faham_")).forEach((k) => localStorage.removeItem(k)); } catch (e) {}
    Object.assign(state, { lang: "bm", letter: "lhdn", learned: new Set(), fresh: new Set(), cleared: new Set(), xp: 0, todo: [], ran: false, custom: null, route: "online" });
    $("#consentBox").checked = false; clearInput(); syncRun();
    renderLang(); renderPicker(); renderLetter(); resetPipeline(); renderLevel(); updateGlossCount(); renderGlossary(); renderPlan(); newRound();
    $("#results").classList.add("empty");
    $("#console").innerHTML = `<div class="ln"><span class="t">[idle]</span> Data cleared. Choose a letter and press Run agent.<span class="cursor"></span></div>`;
    toast("Your data on this device was cleared.");
  };

  /* ---------- init ---------- */
  renderLang(); renderOverview(); renderPicker(); renderLetter(); resetPipeline();
  renderLevel(); updateGlossCount(); renderInput(); syncRun(); fillSelects(); renderArch(); renderTrust(); renderPlan(); newRound();
  tick(); setInterval(tick, 30000); checkApi();

  window.addEventListener("faham:enter", (e) => {
    const hash = (location.hash || "").slice(1);
    const target = e.detail.goto || (hash && $("#view-" + hash) ? hash : null);
    if (target) go(target);
    countUp();
    if (e.detail.goto === "agent") setTimeout(runAgent, 700);
  });
})();
