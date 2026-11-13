"""Rebuilding each Player's hand from a Recorded Game's slim moves (ticket 09), one test per trait of the
logs. The moves are hand-written in the slim shape: Players by place, "Player 1"/"Player 2" in text, and
each move's whole game state (as expand_moves gives them)."""

from typing import Any

from ai.recorded_games.hands import HandReader


def move(
    number: int, player: int | None, description: str, *, generation: int = 1, action: str = "other", **fields: Any
) -> dict[str, Any]:
    """A slim move, its game state holding only the Generation unless hands= gives both Hand Counters."""
    counters = fields.pop("hands", None)
    state: dict[str, Any] = {"generation": generation}
    if counters is not None:
        state["player_trackers"] = {str(place): {"Hand Counter": count} for place, count in enumerate(counters)}
    return {
        "move_number": number,
        "player": player,
        "action_type": action,
        "description": description,
        "game_state": state,
        **fields,
    }


def read(moves: list[dict[str, Any]], *, prelude: bool = True) -> HandReader:
    reader = HandReader(prelude=prelude)
    for entry in moves:
        reader.read(entry)
    return reader


def first_play(number: int, player: int, card: str, generation: int = 1) -> dict[str, Any]:
    return move(
        number,
        player,
        f"Player {player + 1} plays card {card}",
        generation=generation,
        action="play_card",
        card_played=card,
    )


SETUP_KEEP = move(
    2,
    0,
    "Player 1 keeps 5 cards: Vitor, Business Network, Fish, Donation, Research Network",
    cards_kept={"0": ["Vitor", "Business Network", "Fish", "Donation", "Research Network"]},
)


def test_the_setup_keep_puts_all_but_the_corporation_in_hand():
    reader = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant")])

    hand = reader.hands[0]
    assert sorted(hand.cards) == ["business_network", "donation", "fish", "research_network"]
    assert hand.size == 4
    assert hand.exact


def test_a_play_named_only_in_its_field_leaves_the_hand_and_the_keep_logged_with_it_is_a_draw():
    research_network = move(
        3,
        0,
        "Player 1 keeps 3 cards: Electro Catapult, Birds, Media Archives | Player 1 increases M€ Production by 1",
        action="play_card",
        card_played="Research Network",
        cards_kept={"0": ["Electro Catapult", "Birds", "Media Archives"]},
    )

    hand = read([SETUP_KEEP, research_network]).hands[0]

    assert sorted(hand.cards) == ["birds", "business_network", "donation", "electro_catapult", "fish", "media_archives"]
    assert hand.size == 6


def test_a_play_in_the_description_alone_counts_and_goes_to_the_player_it_names():
    credited_to_the_other = move(3, 1, "Player 1 pays 3 M€ | Player 1 plays card Fish", action="play_card")

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), credited_to_the_other]).hands[0]

    assert sorted(hand.cards) == ["business_network", "donation", "research_network"]


def test_a_draw_adds_to_the_hand_and_a_look_adds_only_the_card_kept():
    draw = move(4, 0, "Player 1 draws Pets", action="draw", cards_kept={"0": ["Pets"]})
    look = move(5, 0, "Player 1 draws Protected Habitats", action="draw", card_options={"0": ["Protected Habitats"]})
    keep = move(6, 0, "Player 1 keeps Protected Habitats | Player 1 pays 3 M€", action="buy_card")
    look_discarded = move(7, 0, "Player 1 draws Ice Asteroid", action="draw", card_options={"0": ["Ice Asteroid"]})

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), draw, look, keep, look_discarded]).hands[0]

    assert sorted(hand.cards) == [
        "business_network", "donation", "fish", "pets", "protected_habitats", "research_network",
    ]  # fmt: skip


