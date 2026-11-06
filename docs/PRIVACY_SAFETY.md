# Trust, privacy and safety

Judges are likely to ask three questions: *Can it be wrong? What happens to my letter? Why not just use a general chatbot?*

| Risk | Mitigation in FAHAM |
|---|---|
| Wrong or outdated procedure | Steps come from the official source registry at the time of use and are shown with the source link, a `retrieved_at` timestamp and a confidence level, labelled "not legal advice". |
| Privacy of letters (IC numbers, addresses) | `privacy.redact` runs first. Only redacted text reaches the other tools and the LLM. The API is stateless and does not store letters. PDPA compliance is a design goal. |
| "A general chatbot can do this" | FAHAM adds Malaysia-specific procedures, the nearest office with queue and booking details, scam checks, and a practice mode on the same agent. |
| Harmful action by the agent | The agent only drafts and pre-fills. `requires_approval: true` is set on every action, and the user approves before anything is sent or paid. |

## Data handling
1. **Scan:** the image stays on the device until it is redacted (production target: on-device OCR).
2. **Redact:** IC, phone, account and addressee are masked.
3. **Process:** the agent works on the redacted text only.
4. **Discard:** the letter is not stored. Only the learned glossary terms stay, on the user's device.

## Demo rules
- Use only clearly fictional letters, marked **SAMPEL · FIKTIF**.
- Never use real people's letters or IC numbers.
- Scam examples must not include working links or real phone numbers.
