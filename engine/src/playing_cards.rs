//! The central rules for Project Cards: whether a card can be played, how it can be paid
//! for, and carrying out its effects. Card effects written as data (ADR 0009) all go through
//! here, so no card checks these rules for itself.

use std::cmp::Reverse;

use serde::Serialize;

use crate::board::TileKind;
use crate::cards::{
    CARD_CATALOG, Card, CardType, Counted, Effects, Limit, Owner, Requirement, Tag, VictoryPoints,
};
use crate::game::Game;
use crate::log::{LogEvent, listed};
use crate::resources::Resource;

/// What a steel cube pays towards a card with a building Tag.
pub const STEEL_VALUE: i32 = 2;
/// What a titanium cube pays towards a card with a space Tag.
pub const TITANIUM_VALUE: i32 = 3;

/// How a card is paid for.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub struct Payment {
    pub megacredits: i32,
    pub steel: i32,
    pub titanium: i32,
}

impl Payment {
    /// As labels and the game log write it: "4 MegaCredits", "2 MegaCredits and 1 steel".
    pub fn text(self) -> String {
        let parts = [
            (Resource::MegaCredits, self.megacredits),
            (Resource::Steel, self.steel),
            (Resource::Titanium, self.titanium),
        ];
        let paid: Vec<String> = parts
            .into_iter()
            .filter(|&(_, amount)| amount > 0)
            .map(|(resource, amount)| resource.counted(amount))
            .collect();
        if paid.is_empty() { Resource::MegaCredits.counted(0) } else { listed(paid.into_iter()) }
    }
}

/// The card whose Tiles the current Player is placing, and how many of them are placed.
#[derive(Clone, Copy, Debug)]
pub struct CardTiles {
    pub card: usize,
    pub placed: usize,
}

impl Game {
    /// How many `tag` Tags `player` has in play: those on their played Automated and Active
    /// cards. Events lie face down once played, so none of their Tags count, the Event Tag
    /// included (see docs/rules-notes.md).
    pub fn tags(&self, player: usize, tag: Tag) -> i32 {
        self.players[player]
            .played
            .iter()
            .map(|card| &CARD_CATALOG[card])
            .filter(|printed| printed.card_type != CardType::Event)
            .map(|printed| printed.tags.iter().filter(|&&each| each == tag).count() as i32)
            .sum()
    }

    /// Whether `requirement` holds for `player`.
    pub fn meets(&self, player: usize, requirement: &Requirement) -> bool {
        let within = |value: i32, limit: Limit| match limit {
            Limit::Min(min) => value >= min,
            Limit::Max(max) => value <= max,
        };
        match *requirement {
            Requirement::Oxygen(limit) => within(self.oxygen, limit),
            Requirement::Temperature(limit) => within(self.temperature, limit),
            Requirement::Oceans(limit) => within(self.board.oceans() as i32, limit),
            Requirement::Tag { tag, min } => self.tags(player, tag) >= min,
            Requirement::Production { resource, min } => self.players[player].production[resource] >= min,
            Requirement::Tiles { tile, owner, min } => self.tiles_counted(player, tile, owner) >= min,
        }
    }

    /// How many Tiles of `kind` `owner` names: `player`'s own, or anyone's.
    fn tiles_counted(&self, player: usize, kind: TileKind, owner: Owner) -> i32 {
        let count = match owner {
            Owner::You => self.board.owned(player, kind),
            Owner::Anyone => self.board.in_play(kind),
        };
        count as i32
    }

    /// Whether `player` may play `card` from their hand: it is implemented, its Requirements
    /// hold, they can pay for it, and they can carry out its effects. Affordability is summed
    /// here rather than read from `payments`, which this is asked for every card in hand at
    /// every Action Decision; whenever the sum covers the cost, `payments` has a way to pay.
    pub(crate) fn can_play(&self, player: usize, card: usize) -> bool {
        let printed = &CARD_CATALOG[card];
        let Some(effects) = &printed.effects else { return false };
        let (steel, titanium) = self.usable_cubes(player, printed);
        let spendable =
            self.players[player].resources.megacredits + STEEL_VALUE * steel + TITANIUM_VALUE * titanium;
        printed.requirements.iter().all(|requirement| self.meets(player, requirement))
            && spendable >= printed.project_cost()
            && self.can_carry_out(player, effects)
    }

    /// The steel and titanium `player` may put towards `printed`: steel only for a building
    /// Tag, titanium only for a space Tag.
    fn usable_cubes(&self, player: usize, printed: &Card) -> (i32, i32) {
        let resources = self.players[player].resources;
        let steel = if printed.has_tag(Tag::Building) { resources.steel } else { 0 };
        let titanium = if printed.has_tag(Tag::Space) { resources.titanium } else { 0 };
        (steel, titanium)
    }

    /// The Victory Points on the cards `player` has played.
    pub fn card_victory_points(&self, player: usize) -> i32 {
        self.players[player]
            .played
            .iter()
            .filter_map(|card| CARD_CATALOG[card].victory_points)
            .map(|points| match points {
                VictoryPoints::Fixed(points) => points,
                VictoryPoints::Per { points, per, of } => points * (self.count_of(player, of) / per),
                VictoryPoints::AtLeast { points, at_least, of } => {
                    if self.count_of(player, of) >= at_least {
                        points
                    } else {
                        0
                    }
                }
            })
            .sum()
    }