def test_a_discard_that_names_no_card_shrinks_the_hand_but_leaves_which_cards_unknown():
    sell_patents = [
        move(4, 0, "Player 1 plays standard project Sell patents", action="standard_project"),
        move(5, 0, "Player 1 discards 2 card/s (Sell patents) | Player 1 gains 2 M€"),
    ]
    mars_university = move(6, 0, "Player 1 discards a card", reason="triggered effect of Mars University")

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), *sell_patents, mars_university]).hands[0]

    assert sorted(hand.cards) == ["business_network", "donation", "fish", "research_network"]
    assert hand.gone == 3
    assert hand.size == 1
    assert not hand.exact


OLD_SETUP = move(
    3,
    0,
    "You choose corporation Inventrix | You buy Farming | You buy Herbivores | You got Mining Operations"
    " | You got Research Network | Player 2 keeps 5 card/s | Player 2 chooses corporation CrediCor | Player 2 pays 15"
    " | Player 1 keeps 2 card/s | Player 1 chooses corporation Inventrix | Player 1 pays 6",
)


def test_old_logs_name_only_the_perspective_player_s_setup_and_count_the_other_s():
    reader = read([OLD_SETUP, first_play(4, 1, "Aquifer Turbines")])

    mine, theirs = reader.hands
    assert sorted(mine.cards) == ["farming", "herbivores", "mining_operations", "research_network"]
    assert mine.exact
    assert theirs.cards == {}
    assert theirs.unnamed == 6  # 5 Project Cards and 2 Prelude Cards, one of them played
    assert not theirs.exact


def test_an_old_draw_named_and_then_counted_is_one_draw_and_a_count_alone_adds_unnamed_cards():
    mine = move(5, 0, "Player 1 draws Big Asteroid, Cupola City | Player 1 draws 2 cards | Player 1 draw Undo")
    theirs = move(6, 1, "Player 2 draws 2 cards | Player 2 draw   (no undo beyond this point)")

    reader = read([OLD_SETUP, first_play(4, 1, "Aquifer Turbines"), mine, theirs])

    assert sorted(reader.hands[0].cards) == [
        "big_asteroid", "cupola_city", "farming", "herbivores", "mining_operations", "research_network",
    ]  # fmt: skip
    assert reader.hands[0].exact
    assert reader.hands[1].unnamed == 8


def test_a_card_already_in_hand_is_not_added_again_nor_a_relogged_setup_keep():
    relogged = move(
        3, 1, "Player 2 draws Mine | Player 1 draws 5 cards: Vitor, Business Network, Fish, Donation, Research Network",
        action="draw",
    )  # fmt: skip
    look = move(5, 0, "Player 1 draws 4 cards: A, B, Tropical Resort, Immigration Shuttles", action="play_card",
                card_options={"0": ["Tropical Resort", "Immigration Shuttles"]})  # fmt: skip
    one_kept = move(6, 0, "Player 1 keeps Immigration Shuttles")
    summary = move(7, 0, "Player 1 keeps 2 cards: Tropical Resort, Immigration Shuttles")

    reader = read([SETUP_KEEP, first_play(2, 1, "Biolabs"), relogged, look, one_kept, summary])

    assert sorted(reader.hands[0].cards) == [
        "business_network", "donation", "fish", "immigration_shuttles", "research_network", "tropical_resort",
    ]  # fmt: skip
    assert sorted(reader.hands[1].cards) == ["mine"]


def research(generation: int = 2) -> list[dict[str, Any]]:
    """Generation 2's Research phase from the newer logs, ending with Player 2's first action."""
    return [
        move(
            30, 0, "Player 1 drafts 4 cards: Industrial Center, Mars University, Great Dam, Noctis City"
            " | Player 2 drafts 4 cards: Release of Inert Gases, Small Animals, Ants, Research Coordination",
            generation=generation, action="pass",
        ),
        move(31, 0, "You draft Mars University", generation=generation, action="draft"),
        move(37, 1, "Player 2 keeps 2 cards: Research Coordination, Industrial Center | Player 2 pays 6 M€",
             generation=generation, action="buy_card"),
        move(38, 0, "Player 1 keeps 1 cards: Mars University | Player 2 keeps 2 cards: Industrial Center,"
             " Research Coordination | Player 1 pays 3 M€", generation=generation, action="buy_card"),
        move(39, 1, "Player 2 pays 7 Plant", generation=generation),
        move(40, 1, "Player 2 places Greenery on Tharsis Hex 2,5 (2,5)", generation=generation),
    ]  # fmt: skip


