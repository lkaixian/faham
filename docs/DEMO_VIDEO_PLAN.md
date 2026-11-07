# Demo video plan (Arena Solusi: Agentic AI Challenge)

Rule 4.1: at most 5 minutes, showing the agent working. Target **4:30**. Language: English with Malay subtitles (rule 4.4). The DEMO watermark must be visible all the way through (rule 4.2). No real personal data anywhere (rule 5.4).

**Deadline: submission closes 9 Nov 2026, 11.59 pm.** Today (7 Nov) is prep, 8 Nov is recording and editing, 9 Nov is upload, link test and the form. The live pitch on 19 Nov reuses the same scenes; this plan is only the video.

## The one idea the video must land

> **Tulen asks "should this have reached you?" and shows its evidence. It is an agent that investigates, not an antivirus and not a chatbot.**

Everything on screen should serve that: the agent *decides* (plans, picks tools, reads the organisation's own website), the *rules are the floor* (the AI can raise concern, never lower it), a *person approves* every action, and it never says "safe".

| Judging criterion | The scene that proves it |
|---|---|
| Innovation and creativity | C: files that arrive by chat (ZIP, app, macro) get their own fast, no-AI flow; "tulen or tipu" framing |
| Quality of the agent (autonomous, AI at the core, responsible) | A: live plan, tools, official-site check, evidence; E: guard rails |
| Impact and usability | B and D: real letters, four languages, easy mode, read aloud |
| Pitch | The opening problem and the close |

## Storyboard (4:35 total; trim scene D2 first if over)

| Time | Scene | On screen | Say (English) | Subtitle (Malay) |
|---|---|---|---|---|
| 0:00 | **Hook** (20 s) | A fictional "wedding invitation" WhatsApp message with a file, then a "bill" ZIP | "Scammers no longer only send links. They send files, from people you know, and messages that copy your bank." | "Penipu bukan lagi hanya menghantar pautan. Mereka menghantar fail, daripada orang yang anda kenal, dan mesej yang meniru bank anda." |
| 0:20 | **Logo** (15 s) | The Tulen wordmark, tagline "Tulen atau tipu? Semak dulu." Welcome screen, enter | "This is Tulen. Is it genuine or fake? Check first." | "Inilah Tulen. Tulen atau tipu? Semak dulu." |
| 0:35 | **A. The agent investigates** (70 s) | Paste `A_SAMPEL_sms-pinjaman.txt`. Stay on the live timeline: goal, plan, then each tool as it appears (read the message, look up the bank in the registry, **fetch the bank's own website**), then the result with evidence marked | "It does not just guess. It writes a plan, looks the bank up, then reads the bank's real website to see whether this is how it works. Every sign has the exact words behind it." | "Ia tidak meneka. Ia menulis pelan, menyemak bank itu, kemudian membaca laman web sebenar bank untuk melihat sama ada begini caranya. Setiap tanda ada perkataan sebenar di belakangnya." |
| 1:45 | **B. A real-looking letter** (25 s) | Built-in LHDN example (the genuine one). Show "no scam signs found" and the "check it yourself" steps | "A genuine-looking letter. Tulen finds no signs, but it never says safe. It tells you how to check on the official site." | "Surat yang nampak sah. Tulen tidak menjumpai tanda, tetapi tidak pernah kata selamat. Ia tunjuk cara menyemak di laman rasmi." |
| 2:10 | **C. Files** (65 s) | Drop `C1` (tick "I got this on WhatsApp"): result in about half a second. Then `C2` (the app): permissions explained. Then `C3` (harmless ZIP): "nothing wrong, but not a letter either". Point at "what we checked / did not check" and the fingerprint | "A file is not a letter, so Tulen does not ask an AI. It looks at what it is, how it arrived and what it asks for. A program dressed as a PDF. An app that wants your text messages and your screen, the way TAC codes get stolen. And a harmless file, which it still will not call safe. This is not an antivirus. It says what it checked and what it did not." | "Fail bukan surat, jadi Tulen tidak bertanya AI. Ia melihat apa fail itu, bagaimana ia sampai dan apa yang diminta. Program yang menyamar sebagai PDF. Aplikasi yang mahu mesej teks dan skrin anda, cara kod TAC dicuri. Dan fail yang tidak berbahaya, yang masih tidak dikatakan selamat. Ini bukan antivirus. Ia nyatakan apa yang disemak dan apa yang tidak." |
| 3:15 | **D. Everyone can use it** (25 s) | Easy mode, switch BM / EN / 中文 / தமிழ், press Listen | "Easy mode: big text, three steps. Four languages, read aloud, for older relatives." | "Mod mudah: tulisan besar, tiga langkah. Empat bahasa, dibacakan, untuk saudara yang lebih tua." |
| 3:40 | **E. Why you can trust it** (25 s) | Show a result's trace and the "agent" card; flash the approval note on the draft ("nothing is sent or paid") | "Personal details are masked first. Files are read in a locked-down process. Nothing is stored. The AI can raise a concern but never lower it. And you approve every action." | "Butiran peribadi ditutup dahulu. Fail dibaca dalam proses yang dikunci. Tiada apa disimpan. AI boleh menaikkan kebimbangan tetapi tidak menurunkannya. Dan anda meluluskan setiap tindakan." |
| 4:05 | **Declaration** (20 s) | One slide: models and tools (see `COMPETITION.md`) | "Built with ILMU and Claude for the agent, Tesseract for photos, FastAPI and plain JavaScript, and Claude Code as our coding assistant." | "Dibina dengan ILMU dan Claude untuk ejen, Tesseract untuk foto, FastAPI dan JavaScript biasa, serta Claude Code sebagai pembantu pengekodan." |
| 4:25 | **Close** (10 s) | Wordmark and tagline | "Tulen atau tipu? Semak dulu." | "Tulen atau tipu? Semak dulu." |
| optional | **D2. Email autonomy** (20 s) | Forward a made-up email, the reply arrives in the sender's language | "Forward it to Tulen and it answers on its own." | "Kirim kepada Tulen dan ia menjawab sendiri." |

D2 is the strongest "autonomy" evidence but needs the email channel (Cloudflare, Mailtrap) working on the day. Record it separately and keep it only if it works first time; otherwise cut it.

## Demo files (already built)

Run once on the recording machine:

```bash
cd backend && python ../scripts/make_demo_files.py     # writes ../demo-files/ (git-ignored)
```

| File | Scene | Tick "got it on WhatsApp" | What Tulen shows (checked on 7 Nov) |
|---|---|---|---|
| `A_SAMPEL_sms-pinjaman.txt` | A | no (paste it) | agent investigates; likely scam or caution depending on the model's run |
| `C1_SAMPEL_bil-anda.zip` | C | **yes** | likely scam: a program named like a PDF, lure-like name (about 0.6 s) |
| `C2_SAMPEL_JEMPUTAN-MAJLIS-PERKAHWINAN.apk` | C | **yes** | likely scam: app that can read SMS and draw over other apps (about 0.6 s) |
| `C3_SAMPEL_penyata-gaji.zip` | C | no | caution, no signs, "not a letter" note |
| `C4_SAMPEL_notis-lhdn.docx` | C (optional) | **yes** | likely scam: a macro hidden under a plain Word name |
| `C5_SAMPEL_perisian.rar` | C (optional) | no | caution: "this kind of archive is not opened" |

All are harmless: the "program" is two bytes and zeros, the "app" has no code. Their names say SAMPEL.

## Scene details that save time

- **The agent takes 17 to 28 seconds.** Show the first steps live (about 15 s), cut with a small caption "shortened, about 25 s in real life", then show the result. Do not speed up the screen silently.
- **Scene A is the most variable** because a model is not deterministic. Record it 3 times and keep the best take; keep the take where the agent reads the bank's website.
- **Scene C is deterministic and fast**: it is the safest scene. Record it first to warm up.
- **Zoom in** on the message pane (marked evidence), the tool timeline and the "what we checked / did not check" line. Judges read these.
- **Cursor**: slow, deliberate. Pause one second on each result.

## Say, and do not say

| Say | Never say |
|---|---|
| "No scam signs found. Check it yourself." | "Safe", "genuine", "virus-free", "100% accurate" |
| "It is not an antivirus. It says what it checked and what it did not." | "It detects malware" |
| "On our own test set of 88 messages in four languages the rules caught every scam and raised no false alarms." (This is our synthetic set; say "our test set") | Any national loss statistic (the research notes found conflicting figures) |
| "Security researchers have reported scam apps disguised as wedding invitations in Malaysia." | Specific campaign names or advisory numbers unless you re-check the source on the day |

## Recording checklist (rule 5.4 and 4.2)

- [ ] `docker compose up -d --build`, then open the same address you will pitch on. Hard refresh (Ctrl+F5) to load the new logo.
- [ ] DEMO watermark and corner badge visible in every shot; address bar visible.
- [ ] Only the built-in SAMPEL examples and `demo-files/`. **Do not open `TEST1.pdf`** (real email address). No real names, phone numbers, IC numbers or accounts.
- [ ] Close the `.env`, Cloudflare, Mailtrap and any chat apps; hide bookmarks and notifications (Windows: Focus assist on).
- [ ] 1080p, 30 fps, MP4 (H.264). Record the screen with OBS Studio; record narration separately with a headset microphone (a quiet room), then align in the edit.
- [ ] Check the DEMO scenes in order once without recording (a dry run takes 6 minutes).
- [ ] If the AI is slow or unavailable: say so, and rerun; the file scenes and the rule checks do not depend on it.

## Roles and timeline

| When | Who | What |
|---|---|---|
| **7 Nov (today)** | engineer | Build the demo files; rebuild containers; dry run of all scenes; fix anything that looks wrong |
| 7 Nov | writer | Finalise the English narration and the Malay subtitles (the table above is the draft); read it aloud once against a stopwatch |
| 7 Nov | designer | Hook clip (a fictional wedding-invitation message and a "bill" ZIP, both marked SAMPEL), logo reveal, declaration slide |
| **8 Nov** | presenter + engineer | Record scenes A to E (3 takes of A), narration, optional D2 |
| 8 Nov | editor | Cut to under 4:45, add Malay subtitles, captions for shortened waits, check the watermark is visible in every cut |
| 8 Nov (evening) | whole team | Watch it once start to finish; fix errors; export |
| **9 Nov (morning)** | editor | Upload to YouTube (unlisted) or Google Drive with "Anyone with the link" |
| 9 Nov | anyone | **Open the link in a private window while logged out** (rule 4.3); fill the form; submit before 6 pm, not at 11.59 pm |

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| The model is slow or gives a different answer in scene A | Three takes; keep the best; the rules floor keeps the verdict safe whatever the run |
| The tunnel or email channel fails | Record on `localhost:8081`; cut D2 |
| The AI service is unavailable | Rule-based results still work; scene C is unaffected (it uses no AI) |
| A shot shows something private | Re-record; check every frame in the edit |
| Video over 5:00 | Cut D2, shorten B to 15 s, shorten the declaration |
| Upload link does not open | Test in a private window; keep a second copy on Google Drive |

## Before you submit

- Declaration text for the form: `docs/COMPETITION.md`, section "Declaration for the entry form".
- Re-read the live rules once; the organiser may amend them (rule 7.4).
- Open decisions on category (IPT or Open) and one entry per team are in `docs/COMPETITION.md`.
