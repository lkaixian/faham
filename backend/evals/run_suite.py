"""Measure the agent on the 12 real documents (8 genuine notices, 4 documented scam templates) against a running API.

    python backend/evals/run_suite.py [http://localhost:8081] [repeats] [extras]

The agent is not deterministic, so run it a few times. Reports, per document and in total: whether the verdict is right
(a notice must not be called a scam; a scam template must be), whether the fields came out right, and what the agent did
(rounds, tools, lookups outside Tulen, evidence it added, proposals the guard rails refused, seconds).
Stdlib only. Needs a model key in the API's environment for the agent to run; otherwise it reports rule-only results.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081").rstrip("/")
REPEATS = int(sys.argv[2]) if len(sys.argv) > 2 else 1
EXTRAS_ONLY = len(sys.argv) > 3 and sys.argv[3] == "extras"
SUITE = json.loads((Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "real" / "suite.json").read_text(encoding="utf-8"))


def analyse(payload):
    req = urllib.request.Request(BASE + "/api/analyze", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    t = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r), time.time() - t


# Hard cases beyond the 12 documents (fictional text). Genuine ones look unusual to a model; the scams are not covered by a specific rule.
EXTRA = [
    ("X1_GENUINE_survey_google_form", False, "Jemputan menyertai kajian kepuasan pelanggan Jabatan Perangkaan Malaysia (DOSM) 2026. Tempoh kajian: 1 Januari 2026 hingga 31 Disember 2026. Masa diperlukan: lebih kurang 10 minit. Pautan kaji selidik: https://forms.gle/duKHPXyPqngPEAFx6 . Soalan: perhubunganawam@dosm.gov.my atau 03-8885 4675. Portal: https://www.dosm.gov.my Facebook: https://www.facebook.com/StatsMalaysia/ X: https://x.com/statsmalaysia"),
    ("X2_GENUINE_kwsp_statement", False, "KWSP: Penyata Ahli anda untuk tahun 2025 telah tersedia. Sila log masuk ke i-Akaun di https://www.kwsp.gov.my untuk melihatnya. Tiada tindakan pembayaran diperlukan. Soalan: hubungi talian KWSP di laman web rasmi."),
    ("X3_SCAM_macau_safe_account", True, "Pegawai Bank Negara: akaun anda disyaki terlibat pengubahan wang haram. Untuk mengelakkan akaun dibekukan, pindahkan semua baki ke akaun selamat BNM 5123 4567 8901 hari ini. Jangan beritahu pihak bank atau keluarga kerana siasatan sulit."),
    ("X4_SCAM_parcel_fee", True, "Pos: Bungkusan anda tertahan di pusat kastam kerana alamat tidak lengkap. Bayar yuran penghantaran semula RM 3.50 di https://pos-my-redeliver.top/bayar dalam 24 jam atau bungkusan dipulangkan."),
    ("X5_SCAM_job_deposit", True, "Tawaran kerja dari rumah, gaji RM 400 sehari. Untuk mengesahkan jawatan, sila hantar gambar IC depan dan belakang serta deposit RM 200 melalui kad hadiah. Hubungi pengurus kami di Telegram @kerjaonline."),
]

rows = []
cases = ([] if EXTRAS_ONLY else [(d["document_id"], d["category"] == "documented_scam_template", d["request_payload"], d["ground_truth"]) for d in SUITE])     + [(n, sc, {"text": t, "language": "en"}, None) for n, sc, t in EXTRA]
for rep in range(REPEATS):
    for name, scam, payload, g in cases:
        out, secs = analyse(payload)
        a, f = out["agent"], out["fields"]
        verdict_ok = (out["scam"]["verdict"] == "likely_scam") == scam
        fields_ok = scam or g is None or (f["issuer"] == g["expected_issuer"] and f["amount"] == g["expected_amount"]
                                          and f["deadline"] == g["expected_deadline"] and f["reference"] == g["expected_ref"])
        doc = dict(document_id=name)
        rows.append(dict(doc=doc["document_id"][:34], scam=scam, verdict=out["scam"]["verdict"], verdict_ok=verdict_ok, fields_ok=fields_ok,
                         mode=a["mode"], rounds=a["rounds"], tools=len(a["tools"]), net=a["network"], signals=a["signals"],
                         refused=a["refused"], filled=len(a["filled"]), secs=round(secs, 1)))
        print(f"{'OK ' if verdict_ok and fields_ok else 'BAD'} {rows[-1]['doc']:34} {'scam  ' if scam else 'notice'} -> {out['scam']['verdict']:11} "
              f"mode={a['mode']} rounds={a['rounds']} tools={len(a['tools'])} net={a['network']} +signals={a['signals']} refused={a['refused']} {secs:.1f}s", flush=True)

n = len(rows)
notices, scams = [r for r in rows if not r["scam"]], [r for r in rows if r["scam"]]
pct = lambda xs, k: f"{sum(1 for r in xs if r[k])}/{len(xs)}"
print(f"\n{n} runs against {BASE}")
print(f"  genuine notices not called a scam: {sum(1 for r in notices if r['verdict'] != 'likely_scam')}/{len(notices)}   fields correct: {pct(notices, 'fields_ok')}")
print(f"  scam templates called a scam:      {sum(1 for r in scams if r['verdict'] == 'likely_scam')}/{len(scams)}")
print(f"  agent ran (mode ai): {sum(1 for r in rows if r['mode'] == 'ai')}/{n}   mean seconds: {sum(r['secs'] for r in rows) / n:.1f}   "
      f"mean rounds: {sum(r['rounds'] for r in rows) / n:.1f}   mean tools: {sum(r['tools'] for r in rows) / n:.1f}   "
      f"lookups outside Tulen: {sum(r['net'] for r in rows)}")
print(f"  evidence the agent added to genuine notices (false-alarm pressure): {sum(r['signals'] for r in notices)}   refused by guard rails: {sum(r['refused'] for r in rows)}")
