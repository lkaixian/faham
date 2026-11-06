/* FAHAM — "Welcome to FAHAM" AI intro animation */
(function () {
  const intro = document.getElementById("intro");
  const canvas = document.getElementById("neural");
  const ctx = canvas.getContext("2d");
  let W, H, nodes = [], raf, mouse = { x: -999, y: -999 };
  const DPR = Math.min(window.devicePixelRatio || 1, 2);

  function resize() {
    W = canvas.width = innerWidth * DPR;
    H = canvas.height = innerHeight * DPR;
    canvas.style.width = innerWidth + "px";
    canvas.style.height = innerHeight + "px";
    const count = Math.min(110, Math.floor((innerWidth * innerHeight) / 14000));
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.35 * DPR, vy: (Math.random() - 0.5) * 0.35 * DPR,
      r: (Math.random() * 1.6 + 0.6) * DPR, p: Math.random() * Math.PI * 2
    }));
  }

  // Signal pulses that travel along links — "the agent thinking"
  const pulses = [];
  function spawnPulse() {
    if (nodes.length < 2) return;
    const a = nodes[(Math.random() * nodes.length) | 0];
    let best = null, bd = 1e9;
    for (const b of nodes) {
      if (b === a) continue;
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (d < bd && d > 20 * DPR) { bd = d; best = b; }
    }
    if (best && bd < 160 * DPR) pulses.push({ a, b: best, t: 0 });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const cx = W / 2, cy = H / 2.3;
    const link = 140 * DPR;
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy; n.p += 0.03;
      // gentle pull toward the AI core
      n.vx += (cx - n.x) * 0.0000025; n.vy += (cy - n.y) * 0.0000025;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
      const md = Math.hypot(n.x - mouse.x * DPR, n.y - mouse.y * DPR);
      if (md < 120 * DPR) { n.x += (n.x - mouse.x * DPR) * 0.01; n.y += (n.y - mouse.y * DPR) * 0.01; }
    }
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < link) {
          ctx.strokeStyle = `rgba(139,124,199,${(1 - d / link) * 0.32})`;
          ctx.lineWidth = DPR * 0.7;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    for (const n of nodes) {
      const g = 0.55 + Math.sin(n.p) * 0.35;
      ctx.fillStyle = `rgba(201,194,227,${g})`;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill();
    }
    if (Math.random() < 0.25) spawnPulse();
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i]; p.t += 0.03;
      if (p.t >= 1) { pulses.splice(i, 1); continue; }
      const x = p.a.x + (p.b.x - p.a.x) * p.t, y = p.a.y + (p.b.y - p.a.y) * p.t;
      const grd = ctx.createRadialGradient(x, y, 0, x, y, 8 * DPR);
      grd.addColorStop(0, "rgba(255,255,255,.95)"); grd.addColorStop(1, "rgba(139,124,199,0)");
      ctx.fillStyle = grd; ctx.beginPath(); ctx.arc(x, y, 8 * DPR, 0, Math.PI * 2); ctx.fill();
    }
    raf = requestAnimationFrame(draw);
  }

  // Typing sequence
  const typed = document.getElementById("typed");
  const boot = document.getElementById("boot");
  const phrases = ["Selamat datang ke FAHAM", "Welcome to FAHAM"];
  const bootLines = [
    "› loading agent tools: ocr · redact · classify · scam_check · retrieve · locate · draft",
    "› connecting official source registry (.gov.my)",
    "› languages ready: BM · EN · 中文 · தமிழ்",
    "› agent online ✓"
  ];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function type(text, speed = 55) { for (const ch of text) { typed.textContent += ch; await sleep(speed); } }
  async function erase(speed = 25) { while (typed.textContent.length) { typed.textContent = typed.textContent.slice(0, -1); await sleep(speed); } }

  let finished = false;
  async function sequence() {
    await sleep(500);
    await type(phrases[0]);
    await sleep(900);
    await erase();
    await type(phrases[1], 65);
    document.getElementById("introSub").classList.add("show");
    for (const l of bootLines) { if (finished) return; boot.textContent = l; await sleep(650); }
    document.getElementById("introActions").classList.add("show");
  }

  function close(goto) {
    if (finished) return;
    finished = true;
    intro.classList.add("hide");
    try { sessionStorage.setItem("faham_intro_seen", "1"); } catch (e) {}
    setTimeout(() => { cancelAnimationFrame(raf); intro.remove(); }, 950);
    window.dispatchEvent(new CustomEvent("faham:enter", { detail: { goto } }));
  }

  let seen = false;
  try { seen = window.FAHAM_CONFIG.INTRO_ONCE_PER_SESSION && sessionStorage.getItem("faham_intro_seen") === "1"; } catch (e) {}
  if (seen) { intro.remove(); window.addEventListener("load", () => window.dispatchEvent(new CustomEvent("faham:enter", { detail: {} }))); return; }

  resize(); draw(); sequence();
  addEventListener("resize", resize);
  addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });
  document.getElementById("enterBtn").onclick = () => close();
  document.getElementById("enterDemo").onclick = () => close("agent");
  document.getElementById("skipIntro").onclick = () => close();
  addEventListener("keydown", (e) => { if (e.key === "Escape" || e.key === "Enter") close(); }, { once: true });
})();
