//! The cards whose effects are Rust code of their own rather than effect data (ADR 0009). Each
//! is named by its index in the card catalog, its printed number minus 1, which the catalog
//! checks against the card's id when it is read.

use crate::cards::{CARD_CATALOG, CardType, Tag};
use crate::game::Game;
use crate::log::LogEvent;

/// #086 Robotic Workforce: "Duplicate only the production box of one of your building cards."
pub const ROBOTIC_WORKFORCE: usize = 85;

/// Every card with code here, and its id.
pub const CARDS_WITH_CODE: [(usize, &str); 1] = [(ROBOTIC_WORKFORCE, "robotic_workforce")];

impl Game {
    /// The cards whose production box `player` may copy with Robotic Workforce: their own played
    /// Automated and Active cards with a building Tag and a production box they can carry out in
    /// full. A card's production box is its fixed and per-Tag Production data; a test checks that
    /// against every printed box.
    pub(crate) fn copyable_production_boxes(&self, player: usize) -> impl Iterator<Item = usize> {
        self.players[player].played.iter().filter(move |&card| {
            let printed = &CARD_CATALOG[card];
            printed.card_type != CardType::Event
                && printed.has_tag(Tag::Building)
                && printed.has_production_box()
                && self.can_change_production(player, printed.implemented_effects().production)
        })
    }

    /// `player` copies the production box of `card`, one of their building cards: its fixed
    /// Production, then its Production per Tag or Tile, counted now.
    pub(crate) fn copy_production_box(&mut self, player: usize, card: usize) {
        self.log.push(LogEvent::CopiedProductionBox { player, card });
        let effects = CARD_CATALOG[card].implemented_effects();
        self.change_productions(player, effects.production);
        self.change_production_per(player, effects.production_per);
    }
}
