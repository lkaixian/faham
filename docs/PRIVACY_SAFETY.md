# Trust, privacy and safety

Judges are likely to ask three questions: *Can it be wrong? What happens to my letter? Why not just use a general chatbot?*

| Risk | Mitigation in FAHAM |
|---|---|
| Wrong or outdated procedure | Steps come from the official source registry at the time of use and are shown with the source link, a `retrieved_at` timestamp and a confidence level, labelled "not legal advice". |
| Privacy of letters (IC numbers, addresses) | `privacy.redact` runs first. Only redacted text reaches the other tools and the LLM. The API is stateless and does not store letters. PDPA compliance is a design goal. |
| "A general chatbot can do this" | FAHAM adds Malaysia-specific procedures, the nearest office with queue and booking details, scam checks, and a practice mode on the same agent. |
| Harmful action by the agent | The agent only drafts and pre-fills. `requires_approval: true` is set on every action, and the user approves before anything is sent or paid. |

## Data handling
1. **Read:** text comes out of the input. Images are read by OCR on the server (production target: on-device OCR).
2. **Redact:** `privacy.redact` masks IC numbers, emails, display names, phone numbers, account numbers, addresses, plates, names (after Kepada/Nama, titles, BIN/BINTI/A/L forms), passport-style IDs, dates of birth, and any leftover run of 8 or more digits. It is regex-based and best effort.
3. **Hide again for models:** in the agent's prompts, runs of 7 or more digits become `[NUMBER]`; tool results are masked too; a guard blocks any model call that still contains something that looks like an email, an IC or a long digit run.
4. **Process:** the agent and the explanation work on the masked text only. Scam verdicts use fixed templates, not model text.
5. **Reach outside:** only official URLs (never the message) and domain names that appear in the message leave the server for the agent's lookups.
6. **Discard:** the letter is not stored. Only learned glossary terms stay, on the user's device.

The pattern-by-pattern list, what each service receives, and the known gaps (free-form names, unusual address styles, words inside links) are in [AGENT.md, section 9](AGENT.md#9-personal-data-pii).

## Demo rules
- Use only clearly fictional letters, marked **SAMPEL · FIKTIF**.
- Never use real people's letters or IC numbers.
- Scam examples must not include working links or real phone numbers.
