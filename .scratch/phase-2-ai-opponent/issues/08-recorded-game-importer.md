# 08 — Recorded Game importer

**What to build:** A command that reads `tm_statistics/` and writes a compact private dataset to `.cache/` (ADR 0012): the Games' settings and results, and for now each Draft and buy Decision, with what that Player could see and what they picked.

Each record describes one Player's Decision: the cards on offer, those kept so far, and the public state from the per-move trackers (Global Parameters, Resources, Production, Tag counts, Terraform Rating, cards played, Milestones, Awards), and both Players' ratings and the result. Action-phase Decisions come after tickets 09 and 10, so the format must leave room for them.

Start from `experiments/logs_scan.py`, which scans the archive on all cores. No file in the archive is ever run, and it is read with `python -I` or equivalent.

**Known traits to handle:** see "Recorded Games" in the spec. In particular, card names need a map to the catalog, wording differs by scraper version, and several perspectives of one Game count once.

**Blocked by:** 01 — Prelude cards in the catalog

**Status:** ready-for-agent

- [ ] One command builds the dataset, using all cores, resumes after interruption, and reports coverage: Games read, skipped and why, by setting, rating and scraper version.
- [ ] Filters: 2 Players, Tharsis, Corporate Era, no Colonies, Draft on. Prelude, conceded, rating and date are stored so that training can choose.
- [ ] Every card name in the kept Games resolves to a catalog id, or the report lists it.
- [ ] Test on hand-written snippets: each known trait, including "cancels their move" and a duplicate perspective.
- [ ] Test: no record holds the opponent's hand, the opponent's Draft cards, or the deck. Cards a Player passed on stay visible to that Player, as in the Player View.
- [ ] Player names aren't in the dataset; anonymous ids and ratings are.
- [ ] The dataset is well under 10 GB, and its size is recorded under Comments. Then I decide whether to delete the archive.
- [ ] `tm_statistics/` and the dataset stay out of git.
- [ ] Counts are compared with the spec's table, and any difference is explained under Comments.

## Comments
