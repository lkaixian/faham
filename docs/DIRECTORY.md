# Official directory

`backend/app/data/official_directory.json` lists real Malaysian organisations and the websites they own: 549 entries, about 620 domains.

| Category | What it covers |
|---|---|
| bank, insurer, payment, investment, credit, regulator | Licensed banks (BNM list), insurers and takaful, e-wallets, PayNet, SC, Bursa, PNB |
| federal | Ministries, departments, statutory bodies, social security |
| state | State governments, water and sewerage, zakat and religious bodies |
| council | Local authorities (PBT) in all states |
| university | Public, private and branch-campus universities, polytechnics, education bodies |
| telco, utility, courier, ecommerce, toll, airline, retail, service | Companies most often copied in scam messages |

## What it does

- A link to a listed domain (or any subdomain) shows as an official domain instead of an "unofficial domain" risk.
- `fetch_official_page` may download pages on listed domains.
- `lookup_registry` answers a name or alias ("Xiamen University Malaysia", "DOSM") with the entity and its websites.
- A near-copy of a company or federal name (`maybnk-login.com`) is flagged as a look-alike. Place and campus names are left out of this check so ordinary sites are not condemned.

## What it does not do

- It carries no procedures. Steps, payment methods and lessons still come only from `official_sources.json` (AGENTS.md rule 5).
- It never says a message is genuine. A real domain in a link proves only that the link goes to that organisation.
- `*.gov.my` and `*.edu.my` are trusted as whole suffixes (only government and accredited education bodies can register them). The directory adds `.com.my`, `.my` and global domains.
- Global parent domains (`sc.com`, `citigroup.com`, `dhl.com`) are listed because genuine Malaysian messages link to them. A scammer's link to the same parent site would also look official.

## Provenance and known gaps

Built from BNM, MOHE/MQA, KPKT/JKT and each organisation's own site, then checked for a valid host name, a DNS answer and no domain shared by two entries. Some entries were confirmed only from search results or a partner's page, and some had no confirmable domain (for example KAF Digital Bank, Heriot-Watt Malaysia). Every entry has a `source` URL. Add or fix entries by editing the JSON; `pytest` checks its shape.