def test_research_buys_reach_the_hand_once_the_action_phase_begins():
    reader = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), *research()[:4]])
    assert sorted(reader.hands[1].cards) == []

    reader = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), *research()])

    assert sorted(reader.hands[0].cards) == [
        "business_network",
        "donation",
        "fish",
        "mars_university",
        "research_network",
    ]
    assert sorted(reader.hands[1].cards) == ["industrial_center", "research_coordination"]


def test_keeps_one_at_a_time_add_up_and_drafting_a_kept_card_takes_it_back():
    setup = [
        move(2, 0, "private: Player 1 chooses corporation Teractor and received 60 ME."),
        move(3, 0, "Player 1 keeps Sponsors | Player 1 pays 3 MC"),
        move(4, 0, "Player 1 keeps Power Grid | Player 1 pays 3 MC"),
        move(5, 0, "Player 1 keeps Mining Rights | Player 1 pays 3 MC"),
        move(6, 1, "Player 2 skips rest of actions"),
        move(7, 0, "Player 1 drafts Power Grid", action="draft"),
    ]

    hand = read([*setup, first_play(8, 1, "Pets")]).hands[0]

    assert sorted(hand.cards) == ["mining_rights", "sponsors"]


def test_after_a_cancel_the_next_keep_starts_again_and_a_take_back_drops_what_was_bought():
    cancelled = [
        *research()[:2],
        move(33, 1, "Player 2 keeps 2 cards: Ants, Small Animals", generation=2, action="buy_card"),
        move(34, 1, "Player 2 cancels their move", generation=2),
        move(35, 1, "Player 2 keeps Ants", generation=2, action="buy_card"),
        first_play(36, 1, "Ants", generation=2),
    ]
    taken_back = [
        move(2, 0, "You choose corporation Vitor | You buy Lava Flows | You buy Shuttles"),
        move(3, 0, "Player 1 takes back their move"),
        move(4, 0, "You choose corporation Vitor | You buy Shuttles"),
        move(5, 1, "Player 1 keeps 1 card/s | Player 1 chooses corporation Vitor | Player 2 keeps 1 card/s"),
    ]

    assert read([SETUP_KEEP, first_play(3, 1, "Biolabs"), *cancelled]).hands[1].cards == {}
    assert sorted(read([*taken_back, first_play(6, 1, "Mine")], prelude=False).hands[0].cards) == ["shuttles"]


def test_at_setup_the_deal_is_not_drawn_into_the_hand_but_point_luna_s_draw_is():
    setup = [
        move(1, 0, "Player 1 draws Restricted Area, Great Dam, Natural Preserve, Domed Crater, Greenhouses,"
             " Mining Area,"
             " Pets, Virus, Lunar Beam, Fish | Player 1 draws 10 cards | Player 2 draws 10 cards"),
        move(3, 0, "You choose corporation Point Luna | You buy Pets | Player 1 draws Methane From Titan"
             " | Player 1 keeps 1 card/s | Player 1 chooses corporation Point Luna | Player 1 draws 1 cards"
             " | Player 2 keeps 2 card/s"),
    ]  # fmt: skip

    reader = read([*setup, first_play(4, 1, "Mine")], prelude=False)

    assert sorted(reader.hands[0].cards) == ["methane_from_titan", "pets"]
    assert reader.hands[0].exact
    assert reader.hands[1].unnamed == 1


def test_a_setup_keep_logged_as_a_draw_is_the_keep():
    as_a_draw = move(3, 1, "Player 2 draws 3 cards: Point Luna, Bribed Committee, Business Empire", action="draw")

    assert sorted(read([as_a_draw, first_play(4, 0, "Mine")]).hands[1].cards) == ["bribed_committee", "business_empire"]


