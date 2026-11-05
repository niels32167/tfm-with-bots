//! The cards whose effects are Rust code of their own rather than effect data (ADR 0009). Each
//! is named by its index in the card catalog, its printed number minus 1, which the catalog
//! checks against the card's id when it is read.

use crate::board::{SpecialTile, mining_resource};
use crate::cards::{CARD_CATALOG, CardType, Effects, Tag};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::LogEvent;
use crate::resources::{Resource, Resources};
use crate::targets::Targeting;
use crate::triggers::Happened;

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

/// #185 Olympus Conference: "When you play a Science tag, including this, either add a Science
/// resource to this card, or remove a Science resource from this card to draw a card." Its Trigger is
/// effect data; each science Tag played is one such choice, after the card's other effects, in any
/// order with Mars University's discards (see docs/rules-notes.md).
pub const OLYMPUS_CONFERENCE: usize = 184;

/// #005 Search for Life: "Action: Spend 1 MC to reveal the top card of the draw deck. If that card
/// has a Microbe tag, add a Science resource here." Its effect data is the MegaCredit.
pub const SEARCH_FOR_LIFE: usize = 4;

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

/// #172 Pets: "Animals may not be removed from this card." The sentence is printed on the card, but
/// not in its text in the card file.
pub const PETS: usize = 171;

/// #173 Protected Habitats: "Opponents may not remove your plants, animals or microbes."
pub const PROTECTED_HABITATS: usize = 172;

/// #074 Viral Enhancers: "When you play a plant, microbe, or an animal tag, including this, gain 1
/// plant or add 1 resource to THAT CARD." Its Trigger is effect data, the plant; a card that holds Card
/// Resources lets its Player choose for each such Tag, after the card's other effects (see
/// docs/rules-notes.md).
pub const VIRAL_ENHANCERS: usize = 73;

/// Every card with code here, and its id.
pub const CARDS_WITH_CODE: [(usize, &str); 13] = [
    (ROBOTIC_WORKFORCE, "robotic_workforce"),
    (INSULATION, "insulation"),
    (POWER_INFRASTRUCTURE, "power_infrastructure"),
    (IMMIGRANT_CITY, "immigrant_city"),
    (MARS_UNIVERSITY, "mars_university"),
    (FLOODING, "flooding"),
    (MINING_AREA, "mining_area"),
    (MINING_RIGHTS, "mining_rights"),
    (OLYMPUS_CONFERENCE, "olympus_conference"),
    (SEARCH_FOR_LIFE, "search_for_life"),
    (PETS, "pets"),
    (PROTECTED_HABITATS, "protected_habitats"),
    (VIRAL_ENHANCERS, "viral_enhancers"),
];

