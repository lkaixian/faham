/* FAHAM welcome intro: a neural-network canvas, typed greeting and a short "agent boot" log.
   Ported from the earlier dashboard prototype. Shows once per browser session, never on embed pages,
   and becomes a static card when the user prefers reduced motion. */
(function () {
  const intro = document.getElementById("intro");
  if (!intro) return;
  const KEY = "faham_intro_seen";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let seen = false;
  try { seen = sessionStorage.getItem(KEY) === "1"; } catch (e) {}
  const done = () => window.dispatchEvent(new CustomEvent("faham:intro-done"));   // app.js shows its terms dialog after this
  if (seen) { intro.remove(); done(); return; }

  const page = [...document.body.children].filter((el) => el !== intro);
  page.forEach((el) => el.setAttribute("inert", ""));
  document.documentElement.style.overflow = "hidden";

  const canvas = document.getElementById("neural");
  const ctx = canvas.getContext("2d");
  const DPR = Math.min(window.devicePixelRatio || 1, 2);
  const accent = (getComputedStyle(document.documentElement).getPropertyValue("--accent") || "#5a3b8c").trim();
  let W, H, nodes = [], raf, finished = false;
  const mouse = { x: -999, y: -999 };
  const pulses = [];

  function resize() {
    W = canvas.width = innerWidth * DPR;
    H = canvas.height = innerHeight * DPR;
    const count = Math.min(110, Math.floor((innerWidth * innerHeight) / 14000));
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.35 * DPR, vy: (Math.random() - 0.5) * 0.35 * DPR,
      r: (Math.random() * 1.6 + 0.6) * DPR, p: Math.random() * Math.PI * 2,
    }));
  }

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
    const cx = W / 2, cy = H / 2.3, link = 140 * DPR;
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy; n.p += 0.03;
      n.vx += (cx - n.x) * 0.0000025; n.vy += (cy - n.y) * 0.0000025;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
      if (Math.hypot(n.x - mouse.x * DPR, n.y - mouse.y * DPR) < 120 * DPR) {
        n.x += (n.x - mouse.x * DPR) * 0.01; n.y += (n.y - mouse.y * DPR) * 0.01;
      }
    }
    ctx.strokeStyle = accent; ctx.lineWidth = DPR * 0.7;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j], d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < link) {
          ctx.globalAlpha = (1 - d / link) * 0.25;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    ctx.fillStyle = accent;
    for (const n of nodes) {
      ctx.globalAlpha = 0.3 + (Math.sin(n.p) + 1) * 0.25;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill();
    }
    if (Math.random() < 0.25) spawnPulse();
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i]; p.t += 0.03;
      if (p.t >= 1) { pulses.splice(i, 1); continue; }
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      ctx.arc(p.a.x + (p.b.x - p.a.x) * p.t, p.a.y + (p.b.y - p.a.y) * p.t, 3 * DPR, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    raf = requestAnimationFrame(draw);
  }

  const typed = document.getElementById("typed");
  const boot = document.getElementById("boot");
  const sub = document.getElementById("introSub");
  const actions = document.getElementById("introActions");
  const enter = document.getElementById("enterBtn");
  const phrases = ["Selamat datang ke FAHAM", "Welcome to FAHAM"];
  const bootLines = [
    "> loading agent tools: read, verify, explain, teach, route, act",
    "> connecting official source registry (.gov.my)",
    "> languages ready: BM, EN, 中文, தமிழ்",
    "> agent online",
  ];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function type(text, speed) { for (const ch of text) { if (finished) return; typed.textContent += ch; await sleep(speed); } }
  async function erase() { while (typed.textContent.length && !finished) { typed.textContent = typed.textContent.slice(0, -1); await sleep(25); } }

  async function sequence() {
    await sleep(500);
    await type(phrases[0], 55); await sleep(900); await erase(); await type(phrases[1], 65);
    sub.classList.add("show");
    for (const l of bootLines) { if (finished) return; boot.textContent = l; await sleep(650); }
    actions.classList.add("show");
  }

  function close() {
    if (finished) return;
    finished = true;
    try { sessionStorage.setItem(KEY, "1"); } catch (e) {}
    intro.classList.add("hide");
    page.forEach((el) => el.removeAttribute("inert"));
    document.documentElement.style.overflow = "";
    setTimeout(() => { cancelAnimationFrame(raf); intro.remove(); }, reduce ? 0 : 950);
    const main = document.getElementById("main");
    if (main) { main.setAttribute("tabindex", "-1"); main.focus({ preventScroll: true }); }
    done();
  }

  enter.onclick = close;
  document.getElementById("skipIntro").onclick = close;
  addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });

  if (reduce) {
    typed.textContent = phrases[1];
    boot.textContent = bootLines[bootLines.length - 1];
    sub.classList.add("show"); actions.classList.add("show");
    intro.classList.add("static");
  } else {
    resize(); draw(); sequence();
    addEventListener("resize", resize);
    addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });
  }
  enter.focus({ preventScroll: true });
})();