def test_old_looks_are_known_by_the_card_that_looks_and_how_many_cards_it_shows():
    business_contacts = [
        move(10, 0, "Player 1 pays 7 | Player 1 plays card Business Contacts | Player 1 triggered effect of Point Luna",
             action="play_card", card_played="Business Contacts"),
        move(11, 0, "Player 1 draws Inventors' Guild | Player 1 draws 1 cards"),  # Point Luna's draw comes first.
        move(12, 0, "Player 1 draws Caretaker Contract, Biomass Combustors, Cupola City, Sponsors"
             " | Player 1 draws 4 cards"),
        move(13, 0, "You keep Sponsors"),
        move(14, 0, "You keep Cupola City | Player 1 keeps 2 card/s"),
    ]  # fmt: skip
    inventors_guild = [
        move(15, 1, "Player 2 activates Inventors' Guild", action="activate_card"),
        move(16, 1, "Player 2 draws 1 cards | Player 2 draw Undo"),
        move(17, 1, "Player 2 skips rest of actions | Player 2 discard Undo"),
    ]

    reader = read([OLD_SETUP, first_play(4, 1, "Aquifer Turbines"), *business_contacts, *inventors_guild])

    assert sorted(reader.hands[0].cards) == [
        "cupola_city", "farming", "herbivores", "inventors_guild", "mining_operations", "research_network", "sponsors",
    ]  # fmt: skip
    assert reader.hands[0].exact
    assert reader.hands[1].unnamed == 6


def test_valley_trust_s_first_action_plays_a_prelude_card_straight_from_the_cards_it_shows():
    setup = move(3, 0, "Player 1 keeps 2 card/s | Player 1 chooses corporation Robinson Industries"
                 " | Player 2 keeps 4 card/s | Player 2 chooses corporation Valley Trust"
                 " | Player 2 pays 12")  # fmt: skip
    first_action = [
        move(12, 0, "Player 2 has a mandatory action to perform as a first action"),
        move(14, 1, "Player 2 draws 3 cards"),
        first_play(15, 1, "Great Aquifer"),
    ]

    reader = read([setup, first_play(4, 1, "Metals Company"), *first_action])

    assert reader.hands[1].unnamed == 5  # 4 Project Cards and 2 Prelude Cards, Metals Company played


def test_cards_revealed_with_the_tag_sought_go_to_hand_except_search_for_life_s():
    acquired_space_agency = move(
        9, 0, "Player 1 reveals Herbivores: it does not have a Space tag | Player 1 reveals Comet: it has a Space tag"
        " | Player 1 reveals Toll Station: it has a Space tag",
    )  # fmt: skip
    search_for_life = move(
        10,
        0,
        "Player 1 activates Search For Life | Player 1 pays 1 | Player 1 reveals Insects:"
        " it has a Microbe tag | Player 1 adds Science to Search For Life",
        action="activate_card",
    )

    hand = read([OLD_SETUP, first_play(4, 1, "Aquifer Turbines"), acquired_space_agency, search_for_life]).hands[0]

    assert sorted(hand.cards) == [
        "comet",
        "farming",
        "herbivores",
        "mining_operations",
        "research_network",
        "toll_station",
    ]


def test_a_play_that_names_no_card_leaves_one_unnamed_and_an_unplayable_prelude_card_is_discarded():
    unplayable = move(4, 0, "Player 1 cannot play card Donation, player discards it and gains compensation"
                      " (designer ruling) | Player 1 gains 15 M€")  # fmt: skip
    unnamed_play = move(5, 0, "Player 1 pays 4 MC", action="play_card")

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), unplayable, unnamed_play]).hands[0]

    assert sorted(hand.cards) == ["business_network", "fish", "research_network"]
    assert hand.gone == 1
    assert hand.size == 2


