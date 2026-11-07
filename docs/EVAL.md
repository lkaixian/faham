# Evaluation

Last run: 7 November 2026. Rules only, no LLM, run in process on Python 3.11.

## What is measured

`backend/tests/eval/dataset.json` holds 88 fictional messages: 22 per language (BM, English, 中文, தமிழ்), half `scam` and half `legit`.
Scams cover Macau/police, parcel, family impersonation, job, investment, love, refund phishing, APK install, bank phishing,
prize, court summons and telco-police scripts. Legit messages are bills, bank alerts, a statutory tax notice, a road-tax
reminder, school and clinic notices, receipts and family or work chat. All names, numbers and links are made up.

A message counts as **predicted scam** when the verdict is `likely_scam` (score below 60). `caution` is neither a hit nor a
false alarm: it tells the user to verify first. The report also counts how many scams got no signal at all (must be 0) and
how many legit messages got `caution`.

## Run it

```bash
cd backend
python -m tests.eval.run                                   # report
python -m tests.eval.run --json report.json                # also write JSON
python -m tests.eval.run --min-recall 0.9 --max-fpr 0.1    # exit code 1 if a threshold is missed
pytest -q tests/eval                                       # the same gate as tests
```

CI (`.github/workflows/ci.yml`) runs `pytest -q`, which includes `tests/eval/test_eval.py`, and then the command with the two
thresholds. **The build fails if scam recall is below 0.9 or the legit false-positive rate is above 0.1**, overall or in any one language.

## Results

| Split | n | Recall | False-positive rate | Precision |
|---|---|---|---|---|
| All | 88 | 1.000 | 0.000 | 1.000 |
| dev (72) | 72 | 1.000 | 0.000 | 1.000 |
| held_out (16) | 16 | 1.000 | 0.000 | 1.000 |

Latency of the rules verdict, in process, cache cleared for every message: p50 0.6 ms, p95 1.2 ms, max 8 ms.
The streaming endpoint's 2 s target for the first verdict is about network and queueing, not these rules. LLM latency is not measured here.

Legit messages that got `caution`: 23 of 44. This is by design: a sender that the registry does not know can never score above 79,
so ordinary chat and bills from unknown senders say "check it yourself" rather than "no signals". It is a usability cost
(more `caution` than ideal), not a safety one.

## How much to trust 1.000

Not much, and this section exists so nobody quotes it as accuracy.

1. **The dev split is not independent.** The first run of the 72 dev messages gave recall 0.694: job, investment and
   romance scams had no rule at all and only reached `caution`. Three rules (`guaranteed_returns`, `advance_fee`, `romance_money`)
   were added for them. Those rules were written while looking at those messages, so dev recall of 1.000 mostly shows that the
   rules cover the examples they were written from.
2. **The held-out split was clean only once.** 16 further messages were written after the rules were fixed. First result:
   recall 0.625 (5 of 8 scams), false-positive rate 0.000. All three misses were prize or lottery scams in BM, 中文 and தமிழ்.
   A `prize_win` rule was then added, so the split is no longer clean for that scam type. Held-out 1.000 now means "fixed what it found".
3. **Loose rules were caught by probing, not by the dataset.** The first versions of `prize_win`, `advance_fee` and
   `romance_money` fired on "you won the badminton game", "deposit your cheque ... register" and "my friend's account on Google Drive".
   The dataset did not contain those sentences. They were tightened and the probes are now regression tests in `tests/eval/test_eval.py`.
4. **Small and synthetic.** 88 short messages written by one person, one scam script each. Real scams vary far more (typos, mixed
   languages, voice-note transcripts, screenshots). A real corpus will score lower. The legit side has no long official letters
   beyond the 12 documents in `tests/fixtures/real`.

Before quoting a number to anyone, collect messages the rules have never seen (for example from NSRC or CCID public advisories,
or volunteers' screenshots with names removed), add them as a new `split`, and report that split alone.

## Adding data

Append objects to `dataset.json` through `tests/eval/` tooling or by hand: `{"id", "lang": "bm|en|zh|ta", "label": "scam|legit", "kind", "split", "text"}`.
Use only fictional content. Keep `held_out` for messages written before you look at the rules' output.
