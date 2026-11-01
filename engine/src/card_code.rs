//! The cards whose effects are Rust code of their own rather than effect data (ADR 0009). Each
//! is named by its index in the card catalog, its printed number minus 1, which the catalog
//! checks against the card's id when it is read.

use crate::board::{SpecialTile, mining_resource};
use crate::cards::{CARD_CATALOG, CardType, Effects, Tag};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::LogEvent;
use crate::resources::{Resource, Resources};
use crate::targets::Targeting;

/// #086 Robotic Workforce: "Duplicate only the production box of one of your building cards."
pub const ROBOTIC_WORKFORCE: usize = 85;

/// #152 Insulation: "Decrease your heat production any number of steps and increase your MC
/// production the same number of steps."
pub const INSULATION: usize = 151;

/// #194 Power Infrastructure: "Action: Spend any amount of energy and gain that amount of MC."
pub const POWER_INFRASTRUCTURE: usize = 193;

/// #200 Immigrant City: "When a City tile is placed, including this, increase your MC production
/// 1 step. Decrease your Energy production 1 step and decrease your MC production 2 steps. Place
/// a City tile." Its City is placed before its Production is lowered, so the step its own City
/// gives counts (see docs/rules-notes.md). Its effect data is only that Production change, its
/// City and its Trigger.
pub const IMMIGRANT_CITY: usize = 199;

/// #073 Mars University: "When you play a Science tag, including this, you may discard a card
/// from hand to draw a card." Its Trigger is effect data; each science Tag played lets its Player
/// discard once, after the card's other effects (see docs/rules-notes.md).
pub const MARS_UNIVERSITY: usize = 72;

/// #188 Flooding: "Place an ocean tile. If there are tiles adjacent to this ocean tile, you may
/// remove 4 MC from the owner of one of those tiles." Its effect data is its Ocean and the 4
/// MegaCredits it may remove; it takes only from the owners of Tiles next to that Ocean, and once
/// all 9 Oceans are placed, from nobody (see docs/rules-notes.md).
pub const FLOODING: usize = 187;

/// #064 Mining Area: "Place this tile on an area with a steel or titanium placement bonus, adjacent
/// to another of your tiles. Increase your production of that resource 1 step." Its effect data is
/// its Tile; the Production its Area gives is code, and Robotic Workforce copies it.
pub const MINING_AREA: usize = SpecialTile::MiningArea.card();

/// #067 Mining Rights: "Place this tile on an area with a steel or titanium placement bonus.
/// Increase that production 1 step." Like Mining Area, but anywhere on such an Area.
pub const MINING_RIGHTS: usize = SpecialTile::MiningRights.card();

/// Every card with code here, and its id.
pub const CARDS_WITH_CODE: [(usize, &str); 8] = [
    (ROBOTIC_WORKFORCE, "robotic_workforce"),
    (INSULATION, "insulation"),
    (POWER_INFRASTRUCTURE, "power_infrastructure"),
    (IMMIGRANT_CITY, "immigrant_city"),
    (MARS_UNIVERSITY, "mars_university"),
    (FLOODING, "flooding"),
    (MINING_AREA, "mining_area"),
    (MINING_RIGHTS, "mining_rights"),
];

/// Insulation's Production change for `steps`: that many steps of heat Production traded for as
/// many of MegaCredit Production.
pub fn insulation_change(steps: i32) -> Resources {
    Resources { megacredits: steps, heat: -steps, ..Resources::default() }
}

/// Power Infrastructure's Resource change for `amount`: that much energy spent for as many
/// MegaCredits.
pub fn energy_for_megacredits(amount: i32) -> Resources {
    Resources { megacredits: amount, energy: -amount, ..Resources::default() }
}

impl Game {
    /// The cards whose production box `player` may copy with Robotic Workforce: their own played
    /// Automated and Active cards with a building Tag and a production box they can carry out in
    /// full. A card's production box is its fixed and per-Tag Production data, or the Production
    /// a mining card's Tile gave; a test checks that against every printed box.
    pub(crate) fn copyable_production_boxes(&self, player: usize) -> impl Iterator<Item = usize> {
        self.players[player].played.iter().filter(move |&card| {
            let printed = &CARD_CATALOG[card];
            printed.card_type != CardType::Event
                && printed.has_tag(Tag::Building)
                && (self.mining_tile_resource(card).is_some()
                    || printed.has_production_box()
                        && self.can_carry_out_production_box(player, printed.implemented_effects()))
        })
    }