def test_a_mars_university_discard_the_log_drops_is_inferred_from_its_draw():
    mars_university = [
        move(18, 0, "Player 1 pays 6 M€ | Player 1 plays card Fish | Player 1 triggered effect of Mars University",
             action="play_card", card_played="Fish", reason="triggered effect of Mars University"),
        move(19, 0, "Player 1 other", reason="triggered effect of Mars University"),
        move(20, 0, "Player 1 draws Gene Repair", action="draw", cards_kept={"0": ["Gene Repair"]}),
    ]  # fmt: skip
    logged = [
        move(21, 0, "Player 1 pays 1 M€ | Player 1 plays card Donation"
             " | Player 1 triggered effect of Mars University",
             action="play_card", card_played="Donation"),
        move(22, 0, "Player 1 other", reason="triggered effect of Mars University"),
        move(23, 0, "Player 1 discards 1 card/s (triggered effect of Mars University)",
             reason="triggered effect of Mars University"),
        move(24, 0, "Player 1 draws Space Station", action="draw", cards_kept={"0": ["Space Station"]}),
    ]  # fmt: skip

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), *mars_university, *logged]).hands[0]

    assert sorted(hand.cards) == ["business_network", "gene_repair", "research_network", "space_station"]
    assert hand.gone == 2
    assert hand.size == 2


def test_each_play_is_counted_as_found_by_name_from_an_unnamed_card_or_missing():
    plays = [
        first_play(5, 0, "Farming"),
        first_play(6, 0, "Comet"),  # Not in the hand.
        first_play(7, 1, "Comet"),  # One of the unnamed cards.
        first_play(8, 1, "CrediCor"),  # A Corporation is never in the hand.
    ]

    reader = read([OLD_SETUP, *plays])

    assert reader.plays[0] == {"named": 1, "unnamed": 0, "missing": 1}
    assert reader.plays[1] == {"named": 0, "unnamed": 1, "missing": 0}
    assert [(p.move_number, p.player, p.card, p.found) for p in reader.played] == [
        (5, 0, "farming", "named"), (6, 0, "comet", "missing"), (7, 1, "comet", "unnamed"),
    ]  # fmt: skip
    assert reader.hands[1].unnamed == 6


def test_the_hand_counter_is_checked_only_where_it_just_changed_at_its_player_s_own_play():
    def play(number: int, card: str, hands: tuple[int, int], text: bool = True) -> dict[str, Any]:
        description = f"Player 1 plays card {card}" if text else "Player 1 keeps Birds"
        return move(number, 0, description, action="play_card", card_played=card, hands=hands)

    moves = [
        move(2, 0, SETUP_KEEP["description"], hands=(0, 0)),
        play(3, "Fish", (0, 0)),  # The counter has not started.
        play(4, "Donation", (2, 0)),  # Changed at a play: checked, and the rebuild agrees (Fish, Donation gone).
        move(5, 0, "Player 1 draws Pets", action="draw", cards_kept={"0": ["Pets"]}, hands=(2, 0)),  # Stale at draws.
        play(6, "Pets", (2, 0)),  # Unchanged: not checked.
        play(7, "Research Network", (3, 0), text=False),  # Its "plays card" line is missing: stale.
        play(8, "Business Network", (5, 0)),  # Checked: the rebuild is 1, the counter 5.
    ]

    assert [(c.move_number, c.player, c.rebuilt, c.counter) for c in read(moves).checks] == [(4, 0, 2, 2), (8, 0, 1, 5)]


def test_card_lines_about_a_player_by_another_name_are_counted_as_unread():
    renamed = move(5, 1, "Old Name draws 2 cards: Comet, Mine | Old Name gains 2 M€ | Player 2 draws Pets",
                   action="draw")  # fmt: skip

    reader = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), renamed])

    assert reader.unread == 1
    assert sorted(reader.hands[1].cards) == ["pets"]


