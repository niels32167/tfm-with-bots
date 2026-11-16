//! Prelude Cards at setup (ADR 0011), in a Game with the `prelude` setting on: each Player is dealt 4
//! and keeps 2, choosing them with their Corporation and the cards they buy. Like those choices they stay
//! hidden until every Player is done. Once every Corporation is revealed and every card paid for, each
//! Player in player order plays both of theirs, in the order they choose, before Generation 1's Action
//! phase. A Prelude Card that can't be played is discarded instead, for 15 MegaCredits.

use crate::board::TileKind;
use crate::card_set::CardSet;
use crate::cards::{CARD_CATALOG, CATALOG_CARDS, FIRST_PRELUDE_CARD, PRELUDE_CARDS, Reveal};
use crate::expenses::Expense;
use crate::game::{DecisionOption, Game, MAX_OCEANS, Phase, Waiting};
use crate::log::LogEvent;

/// How many Prelude Cards each Player is dealt at setup.
pub const PRELUDE_CARDS_DEALT: usize = 4;
/// How many of them each Player keeps.
pub const PRELUDE_CARDS_KEPT: usize = 2;
/// What a Player gains for a Prelude Card they can't play, which they discard instead.
pub const MEGACREDITS_FOR_AN_UNPLAYABLE_PRELUDE_CARD: i32 = 15;

const _: () = assert!(PRELUDE_CARDS <= 64, "a PreludeSet has room for every Prelude Card");

/// A set of Prelude Cards, one bit for each. Smaller than a `CardSet`, which every Player would
/// otherwise carry twice more, so copying a Game stays cheap (ADR 0004). Its cards come out in
/// card-number order (ADR 0010).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct PreludeSet {
    bits: u64,
}

impl PreludeSet {
    pub fn insert(&mut self, card: usize) {
        self.bits |= bit(card);
    }

    pub fn remove(&mut self, card: usize) {
        self.bits &= !bit(card);
    }

    pub fn union(self, other: PreludeSet) -> PreludeSet {
        PreludeSet { bits: self.bits | other.bits }
    }

    /// The cards in this set but not in `other`.
    pub fn without(self, other: PreludeSet) -> PreludeSet {
        PreludeSet { bits: self.bits & !other.bits }
    }

    pub fn len(self) -> usize {
        self.bits.count_ones() as usize
    }

    pub fn is_empty(self) -> bool {
        self.bits == 0
    }

    /// The cards in card-number order.
    pub fn iter(self) -> impl Iterator<Item = usize> {
        let mut bits = self.bits;
        std::iter::from_fn(move || {
            (bits != 0).then(|| {
                let card = FIRST_PRELUDE_CARD + bits.trailing_zeros() as usize;
                bits &= bits - 1;
                card
            })
        })
    }
}

impl FromIterator<usize> for PreludeSet {
    fn from_iter<I: IntoIterator<Item = usize>>(cards: I) -> PreludeSet {
        let mut set = PreludeSet::default();
        for card in cards {
            set.insert(card);
        }
        set
    }
}

fn bit(card: usize) -> u64 {
    assert!((FIRST_PRELUDE_CARD..CATALOG_CARDS).contains(&card), "card {card} is no Prelude Card");
    1 << (card - FIRST_PRELUDE_CARD)
}

/// A Player's Prelude Cards: at setup those dealt to them and those of them they have kept so far,
/// then those they kept and have still to play.
#[derive(Clone, Copy, Debug, Default)]
pub struct PreludeCards {
    pub dealt: PreludeSet,
    pub kept: PreludeSet,
}

impl PreludeCards {
    /// Whether the Player still has one to keep: they were dealt some, as a Player of a Game with
    /// Prelude is, and kept fewer than 2.
    pub fn keeping_due(self) -> bool {
        !self.dealt.is_empty() && self.kept.len() < PRELUDE_CARDS_KEPT
    }
}

impl Game {
    /// Each Player, in player order from the first player, is dealt their Prelude Cards from the
    /// shuffled Prelude Cards. Those left over are the Prelude deck; those not kept go back in the box.
    pub(crate) fn deal_prelude_cards(&mut self) {
        let cards = self.dealing_order(FIRST_PRELUDE_CARD..CATALOG_CARDS, |deal| &deal.prelude_cards);
        let mut dealing = cards.chunks(PRELUDE_CARDS_DEALT);
        for player in self.player_order() {
            let dealt = dealing.next().expect("there are enough Prelude Cards for 5 Players");
            assert_eq!(dealt.len(), PRELUDE_CARDS_DEALT, "there are enough Prelude Cards for 5 Players");
            self.players[player].prelude_cards.dealt = dealt.iter().copied().collect();
        }
        self.prelude_deck = dealing.flatten().copied().collect();
        self.log.push(LogEvent::PreludeCardsDealt);
    }