/// The card played whose Tags Viral Enhancers still asks about, which holds Card Resources, and how
/// many times more.
#[derive(Clone, Copy, Debug)]
pub struct ViralEnhancing {
    pub card: usize,
    pub times: u32,
}

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

    /// Whether a card can be drawn: the deck or the discard pile, which is shuffled into a new deck
    /// when the deck runs out, has one.
    pub(crate) fn can_draw(&self) -> bool {
        !self.deck.is_empty() || !self.discard.is_empty()
    }

    /// `player` reveals the top card of the deck with Search for Life and discards it. If it has a
    /// microbe Tag, a science goes on Search for Life.
    pub(crate) fn search_for_life(&mut self, player: usize) {
        let revealed = self.draw_cards(player, 1);
        for card in revealed.iter() {
            self.log.push(LogEvent::RevealedCard { player, card });
            self.discard.insert(card);
            if CARD_CATALOG[card].has_tag(Tag::Microbe) {
                self.change_card_resources(player, SEARCH_FOR_LIFE, 1);
            }
        }
    }

    /// Whether the current Player has a choice with Olympus Conference: a science on it to remove,
    /// and a card to draw for it.
    fn can_draw_with_olympus_conference(&self) -> bool {
        self.card_resources.on(OLYMPUS_CONFERENCE) > 0 && self.can_draw()
    }

    /// Offers the current Player, done with the card they played, what the science Tags they played
    /// let them do, and returns whether the Game now waits on it. Olympus Conference's science is
    /// added without a Decision while there is nothing else to do with it; that first is never
    /// worse, as it can only give them a science to remove for a later Tag. While both cards have
    /// something due, the Player orders them by picking either's Option, in one Decision (see
    /// docs/rules-notes.md). Then Mars University lets them discard a card to draw one if a discard
    /// is due; without a card in their hand, they have nothing to discard, and the discards due are
    /// dropped.
    pub(crate) fn offer_science_tag_effects(&mut self) -> bool {
        while self.olympus_conference_due > 0 && !self.can_draw_with_olympus_conference() {
            self.olympus_conference_due -= 1;
            self.change_card_resources(self.current_player, OLYMPUS_CONFERENCE, 1);
        }
        if self.olympus_conference_due > 0 {
            self.wait_on(Waiting::OlympusConference);
            return true;
        }
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

    /// Offers the current Player what Viral Enhancers does for a card they played that holds Card
    /// Resources, and returns whether the Game now waits on it. It comes last of what the card sets
    /// off, which is never worse: the plant or Card Resource gives nothing to the others, and a card
    /// they draw may tell them which to take.
    pub(crate) fn offer_viral_enhancers(&mut self) -> bool {
        if self.viral_enhancing.is_none() {
            return false;
        }
        self.wait_on(Waiting::ViralEnhancers);
        true
    }

    /// The current Player chooses what Viral Enhancers does for the card played.
    pub(crate) fn viral_enhancers_options(&self) -> Vec<DecisionOption> {
        let card = self.viral_enhancing.expect("Viral Enhancers asks only while it is due").card;
        [true, false].map(|add| DecisionOption::ViralEnhancers { card, add }).to_vec()
    }

    /// The current Player adds 1 Card Resource to `card`, or gains 1 plant. Then Viral Enhancers asks
    /// again for the next Tag, or the Action ends.
    pub(crate) fn viral_enhancers(&mut self, card: usize, add: bool) {
        self.waiting = None;
        let times = self.viral_enhancing.expect("Viral Enhancers asks only while it is due").times - 1;
        self.viral_enhancing = (times > 0).then_some(ViralEnhancing { card, times });
        let player = self.current_player;
        if add {
            self.change_card_resources(player, card, 1);
        } else {
            self.change_resources(player, Resources { plants: 1, ..Resources::default() });
        }
        self.finish_unless_placing();
    }

    /// The plants `player` gains from Viral Enhancers as soon as they play `card`, before its effects:
    /// one for each such Tag, unless the card holds Card Resources and they may choose those instead.
    pub(crate) fn plants_from_viral_enhancers(&self, player: usize, card: usize) -> i32 {
        if !self.players[player].played.contains(VIRAL_ENHANCERS) || CARD_CATALOG[card].holds().is_some() {
            return 0;
        }
        let happened = Happened::CardPlayed { player, card };
        let triggers = &CARD_CATALOG[VIRAL_ENHANCERS].implemented_effects().when;
        triggers.iter().map(|trigger| trigger.resources.plants * happened.times(&trigger.on, player)).sum()
    }

    /// The current Player may discard any card from their hand to draw one, or be done.
    pub(crate) fn discard_to_draw_options(&self) -> Vec<DecisionOption> {
        let hand = self.players[self.current_player].hand.iter().map(DecisionOption::DiscardCard);
        hand.chain([DecisionOption::Done]).collect()
    }

    /// The current Player chooses what Olympus Conference does, or, with a discard due, to carry out
    /// Mars University's first: with a card in their hand, its Options come too.
    pub(crate) fn olympus_conference_options(&self) -> Vec<DecisionOption> {
        let own_options = [false, true].map(|draw| DecisionOption::OlympusConference { draw });
        let hand_is_empty = self.players[self.current_player].hand.is_empty();
        let discards = if self.discards_to_draw > 0 && !hand_is_empty {
            self.discard_to_draw_options()
        } else {
            Vec::new()
        };
        own_options.into_iter().chain(discards).collect()
    }

    /// The current Player removes a science from Olympus Conference to draw a card, or adds one to
    /// it. Then the next effect due follows, or the Action ends.
    pub(crate) fn olympus_conference(&mut self, draw: bool) {
        self.waiting = None;
        self.olympus_conference_due -= 1;
        let player = self.current_player;
        if draw {
            self.change_card_resources(player, OLYMPUS_CONFERENCE, -1);
            self.log.push(LogEvent::DrewCards { player, count: 1 });
            self.draw(player, 1);
        } else {
            self.change_card_resources(player, OLYMPUS_CONFERENCE, 1);
        }
        self.finish_unless_placing();
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