    /// Whether `player` can carry out the production box of a card with `effects` in full: their own
    /// Production change, and lowering any Player's (Heat Trappers), whose target they pick again.
    fn can_carry_out_production_box(&self, player: usize, effects: &Effects) -> bool {
        self.can_change_production(player, effects.production)
            && self.someone_can_lose_production(player, effects)
    }

    /// `player` copies the production box of `card`, one of their building cards: its fixed
    /// Production, then its Production per Tag or Tile, counted now.
    pub(crate) fn copy_production_box(&mut self, player: usize, card: usize) {
        self.log.push(LogEvent::CopiedProductionBox { player, card });
        if let Some(resource) = self.mining_tile_resource(card) {
            self.change_production(player, resource, 1);
            return;
        }
        let effects = CARD_CATALOG[card].implemented_effects();
        self.change_productions(player, effects.production);
        self.change_production_per(player, effects.production_per);
        if !effects.any_player_production().is_zero() {
            self.take_from_any_player_later(card);
        }
    }

    /// The Resource whose Production `card`'s Tile raised, if `card` is Mining Area or Mining
    /// Rights (the FAQ has Robotic Workforce copy it): the steel or titanium of its Area's
    /// placement bonus.
    fn mining_tile_resource(&self, card: usize) -> Option<Resource> {
        if card != MINING_AREA && card != MINING_RIGHTS {
            return None;
        }
        let tile = SpecialTile::of_card(card)?;
        self.board.area_of(tile).and_then(mining_resource)
    }

    /// Once Mining Area's or Mining Rights' Tile is on `area`, `player` raises their Production of
    /// the steel or titanium its placement bonus gives.
    pub(crate) fn raise_mining_production(&mut self, player: usize, area: usize) {
        let resource = mining_resource(area).expect("a mining Tile goes on a steel or titanium bonus");
        self.change_production(player, resource, 1);
    }

    /// Whether `player` can carry out Immigrant City: place its City, then lower their Production
    /// as printed once its own City has raised their MegaCredit Production 1 step.
    pub(crate) fn can_carry_out_immigrant_city(&self, player: usize) -> bool {
        let effects = CARD_CATALOG[IMMIGRANT_CITY].implemented_effects();
        let mut production = effects.production;
        production.megacredits += 1;
        self.can_change_production(player, production)
            && effects.tiles.iter().all(|&placement| self.can_take_action_placing(player, Some(placement)))
    }

    /// Offers the current Player, done with the card they played, to discard a card to draw one
    /// with Mars University if a discard is due, and returns whether the Game now waits on it.
    /// Without a card in their hand, they have nothing to discard, and the discards due are
    /// dropped.
    pub(crate) fn offer_discard_to_draw(&mut self) -> bool {
        if self.discards_to_draw == 0 {
            return false;
        }
        if self.players[self.current_player].hand.is_empty() {
            self.discards_to_draw = 0;
            return false;
        }
        self.wait_on(Waiting::DiscardToDraw);
        true
    }

    /// The current Player may discard any card from their hand to draw one, or be done.
    pub(crate) fn discard_to_draw_options(&self) -> Vec<DecisionOption> {
        let hand = self.players[self.current_player].hand.iter().map(DecisionOption::DiscardCard);
        hand.chain([DecisionOption::Done]).collect()
    }

    /// The current Player discards `card` face down, if they chose one, and draws a card. Then the
    /// next discard due follows, or the Action ends.
    pub(crate) fn discard_to_draw(&mut self, card: Option<usize>) {
        self.waiting = None;
        self.discards_to_draw -= 1;
        if let Some(card) = card {
            let player = self.current_player;
            self.players[player].hand.remove(card);
            self.discard.insert(card);
            self.log.push(LogEvent::DiscardedToDraw { player });
            self.draw(player, 1);
        }
        self.finish_unless_placing();
    }

    /// Flooding's Ocean is placed on `area`: once the card is done, it may take from the owner of a
    /// Tile next to it.
    pub(crate) fn take_next_to_floodings_ocean(&mut self, area: usize) {
        self.targeting = Some(Targeting { card: FLOODING, next_to: Some(area) });
    }

    /// Once Immigrant City's City is placed, the current Player lowers their Production as
    /// printed.
    pub(crate) fn finish_immigrant_city(&mut self) {
        let production = CARD_CATALOG[IMMIGRANT_CITY].implemented_effects().production;
        self.change_productions(self.current_player, production);
    }

    /// How many steps of heat Production `player` may trade with Insulation: from 1 up to all of
    /// it. Trading 0 steps is never offered, as it would only spend the card (see
    /// docs/rules-notes.md).
    pub(crate) fn insulation_steps(&self, player: usize) -> std::ops::RangeInclusive<i32> {
        1..=self.players[player].production.heat
    }
}
