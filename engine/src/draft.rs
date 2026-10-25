//! The Draft (on by default, ADR 0003): from Generation 2, the Research phase deals each Player
//! their cards to draft instead of to buy from. Each keeps one and passes the rest to their
//! neighbour, until every card is kept; then they buy from the cards they kept.
//!
//! Picks are simultaneous at the table. The engine asks one Player at a time, in player order
//! from the first player (ADR 0002), and the cards passed on reach their new owner only once
//! everyone has kept one, so no Player sees what another kept.

use crate::card_flow::RESEARCH_CARDS;
use crate::card_set::CardSet;
use crate::game::{DecisionOption, Game, Phase};
use crate::log::LogEvent;

/// What a Player is drafting: the cards they pick one from now and pass the rest on, and the
/// cards they have kept so far.
#[derive(Clone, Copy, Debug, Default)]
pub struct Drafting {
    pub picking_from: CardSet,
    pub kept: CardSet,
}

/// Cards a Player passed on in the Draft: in `generation`, `player` passed `cards` to `to`. A
/// Player knows the cards they passed for the rest of the Game.
#[derive(Clone, Copy, Debug)]
pub struct DraftPass {
    pub generation: u32,
    pub player: usize,
    pub to: usize,
    pub cards: CardSet,
}

impl Game {
    /// The Research phase with the Draft: each Player, in player order from the first player, is
    /// dealt their cards to draft.
    pub(crate) fn begin_draft(&mut self) {
        self.phase = Phase::Draft;
        self.log.push(LogEvent::ResearchPhaseWithDraft {
            players: self.players.len(),
            clockwise: self.passes_clockwise(),
        });
        for player in self.player_order() {
            self.players[player].drafting.picking_from = self.draw_cards(player, RESEARCH_CARDS);
        }
        self.begin_picking();
    }

    /// Whether cards are passed clockwise in this Generation: in even Generations they are, and
    /// counter-clockwise in odd ones.
    pub fn passes_clockwise(&self) -> bool {
        self.generation.is_multiple_of(2)
    }

    /// Whom `player` passes cards to in this Generation's Draft: clockwise, the next Player, as
    /// the Turns go; counter-clockwise, the one before.
    pub fn passing_to(&self, player: usize) -> usize {
        let count = self.players.len();
        if self.passes_clockwise() { (player + 1) % count } else { (player + count - 1) % count }
    }

    /// Every Player keeps one of the cards they hold: one with a single card left keeps it, since
    /// there is nothing to choose, and the others pick in player order. Once every card is kept,
    /// the Draft is over.
    fn begin_picking(&mut self) {
        for own in &mut self.players {
            if own.drafting.picking_from.len() == 1 {
                own.drafting.kept = own.drafting.kept.union(own.drafting.picking_from);
                own.drafting.picking_from = CardSet::default();
            }
        }
        if self.players.iter().all(|own| own.drafting.picking_from.is_empty()) {
            self.finish_draft();
        } else {
            self.offer_drafting_from(0);
        }
    }

    /// Whether `player` has a card to pick: one of two or more.
    fn can_draft(&self, player: usize) -> bool {
        self.players[player].drafting.picking_from.len() >= 2
    }

    /// The current Player may keep any of the cards they are picking from.
    pub(crate) fn drafting_options(&self) -> Vec<DecisionOption> {
        let picking_from = self.players[self.current_player].drafting.picking_from;
        picking_from.iter().map(DecisionOption::DraftCard).collect()
    }

    /// The current Player keeps `card`, and the next one picks.
    pub(crate) fn draft(&mut self, card: usize) {
        let drafting = &mut self.players[self.current_player].drafting;
        drafting.picking_from.remove(card);
        drafting.kept.insert(card);
        self.offer_drafting_from(self.index_in_player_order() + 1);
    }

    /// Hands the pick to the first Player who has one, looking from index `start` in player order
    /// (0 is the first player). Once everyone has picked, the cards left are passed on.
    fn offer_drafting_from(&mut self, start: usize) {
        match self.first_in_player_order_who(start, Game::can_draft) {
            Some(player) => self.current_player = player,
            None => self.pass_drafted_cards(),
        }
    }

    /// Every Player passes the cards they did not keep to their neighbour, all at once, and each
    /// picks again from the cards passed to them.
    fn pass_drafted_cards(&mut self) {
        let passed: Vec<CardSet> = self.players.iter().map(|own| own.drafting.picking_from).collect();
        for (player, cards) in passed.into_iter().enumerate() {
            let to = self.passing_to(player);
            self.players[to].drafting.picking_from = cards;
            if !cards.is_empty() {
                self.draft_passes.push(DraftPass { generation: self.generation, player, to, cards });
            }
        }
        self.begin_picking();
    }

    /// Every card is kept: each Player may buy any of the cards they kept.
    fn finish_draft(&mut self) {
        for own in &mut self.players {
            own.buying.dealt = std::mem::take(&mut own.drafting).kept;
        }
        self.phase = Phase::Research;
        self.log.push(LogEvent::DraftIsOver);
        self.offer_buying_from(0);
    }
}
