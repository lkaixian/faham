/* Terms of Use, Privacy Notice and Code of Conduct page. The text lives in assets/legal.json (English and Malay in full;
   Chinese and Tamil show a short summary and then the English text). Language: ?lang=bm|en|zh|ta, else the saved choice, else Malay. */
(function () {
  var NAME = { bm: "BM", en: "EN", zh: "中文", ta: "தமிழ்" }, HTML_LANG = { bm: "ms", en: "en", zh: "zh", ta: "ta" };
  var T = window.FAHAM_T || {}, legal = null;
  var saved = ""; try { saved = JSON.parse(localStorage.getItem("faham_lang") || '""'); } catch (e) {}
  var q = new URLSearchParams(location.search).get("lang");
  var lang = [q, saved, "bm"].filter(function (l) { return NAME[l]; })[0];
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var ul = function (a) { return "<ul>" + a.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>"; };
  // a web address in the text becomes a link (https only); everything else stays escaped text
  var linkify = function (s) { return esc(s).replace(/https:\/\/[^\s<]+[^\s<.,;:)]/g, function (u) { return '<a href="' + u + '" rel="noopener noreferrer">' + u + "</a>"; }); };
  var para = function (s) { return "<p>" + linkify(s) + "</p>"; };
  var lis = function (a) { return "<ul>" + a.map(function (x) { return "<li>" + linkify(x) + "</li>"; }).join("") + "</ul>"; };

  function parts(L) {
    return L.parts.map(function (p, i) {
      var html = '<h2 id="part-' + i + '">' + esc(p.h) + "</h2>" + (p.intro ? para(p.intro) : "");
      html += p.sections.map(function (s, j) {
        return "<h3>" + (j + 1) + ". " + esc(s.h) + "</h3>" + (s.p || []).map(para).join("") + (s.ul ? lis(s.ul) : "");
      }).join("");
      return html;
    }).join("");
  }
  function draw() {
    if (!legal) return;
    var L = legal[lang] || legal.en, full = L.parts ? L : legal.en;
    document.documentElement.lang = HTML_LANG[lang];
    document.title = L.title + " · Tulen";
    document.getElementById("tmTitle").textContent = L.title;
    document.getElementById("tmDraft").textContent = L.draft;
    document.getElementById("tmBack").textContent = (T[lang] && T[lang].tm_back) || "Back to Tulen";
    document.getElementById("uiChips").innerHTML = Object.keys(NAME).map(function (k) {
      return '<button type="button" class="chip" data-l="' + k + '" lang="' + HTML_LANG[k] + '" aria-pressed="' + (k === lang) + '">' + NAME[k] + "</button>";
    }).join("");
    var out = '<p class="muted">' + esc(L.updated) + "</p>";
    if (L.parts) {
      out += '<section class="note"><h2 class="h3" style="margin-top:0">' + esc(L.summary_h) + "</h2>" + lis(L.summary) + "</section>";
    } else {
      out += para(L.note) + lis(L.points) + '<hr><p class="muted" lang="en">English full text</p>';
    }
    out += '<nav aria-label="Contents" class="toc"><ol>' + full.parts.map(function (p, i) { return '<li><a href="#part-' + i + '">' + esc(p.h) + "</a></li>"; }).join("") + "</ol></nav>";
    document.getElementById("tmBody").innerHTML = out + '<div lang="' + (L.parts ? HTML_LANG[lang] : "en") + '">' + parts(full) + "</div>";
  }
  document.getElementById("uiChips").addEventListener("click", function (e) {
    var b = e.target.closest("[data-l]"); if (b) { lang = b.dataset.l; draw(); }
  });
  var th = ""; try { th = JSON.parse(localStorage.getItem("faham_theme") || '""'); } catch (e) {}
  if (th === "dark") document.documentElement.dataset.theme = "dark";
  fetch("assets/legal.json").then(function (r) { return r.json(); }).then(function (d) { legal = d; draw(); })
    .catch(function () { document.getElementById("tmBody").textContent = "The text could not be loaded. Please try again."; });
})();