    /// The current Player may keep any Prelude Card dealt to them that they haven't kept.
    pub(crate) fn prelude_keeping_options(&self) -> Vec<DecisionOption> {
        let cards = self.players[self.current_player].prelude_cards;
        cards.dealt.without(cards.kept).iter().map(DecisionOption::KeepPreludeCard).collect()
    }

    /// The current Player keeps `card`, and keeps another, or goes on to buy cards.
    pub(crate) fn keep_prelude_card(&mut self, card: usize) {
        self.waiting = None;
        self.players[self.current_player].prelude_cards.kept.insert(card);
        self.buy_more_or_be_done();
    }

    /// The Prelude Cards `player` was dealt and didn't keep go back in the box.
    pub(crate) fn put_back_prelude_cards_not_kept(&mut self, player: usize) {
        self.players[player].prelude_cards.dealt = PreludeSet::default();
    }

    /// After setup, each Player in player order plays their Prelude Cards; then Generation 1's Action
    /// phase begins.
    pub(crate) fn begin_playing_prelude_cards(&mut self) {
        self.phase = Phase::PreludeCards;
        self.log.push(LogEvent::PreludeCardsPlayed);
        self.offer_prelude_cards_from(0);
    }

    /// Hands playing Prelude Cards to the first Player with any left, looking from index `start` in
    /// player order (0 is the first player). Once nobody has, the Action phase begins.
    pub(crate) fn offer_prelude_cards_from(&mut self, start: usize) {
        match self.first_in_player_order_who(start, |game, player| {
            !game.players[player].prelude_cards.kept.is_empty()
        }) {
            Some(player) => {
                self.current_player = player;
                self.play_next_prelude_card();
            }
            None => self.begin(self.generation, self.first_player),
        }
    }

    /// Once a Prelude Card is done, the current Player plays their next: with two left they choose
    /// which, and the last they play without a Decision. With none left, the next Player plays theirs.
    /// Played as a first action (Valley Trust), the Action ends instead.
    pub(crate) fn play_next_prelude_card(&mut self) {
        if self.phase != Phase::PreludeCards {
            return self.finish_action();
        }
        let kept = self.players[self.current_player].prelude_cards.kept;
        match kept.len() {
            0 => self.offer_prelude_cards_from(self.index_in_player_order() + 1),
            1 => self.play_prelude_card(kept.iter().next().expect("one is left")),
            _ => {}
        }
    }

    /// The current Player may play either Prelude Card they have left first.
    pub(crate) fn prelude_playing_options(&self) -> Vec<DecisionOption> {
        let kept = self.players[self.current_player].prelude_cards.kept;
        kept.iter().map(DecisionOption::PlayPreludeCard).collect()
    }

    /// Whether `player` can play the Prelude Card `card`: carry out its effects, as for a Project
    /// Card, and pay its price once they are done, counting what its Ocean gains for the Oceans next
    /// to it. A Prelude Card has no cost and no Requirements.
    pub fn can_play_prelude_card(&self, player: usize, card: usize) -> bool {
        let effects = CARD_CATALOG[card].implemented_effects();
        self.can_carry_out(player, effects)
            && self.can_make_a_production_change(player, card)
            && self.spendable_megacredits(player) + self.most_megacredits_from_ocean(player, card)
                >= prelude_card_price(card)
            && (effects.next_card.is_none() || self.could_play_a_card_for(player, card))
    }

    /// Whether `player` could play a card from their hand for `card`, a Prelude Card that plays one,
    /// once it is in play: with its Tags and Production, and with what it changes about that card.
    /// Tried on a copy of the Game, as only the engine itself sees it (ADR 0013 is about Controllers).
    fn could_play_a_card_for(&self, player: usize, card: usize) -> bool {
        let mut trying = self.clone();
        trying.players[player].played.insert(card);
        trying.players[player].next_card = Some(card);
        trying.change_productions(player, CARD_CATALOG[card].implemented_effects().production);
        trying.players[player].hand.iter().any(|in_hand| trying.can_play(player, in_hand))
    }

    /// The most MegaCredits `player` may gain for the Oceans next to the Ocean of `card`, a Prelude
    /// Card (Aquifer Turbines): 0 for a card without one, or once all 9 are placed.
    fn most_megacredits_from_ocean(&self, player: usize, card: usize) -> i32 {
        let tiles = &CARD_CATALOG[card].implemented_effects().tiles;
        let Some(&placement) = tiles.iter().find(|placement| placement.tile == TileKind::Ocean) else {
            return 0;
        };
        if self.board.oceans() >= MAX_OCEANS {
            return 0;
        }
        let areas = self.board.areas_for(placement, player).into_iter();
        areas.map(|area| self.megacredits_from_oceans_next_to(area)).max().unwrap_or(0)
    }