def test_a_dropped_mars_university_discard_is_inferred_without_a_reason_when_nothing_else_could_draw():
    def science_play(number: int, card: str, triggers: str) -> dict[str, Any]:
        return move(number, 0, f"Player 1 plays card {card} | {triggers}", action="play_card", card_played=card)

    alone = [
        science_play(18, "Fish", "Player 1 triggered effect of Mars University"),
        move(19, 0, "Player 1 other"),
        move(20, 0, "Player 1 other"),
        move(21, 0, "Player 1 draws Gene Repair | Player 1 gains 1 Steel Exchange Rate", action="draw"),
    ]
    with_olympus_conference = [
        science_play(22, "Donation", "Player 1 triggered effect of Olympus Conference"
                     " | Player 1 triggered effect of Mars University"),
        move(23, 0, "Player 1 other"),
        move(24, 0, "Player 1 draws Space Station", action="draw"),  # Olympus Conference's, Mars University declined.
    ]  # fmt: skip

    hand = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), *alone, *with_olympus_conference]).hands[0]

    assert hand.gone == 1
    assert hand.size == 3  # 4 kept, Fish and Donation played, 1 discarded, Gene Repair and Space Station drawn


def test_with_resync_a_fresh_hand_counter_corrects_the_size_and_marks_the_hand_inexact():
    def play(number: int, card: str, counter: int) -> dict[str, Any]:
        return move(number, 0, f"Player 1 plays card {card}", action="play_card", card_played=card, hands=(counter, 0))

    moves = [
        move(2, 0, SETUP_KEEP["description"], hands=(0, 0)),
        play(3, "Fish", 3),
        move(4, 0, "Player 1 other", hands=(3, 0)),  # A discard the log dropped.
        play(5, "Donation", 1),  # The rebuild says 2: 1 card went without a line.
        move(6, 0, "Player 1 draws 2 cards", hands=(1, 0)),  # Old wording: 2 unnamed cards.
        play(7, "Mine", 3),  # One of them. The rebuild says 2 after correcting, 3 without: 1 came without a line.
    ]

    plain, resynced = HandReader(prelude=True), HandReader(prelude=True, resync=True)
    for entry in moves:
        plain.read(entry)
        resynced.read(entry)

    assert [c.rebuilt for c in plain.checks] == [3, 2, 3]  # The dropped discard is made up for by chance.
    assert [c.rebuilt for c in resynced.checks] == [3, 2, 2]  # Each check is taken before correcting.
    assert resynced.hands[0].size == 3
    assert (resynced.hands[0].gone, resynced.hands[0].unnamed) == (1, 2)
    assert resynced.resynced == 2


def test_a_play_in_a_move_without_a_player_goes_to_whom_the_description_names_or_is_unread():
    named = move(4, None, "Player 1 plays card Fish", action="play_card", card_played="Fish")
    nobody = move(5, None, "Auto passing on next turn", card_played="Donation")
    del named["player"], nobody["player"]  # The slim moves leave out a Player of None.

    reader = read([SETUP_KEEP, first_play(3, 1, "Smelting Plant"), named, nobody])

    assert sorted(reader.hands[0].cards) == ["business_network", "donation", "research_network"]
    assert reader.unread == 1


def test_a_look_that_never_shows_its_cards_does_not_swallow_a_later_draw_of_that_many():
    no_look_logged = move(15, 0, "Player 1 activates Inventors' Guild", action="activate_card")
    later_draw = move(
        16, 0, "Player 1 plays card Farming | Player 1 triggered effect of Point Luna | Player 1 draws 1 cards",
        action="play_card", card_played="Farming",
    )  # fmt: skip

    hand = read([OLD_SETUP, first_play(4, 1, "Aquifer Turbines"), no_look_logged, later_draw]).hands[0]

    assert hand.unnamed == 1


def test_a_buy_cancelled_and_not_kept_again_still_reaches_the_hand():
    # Measured on all 59,039 Games: taking such a buy as nothing bought left 54% of Games with every Hand Counter
    # check exact, against 97% keeping it. "Cancels their move" there undoes something else.
    cancelled = [
        *research()[:2],
        move(33, 1, "Player 2 keeps 2 cards: Ants, Small Animals", generation=2, action="buy_card"),
        move(34, 1, "Player 2 cancels their move", generation=2),
        first_play(36, 1, "Ants", generation=2),
    ]

    assert sorted(read([SETUP_KEEP, first_play(3, 1, "Biolabs"), *cancelled]).hands[1].cards) == ["small_animals"]
