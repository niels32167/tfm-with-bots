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

- [x] All 208 Project Cards and 12 Corporations are present with their printed data, and Corporate Era cards are marked.
- [x] The import tool can be re-run, and nothing depends on the website at runtime.
- [x] The mismatch report lists every field that differs from the open-source game (cost, Tags, Requirements, Victory Points) and is kept in the project for the card-batch tickets.
- [x] The icons are stored in the project.
- [x] The card catalog is available from the Python engine module.
- [x] The GUI gallery draws every card readably in the card list's style, filters by type and Tag, and enlarges a card on hover or click.
- [x] Ten cards of different types are compared side by side with the card list page and look the same in substance.

## Comments

### 2026-10-23 — implemented (Claude)

**Decisions made with the user:**
- **Downloads** (each approved first):
  - the card list page and its stylesheet;
  - the 39 icon and font files the v1 cards use (917 KB), including the textured card background `images/mars.png` and the Corporate Era triangle;
  - the open-source game's card definitions (`src/server/cards/base`, `src/server/cards/corporation` and `StandardCardManifests.ts`) at commit `4d30aa07f14eeb5aa5647775ce5a7c9e49f6ac04`.
- **What git keeps:**
  - the page snapshot (`tools/card_list_snapshot/`), so the import runs offline and a diff shows upstream changes;
  - the icons (`gui/public/card-list/`);
  - only the report from the open-source game, whose GPL-3.0 files stay in `.cache/open-source-cards/<commit>/` (ignored by git).
- **Card file:** one JSON file, `engine/cards/cards.json`, with one line per field. Running the import again rewrites the printed fields and keeps any other field, which is where ticket 08's hand-written effect data goes.
- **Engine:** `include_str!` builds the card file in, and it is parsed once into a `LazyLock<Vec<Card>>` (`engine/src/cards.rs`). There is no hash map, and a Game holds no card data, so nothing is copied with a Game. This adds the `serde_json` crate.
- **To the GUI:** `tm_engine.card_catalog()`, which the server sends as `{"type": "card_catalog", "cards": [...]}` first on each connection.
- **Card faces:** an element tree, `"face": {"content": <element>, "title_style": {...}}`. `title_style` is there only for the three long titles printed smaller.
- **Card ids:** snake_case names (`black_polar_dust`). Corporations have `number` and `cost` null; they have no printed number.
- **Gallery:** an overlay from a **Cards** button in the top bar and on the setup screen.
- **Test seams:**
  - `tests/cards/`: the catalog through `tm_engine`;
  - `tests/tools/`: the import, the mismatch parser, the icons being stored, and the engine's catalog equalling the import of the snapshot;
  - `tests/server/test_card_catalog.py`: the catalog message.
- **Names:** the card list writes "Underground city" and "Anti-gravity Technology". The import corrects them to "Underground City" and "Anti-Gravity Technology" (`NAME_CORRECTIONS`).

**Design notes:**
- **Import** (`uv run python -m tools.card_import [--download]`):
  - The page is parsed with `html.parser` into an element tree. A v1 card is an `<li class="filterDiv">` with a type class (automated, active, events, corporation) and the set class `standard` (base) or `corporate` (Corporate Era).
  - Corporations have no title on the page. Their names come from a table by the page's ids (`#CORP01`–`#CORP12`), and each is checked against the letters of its logo.
  - `check_v1_set` refuses a page that no longer gives #001–#208 and 12 Corporations. An unknown Requirement or Victory Points form stops the import and names the card.
