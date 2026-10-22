# 07 — Card import and card gallery

**What to build:** Our own card file for the v1 card set (ADR 0005): the 208 Project Cards (#001–#208) and the 12 Corporations (10 base plus the 2 Corporate Era ones).

For each card it holds:
- name, number and type;
- cost, Tags and Requirements;
- Victory Points and text;
- whatever icon and layout information the GUI needs to draw the card like the fan-made card list does.

The data is parsed from the card list at ssimeonoff.github.io/cards-list by a re-runnable import tool, and the output is committed. The card list's icon images are downloaded into the project, with the user's OK first.

A mismatch report compares the imported data with the open-source game's card definitions. The card catalog is available from the Python engine module. The GUI gets a gallery to browse all cards, drawn in the card list's style.

**Blocked by:** 01 — Walking skeleton

**Status:** ready-for-agent

- [ ] All 208 Project Cards and 12 Corporations are present with their printed data, and Corporate Era cards are marked.
- [ ] The import tool can be re-run, and nothing depends on the website at runtime.
- [ ] The mismatch report lists every field that differs from the open-source game (cost, Tags, Requirements, Victory Points) and is kept in the project for the card-batch tickets.
- [ ] The icons are stored in the project.
- [ ] The card catalog is available from the Python engine module.
- [ ] The GUI gallery draws every card readably in the card list's style, filters by type and Tag, and enlarges a card on hover or click.
- [ ] Ten cards of different types are compared side by side with the card list page and look the same in substance.