    /// How many of `what` there are for `player`'s card Victory Points. Card Resources (ticket
    /// 19) and Tiles of cards (ticket 18) don't exist yet, so they count 0.
    fn count_of(&self, player: usize, what: Counted) -> i32 {
        match what {
            Counted::Tag(tag) => self.tags(player, tag),
            Counted::TilesInPlay(kind) => self.board.in_play(kind) as i32,
            Counted::CardResource(_) | Counted::Adjacent(_) => 0,
        }
    }

    /// Whether `player` can carry out `effects`: on their own Resources and Production, and
    /// with an Area for each Tile (an Ocean always, as Aquifer: see docs/rules-notes.md).
    /// Resources lost are checked against what the Player holds before paying for the card;
    /// no card yet both costs steel or titanium and loses some.
    fn can_carry_out(&self, player: usize, effects: &Effects) -> bool {
        let own = &self.players[player];
        Resource::ALL.into_iter().all(|resource| {
            own.resources[resource] + effects.resources[resource] >= 0
                && own.production[resource] + effects.production[resource] >= resource.min_production()
        }) && effects.tiles.iter().all(|&tile| self.can_take_action_placing(Some(tile)))
    }

    /// Every way `player` may pay for `card`, the most MegaCredits first: each split between
    /// steel, titanium and MegaCredits for the rest. Steel and titanium may pay more than the
    /// cost, with no change, but a split with a cube the others make unneeded is never worth
    /// taking, so it is left out (see docs/rules-notes.md).
    pub(crate) fn payments(&self, player: usize, card: usize) -> Vec<Payment> {
        let printed = &CARD_CATALOG[card];
        let cost = printed.project_cost();
        let (most_steel, most_titanium) = self.usable_cubes(player, printed);
        let megacredits = self.players[player].resources.megacredits;
        let mut payments = Vec::new();
        for titanium in 0..=most_titanium.min(cubes_to_pay(cost, TITANIUM_VALUE)) {
            for steel in 0..=most_steel.min(cubes_to_pay(cost, STEEL_VALUE)) {
                let covered = STEEL_VALUE * steel + TITANIUM_VALUE * titanium;
                let unneeded = (steel > 0 && covered - STEEL_VALUE >= cost)
                    || (titanium > 0 && covered - TITANIUM_VALUE >= cost);
                let payment = Payment { megacredits: (cost - covered).max(0), steel, titanium };
                if !unneeded && payment.megacredits <= megacredits {
                    payments.push(payment);
                }
            }
        }
        payments.sort_by_key(|payment| Reverse(payment.megacredits));
        payments
    }

    /// `player` pays for `card` and plays it from their hand: it joins their played cards and
    /// its effects are carried out.
    pub(crate) fn play_card(&mut self, player: usize, card: usize, payment: Payment) {
        let own = &mut self.players[player];
        own.resources.megacredits -= payment.megacredits;
        own.resources.steel -= payment.steel;
        own.resources.titanium -= payment.titanium;
        own.hand.remove(card);
        own.played.insert(card);
        self.log.push(LogEvent::PlayedCard { player, card, payment });
        let effects = CARD_CATALOG[card].implemented_effects();
        self.carry_out(player, effects);
        if !effects.tiles.is_empty() {
            self.placing_for = Some(CardTiles { card, placed: 0 });
        }
        self.finish_unless_placing();
    }

    /// Starts placing the next Tile of the card being played, if it has one left. An Ocean
    /// once all 9 are placed is skipped, as for Aquifer (see docs/rules-notes.md).
    pub(crate) fn place_next_card_tile(&mut self) {
        while let Some(CardTiles { card, placed }) = self.placing_for {
            let Some(&tile) = CARD_CATALOG[card].implemented_effects().tiles.get(placed) else {
                self.placing_for = None;
                return;
            };
            self.placing_for = Some(CardTiles { card, placed: placed + 1 });
            match tile {
                TileKind::Ocean => self.place_ocean(),
                _ => self.placing = Some(tile),
            }
            if self.placing.is_some() {
                return;
            }
        }
    }

    /// Carries out `effects` for `player`, in the order `Effects` gives.
    fn carry_out(&mut self, player: usize, effects: &Effects) {
        for resource in Resource::ALL {
            let by = effects.resources[resource];
            if by != 0 {
                self.players[player].resources[resource] += by;
                self.log.push(LogEvent::ResourceChanged { player, resource, by });
            }
        }
        for resource in Resource::ALL {
            let by = effects.production[resource];
            if by != 0 {
                self.change_production(player, resource, by);
            }
        }
        for _ in 0..effects.temperature {
            self.raise_temperature(player);
        }
        for _ in 0..effects.oxygen {
            self.raise_oxygen(player);
        }
        if effects.terraform_rating != 0 {
            self.players[player].terraform_rating += effects.terraform_rating;
            self.log.push(LogEvent::TerraformRatingRaised { player, by: effects.terraform_rating });
        }
        if effects.draw > 0 {
            self.log.push(LogEvent::DrewCards { player, count: effects.draw });
            self.draw(player, effects.draw);
        }
    }
}

/// How many cubes worth `value` each it takes to pay `cost` on their own.
fn cubes_to_pay(cost: i32, value: i32) -> i32 {
    (cost + value - 1) / value
}
