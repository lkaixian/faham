# Terms, Privacy and Code of Conduct: review notes

Written 6 November 2026. The published text is `frontend/assets/legal.json` (shown at `/terms`). `scripts/legal_md.py` turns it into `CODE_OF_CONDUCT.md` and `docs/TERMS_AND_PRIVACY.md`. This page records what we reviewed, what we took, and what still needs a human.

**This is a draft, not legal advice. It has not been reviewed by a lawyer.**

## Sources reviewed

| Source | Reuse terms seen | Taken as an idea | Left out |
|---|---|---|---|
| [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) | Page asks for attribution when adapted; licence text not on the page (check the project's repository) | Graduated response (reminder, warning, temporary, permanent); duty to keep reports private; protecting others' private information | Contact placeholders and account-based ban tiers |
| [Mozilla Community Participation Guidelines](https://www.mozilla.org/en-US/about/governance/policies/participation/) | CC BY-SA 3.0 | Abuse of the reporting process is itself a violation; stop when asked; encouraging bad behaviour counts | Event and staff rules, response-time promises |
| [Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct) | CC BY-SA 3.0 | Spirit over rulebook; ask for help when unsure | Leadership and council structure |
| [Wikimedia Universal Code of Conduct](https://foundation.wikimedia.org/wiki/Policy:Universal_Code_of_Conduct) | CC BY-SA | Doxing and manipulation named as unacceptable | Editing rules, committee process |
| [Python Software Foundation CoC](https://policies.python.org/python.org/code-of-conduct/) | CC BY-SA 3.0 | Comply at once when asked to stop; scope lists the exact channels covered | Event, weapons and transparency-report sections |
| [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) | Not stated on the page | No impersonation or false identity; no deceptive content; limits on excessive use; protect users as a whole | Repository, package and API rules |
| [Mozilla Websites Terms of Use](https://www.mozilla.org/en-US/about/legal/terms/mozilla/) | Not stated | "As is" disclaimer, date at the top and continued use as acceptance, one language controls translations | US liability cap, indemnity, California law, accounts |
| [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) (structure only) | CC BY-SA | "General information only, seek a professional" wording; plain-language summary box | Editing, paid-contribution and arbitration clauses |

**Why we wrote our own words.** Four of these are CC BY-SA, which would oblige us to publish our whole text under the same licence if we copied sentences. We took ideas and wrote the wording ourselves, and the Code of Conduct credits all of them in its last section.

**Not reviewed.** The Citizen Code of Conduct site did not load (DNS failure). No Automattic or other CC0 terms template was searched or read. Add them if you want a wider comparison.

## What is specific to FAHAM

These points are in the text because a generic template would miss them:

- It is not an agency and must not look like one (no logos, no impersonation).
- "No scam signs found" is never "genuine". The text says so in the summary and in the terms.
- People paste other people's letters, so the terms and code say not to without permission.
- Masking is best effort, and the privacy notice says what can still leak.
- Third parties are named: ILMU and Anthropic (masked text), Cloudflare (traffic and incoming email), Mailtrap (sent replies), Meta (Messenger).
- Chat and email replies are automatic and rate limited (about one per sender per hour).
- Minors: use with a guardian.

## Facts in the privacy notice to check against the code

| Statement | Where it comes from | Status |
|---|---|---|
| Letters are read in memory and not saved | `backend/app/main.py`, `ingest.py` | True in the code |
| Long digit strings stop the AI and voice calls | `llm.py` `RESIDUAL_PII`, `tts.py` | True in the code |
| Chat consent and counters kept as scrambled codes, up to 30 days, lost on restart | `channels.py` `TTL`, `_hid` | True in the code |
| One reply per email sender per hour | `channels.py` `_count` | True in the code |
| Mailtrap keeps delivery logs that include the reply | Mailtrap behaviour | **Verify** in your Mailtrap account |
| Cloudflare and Mailtrap may process data outside Malaysia | Provider locations | **Verify** |
| No access logs with message content | uvicorn and nginx defaults | Check your own log settings |

## Malaysia PDPA: what is and is not established

Established from the regulator's pages (in Malay): the seven principles in section 5 are General, Notice and Choice, Disclosure, Security, Retention, Data Integrity and Access. The 2024 amendment renames "data user" as "data controller". The regulator has an October 2026 consultation on AI and personal data protection.

**Not established (marked [verify]; ask a lawyer):**

1. Whether a free service with no accounts counts as a "commercial transaction" under the Act. The regulator's text we could read says the Act applies to processing "in respect of commercial transactions".
2. What a privacy notice must contain, and whether it must be in Malay and English. We publish both languages to be safe.
3. Rules on children and consent. We ask under-18s to use FAHAM with a guardian, which is a precaution, not a legal test.
4. Cross-border transfer conditions, because Cloudflare, Mailtrap, Anthropic and Meta may process data abroad.
5. Whether a data protection officer, breach notification or registration applies to a project this size.
6. Governing law and courts: the text says Malaysia. A lawyer should confirm that wording.

## To do before the text goes beyond a demo

- Replace the GitHub issues link with a dedicated contact address (set in `legal.json`, then run `python scripts/legal_md.py`).
- Turn on private vulnerability reporting in the repository settings, so security reports have a private route (the Code of Conduct promises one).
- Have the Malay text read by a Malay speaker and the Chinese and Tamil summaries by native speakers.
- Have a lawyer review the liability limit, the governing-law line and the PDPA points above.
- Re-check this table if a provider changes (for example a different AI or mail service).