    /// Whether the current Player may place the Ocean they are placing on `area`: unless it is the
    /// Ocean of the Prelude Card they are playing, which they may place only where they can still pay
    /// the card's price with what that gains them (Aquifer Turbines).
    pub(crate) fn ocean_pays_for_prelude_card(&self, area: usize) -> bool {
        let Some(card) = self.playing_prelude_card else { return true };
        self.placing_for.is_none_or(|tiles| tiles.card != card)
            || self.spendable_megacredits(self.current_player) + self.megacredits_from_oceans_next_to(area)
                >= prelude_card_price(card)
    }

    /// The current Player plays `card`, one of their Prelude Cards: it joins their played cards and
    /// its effects are carried out, as a Project Card's are. If they can't play it, they discard it and
    /// gain 15 MegaCredits instead. One of those drawn for a first action (Valley Trust) is played the
    /// same way, and the others are discarded, unseen by the other Players.
    pub(crate) fn play_prelude_card(&mut self, card: usize) {
        let player = self.current_player;
        if let Some(Waiting::DrawnPreludeCards) = self.waiting {
            self.waiting = None;
            self.players[player].prelude_cards.kept = PreludeSet::default();
        }
        self.players[player].prelude_cards.kept.remove(card);
        if !self.can_play_prelude_card(player, card) {
            self.players[player].resources.megacredits += MEGACREDITS_FOR_AN_UNPLAYABLE_PRELUDE_CARD;
            self.log.push(LogEvent::DiscardedUnplayablePreludeCard { player, card });
            return self.play_next_prelude_card();
        }
        self.log.push(LogEvent::PlayedPreludeCard { player, card });
        // Playing it uses up what an Event did to the next card played (see docs/rules-notes.md).
        self.players[player].next_card = None;
        self.playing_prelude_card = Some(card);
        self.put_into_play(player, card);
    }

    /// Once the Prelude Card being played has carried out its other effects, its Player reveals cards
    /// until they find those it asks for, pays its price, or plays a card from their hand, as it says;
    /// then they play their next. No Prelude Card does more than one of these.
    pub(crate) fn finish_prelude_card(&mut self) {
        let Some(card) = self.playing_prelude_card.take() else {
            return self.play_next_prelude_card();
        };
        let effects = CARD_CATALOG[card].implemented_effects();
        if let Some(reveal) = effects.reveal {
            self.reveal_until_found(self.current_player, reveal);
        }
        if effects.pay.is_some() {
            return self.spend_on(Expense::PreludeCard(card));
        }
        if effects.next_card.is_some() {
            self.players[self.current_player].next_card = Some(card);
            return self.wait_on(Waiting::CardFromHand);
        }
        self.play_next_prelude_card();
    }

    /// `player` reveals cards from the top of the deck until they find `reveal.count` with its Tag,
    /// and takes those into their hand. The rest go on the discard pile once they are done, so when
    /// the deck runs out, the discard pile shuffled into a new deck holds none of them. Once both are
    /// empty, they take those found so far.
    fn reveal_until_found(&mut self, player: usize, reveal: Reveal) {
        let mut found = 0;
        let mut not_taken = CardSet::default();
        while found < reveal.count {
            let Some(card) = self.draw_cards(player, 1).iter().next() else { break };
            let taken = CARD_CATALOG[card].has_tag(reveal.tag);
            self.log.push(LogEvent::RevealedLookingForTag {
                player,
                card,
                taken_for: taken.then_some(reveal.tag),
            });
            if taken {
                self.players[player].hand.insert(card);
                found += 1;
            } else {
                not_taken.insert(card);
            }
        }
        self.discard = self.discard.union(not_taken);
    }

    /// `player` draws up to `count` Prelude Cards at random from the Prelude deck, as from a shuffled
    /// deck, and holds them to play one (Valley Trust's first action). With a deal, they are the next it names.
    pub(crate) fn draw_prelude_cards(&mut self, player: usize, count: usize) {
        let deck = self.prelude_deck;
        let mut cards = self.dealing_order(deck.iter(), |deal| &deal.prelude_cards);
        cards.truncate(count);
        for &card in &cards {
            self.prelude_deck.remove(card);
        }
        self.players[player].prelude_cards.kept = cards.iter().copied().collect();
        self.log.push(LogEvent::DrewPreludeCards { player, count: cards.len() });
    }

    /// If the current Player still has a Prelude Card to keep, the Game waits on which.
    pub(crate) fn offer_keeping_prelude_card(&mut self) {
        if self.players[self.current_player].prelude_cards.keeping_due() {
            self.wait_on(Waiting::PreludeCards);
        }
    }
}

/// The MegaCredits `card`, a Prelude Card, costs once its other effects are done ("Pay 6 M€"), which
/// Helion's heat may pay: 0 for most.
pub(crate) fn prelude_card_price(card: usize) -> i32 {
    CARD_CATALOG[card].implemented_effects().pay.map_or(0, |price| price.megacredits)
}

/// The ids of Prelude Cards, for the view.
pub(crate) fn prelude_card_ids(cards: PreludeSet) -> Vec<&'static str> {
    cards.iter().map(|card| CARD_CATALOG[card].id.as_str()).collect()
}