- **Printed data:**
  - **Requirements:**
    - `{"type": "oxygen" | "temperature" | "oceans", "min" | "max": n}`;
    - `{"type": "tag", "tag", "min"}`;
    - `{"type": "production", "resource", "min"}`;
    - `{"type": "tiles", "tile", "owner": "you" | "anyone", "min"}`. Whose Tiles count comes from the text ("in play").
  - **Victory Points:** a number, `{"points", "per", "of"}` or `{"points", "at_least", "of"}` (Search for Life). `of` is one of `card_resource`, `tag`, `adjacent` (Tiles next to the card's Tile) or `tiles_in_play`.
  - **Tags:** in printed order, including the Event Tag on Events.
  - **Text:** the descriptions' paragraphs (two `<br>`s start a new one), without numbers drawn as icons. A card with no description takes the text of its middle part.
- **Engine types:** `Card`, `CardType`, `Tag`, `CardResource`, `Requirement` (with `Limit::Min`/`Max`), `Owner`, `VictoryPoints` (`Fixed`, `Per`, `AtLeast`) and `Counted`.
  - `face` is a `serde_json::Value`, read only by the GUI.
  - `Card` denies unknown fields.
  - `Resource` gained `Serialize`.
  - uv's cache keys now include `cards/*.json`, so editing the card file rebuilds the engine.
- **GUI** (`gui/src/cards/`):
  - `PrintedCard.tsx` draws the frame, title, cost, Tags and number from the printed data, and the middle part from the face.
  - `cardList.css` holds the card list stylesheet's 78 rules the v1 cards use, scoped under `.printed-card`, plus a reset of the GUI's `border-box` sizing and light text colour.
  - `CardGallery.tsx` filters by type and Tag (a card must have every selected Tag). Hovering enlarges a card ×1.5 in place, and clicking shows it as large as the window allows; Escape puts it back, then closes the gallery.
  - `CardsButton.tsx` is the shared Cards button.
- **Mismatch report** (`uv run python -m tools.card_mismatches [--download]`, written to `docs/card-mismatches.md`):
  - It pairs Project Cards by number and Corporations by name.
  - It compares Corporate Era (from the open-source manifests), type, cost, Tags (in any order, with the Event Tag the open-source game leaves out added back), Requirements (in any order) and Victory Points.
  - **Result: no differences**, so there were no disputes to settle. Search for Life is the only card not compared, because the open-source game works out its points in code: 3 Victory Points with at least one science resource, which matches ours.
  - Breaking our data on purpose (costs +1, a Tag removed, Victory Points cleared) shows 220, 193 and 82 differences, so the comparison is real.
- **Sizes:** the card file is 218 KB, the snapshot 724 KB and the icons 917 KB. `card_catalog()` takes 5 ms the first time and 2.5 ms after that.
- **Browser check** (1440×900, against the live card list page):
  - For all 220 cards, every element's position, size, computed style (images, colours, fonts, filters, shadows, transforms, the frame's `::before` and the Corporate Era `::after`) and own text match exactly.
  - Ten cards were also compared side by side: #005, #008, #009, #027, #058, #095, #128 and #195, plus CrediCor and Saturn Systems. That covers Automated, Active, Event and Corporation cards, a long title and the Corporate Era icon.
  - The filters, search, hover, click, Escape and the Cards buttons were checked by hand.
- **Benchmark** (power-saver profile, on mains): 188,779 Games per second on 16 processes and 17,705 in 1. Copies take 0.18, 0.31 and 0.63 µs. All are unchanged from ticket 06.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Duplication:
    - the tools share `PROJECT` and `fetch`;
    - `_tags` uses `_named`;
    - one `_v1_cards` replaces two helpers;
    - comments are stripped from CSS in one place;
    - the Cards button is one component.
  - Names:
    - `Element.all` became `outermost`;
    - the server's `card_catalog` became `card_catalog_message`;
    - `drawn` became `faceElement`, with a doc comment;
    - `resource_type` became `card_resource` (the glossary avoids "resource" for Card Resources).
  - Tests:
    - the check that the engine holds the import of the snapshot moved to `tests/tools/`, so `tests/cards/` goes through `tm_engine` only;
    - the copy test no longer depends on #001's cost;
    - the open-source "Capital" test became a made-up card.
  - A named margin constant, fuller docstrings, and lines wrapped to the house's 120 columns.
  - The spec review's point that names were compared without regard to case led to the two name corrections.
- Left as is:
  - `"special"` and `{"unknown": …}` in the mismatch parser. They let the report show a form it can't read instead of stopping, and they are documented.
  - `Comparison.not_compared` holds sentences.
  - **Beyond the ticket text:**
    - a name-or-number search in the gallery;
    - the report also compares type and Corporate Era, and has a `--commit` option;
    - the README's Credits section;
    - Escape handling;
    - the gallery's card count.

**Open points:**
- **Ticket 08:**
  - `Card` denies unknown fields. Declare each hand-written field (effect data) in `engine/src/cards.rs` before adding it to `cards.json`, or the catalog panics on its first read. The catalog tests catch this.
  - Events list the Event Tag among their Tags, as printed; the open-source game leaves it out. Decide whether it counts wherever Tags are counted.
  - Name cards by their `id` in Option details and Scenarios.
- **Ticket 21:** Corporations' starting MegaCredits, Resources and Production are only in their `text`. Once effect data adds them, the report can compare the open-source game's `startingMegaCredits`.
- **`text` on icon-only cards** is thin:
  - Protected Habitats ends at "…MAY NOT REMOVE YOUR";
  - Interstellar Colony Ship and Trans-Neptune Probe have none;
  - five cards keep the card list's capitalised icon-row wording.

  The GUI draws the face, so this matters only for later uses such as the game log or the AI.
- **Names:** the report compares names without regard to case or punctuation, since the open-source files give only constants such as `UNDERGROUND_CITY`.
- **Public release** (ADR 0003): the snapshot and icons are BSD-3-Clause, which needs the licence text if redistributed. The Prototype font is free for personal use only.
- **Ticket 23:** at 1440×900 the Game page overflows by 20 px when the status bar's Options wrap onto a second line (Generation 1, 42 MegaCredits). This was there before this ticket.
- **Glossary:** "Card catalog" was added to CONTEXT.md.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
