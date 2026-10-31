//! The central rules for Project Cards: whether a card can be played, how it can be paid
//! for, and carrying out its effects. Card effects written as data (ADR 0009) all go through
//! here, so no card checks these rules for itself.

use std::cmp::Reverse;

use serde::Serialize;

use crate::board::{Placement, TileKind};
use crate::card_code::{INSULATION, ROBOTIC_WORKFORCE, insulation_change};
use crate::cards::{
    CARD_CATALOG, CardType, Counted, Effects, Limit, Owner, ProductionAtLeast, ProductionPer, Requirement,
    ResourcesPer, Tag, TerraformRatingPer, VictoryPoints,
};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::{LogEvent, listed};
use crate::resources::{Resource, Resources};

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
    /// Nothing paid, for an action that costs no MegaCredits.
    pub const NOTHING: Payment = Payment { megacredits: 0, steel: 0, titanium: 0 };

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

/// A Production change the Player chooses for the card they are playing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProductionChange {
    /// The card's own Production alternative at this index (Artificial Photosynthesis).
    Alternative(usize),
    /// The production box of this building card of the Player's, copied (Robotic Workforce).
    CopyBox(usize),
    /// This many steps of heat Production traded for MegaCredit Production (Insulation).
    HeatForMegaCredits(i32),
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
        let spendable = self.spendable(player, printed.has_tag(Tag::Building), printed.has_tag(Tag::Space));
        printed.requirements.iter().all(|requirement| self.meets(player, requirement))
            && spendable >= printed.project_cost()
            && self.can_carry_out(player, effects)
            && self.can_make_a_production_change(player, card)
    }

    /// The steel and titanium `player` may put towards a cost: their steel if `steel` may pay it
    /// (a card with a building Tag, Aquifer Pumping's action), their titanium if `titanium` may (a
    /// card with a space Tag, Water Import from Europa's action).
    pub(crate) fn usable_cubes(&self, player: usize, steel: bool, titanium: bool) -> (i32, i32) {
        let resources = self.players[player].resources;
        (if steel { resources.steel } else { 0 }, if titanium { resources.titanium } else { 0 })
    }

    /// What `player` could spend on a cost that steel or titanium may pay as `usable_cubes` says:
    /// their MegaCredits plus what those cubes are worth.
    pub(crate) fn spendable(&self, player: usize, steel: bool, titanium: bool) -> i32 {
        let (steel, titanium) = self.usable_cubes(player, steel, titanium);
        self.players[player].resources.megacredits + STEEL_VALUE * steel + TITANIUM_VALUE * titanium
    }

    /// The Victory Points on the cards `player` has played.
    pub fn card_victory_points(&self, player: usize) -> i32 {
        self.players[player]
            .played
            .iter()
            .filter_map(|card| CARD_CATALOG[card].victory_points)
            .map(|points| match points {
                VictoryPoints::Fixed(points) => points,
                VictoryPoints::Per { points, per, of } => self.for_every(player, points, per, of),
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

    /// `amount` for every `per` of `of` that `player` has: 2 for 5 Tags at 1 for every 2.
    fn for_every(&self, player: usize, amount: i32, per: i32, of: Counted) -> i32 {
        amount * (self.count_of(player, of) / per)
    }

    /// How many of `what` there are for `player`'s card Victory Points or Production. Card
    /// Resources (ticket 19) and Tiles of cards (ticket 18) don't exist yet, so they count 0.
    fn count_of(&self, player: usize, what: Counted) -> i32 {
        match what {
            Counted::Tag(tag) => self.tags(player, tag),
            Counted::TilesInPlay(kind) => self.board.in_play(kind) as i32,
            Counted::TilesOnMars(kind) => self.board.on_mars(kind) as i32,
            Counted::CardResource(_) | Counted::Adjacent(_) => 0,
        }
    }

    /// Whether `player` can carry out `effects`: on their own Resources and Production, and
    /// with an Area for each Tile (an Ocean always, as Aquifer: see docs/rules-notes.md).
    /// Resources lost are checked against what the Player holds before paying for the card;
    /// no card yet both costs steel or titanium and loses some.
    pub(crate) fn can_carry_out(&self, player: usize, effects: &Effects) -> bool {
        let own = &self.players[player];
        Resource::ALL.into_iter().all(|resource| own.resources[resource] + effects.resources[resource] >= 0)
            && self.can_change_production(player, effects.production)
            && effects.tiles.iter().all(|&placement| self.can_take_action_placing(Some(placement)))
    }

    /// Whether changing `player`'s Production `by` this keeps it within its limits.
    pub(crate) fn can_change_production(&self, player: usize, by: Resources) -> bool {
        let production = self.players[player].production;
        Resource::ALL
            .into_iter()
            .all(|resource| production[resource] + by[resource] >= resource.min_production())
    }

    /// The Production changes `player` may choose between for `card`, which they are playing:
    /// none for a card that offers no such choice.
    pub(crate) fn production_options(&self, player: usize, card: usize) -> Vec<DecisionOption> {
        let changes: Vec<ProductionChange> = if card == ROBOTIC_WORKFORCE {
            self.copyable_production_boxes(player).map(ProductionChange::CopyBox).collect()
        } else if card == INSULATION {
            self.insulation_steps(player).map(ProductionChange::HeatForMegaCredits).collect()
        } else {
            let alternatives = &CARD_CATALOG[card].implemented_effects().production_choice;
            (0..alternatives.len())
                .filter(|&index| self.can_change_production(player, alternatives[index]))
                .map(ProductionChange::Alternative)
                .collect()
        };
        changes.into_iter().map(|change| DecisionOption::ChangeProduction { card, change }).collect()
    }

    /// Whether `card` offers `player` no Production change to choose, or at least one they can
    /// make: `production_options` not being empty, but quicker, as it stops at the first one.
    /// It is checked against their Production before the card's other effects; no card has both a
    /// choice and fixed Production.
    fn can_make_a_production_change(&self, player: usize, card: usize) -> bool {
        if card == ROBOTIC_WORKFORCE {
            return self.copyable_production_boxes(player).next().is_some();
        }
        if card == INSULATION {
            return !self.insulation_steps(player).is_empty();
        }
        let alternatives = &CARD_CATALOG[card].implemented_effects().production_choice;
        alternatives.is_empty() || alternatives.iter().any(|&by| self.can_change_production(player, by))
    }

    /// Every way `player` may pay for `card`, the most MegaCredits first: each split between
    /// steel, titanium and MegaCredits for the rest. Steel and titanium may pay more than the
    /// cost, with no change, but a split with a cube the others make unneeded is never worth
    /// taking, so it is left out (see docs/rules-notes.md).
    pub(crate) fn payments(&self, player: usize, card: usize) -> Vec<Payment> {
        let printed = &CARD_CATALOG[card];
        let (steel, titanium) =
            self.usable_cubes(player, printed.has_tag(Tag::Building), printed.has_tag(Tag::Space));
        self.ways_to_pay(player, printed.project_cost(), steel, titanium)
    }

    /// Every way `player` may pay `cost` with up to `most_steel` steel and `most_titanium`
    /// titanium, the most MegaCredits first, leaving out a split with a cube the others make
    /// unneeded (see `payments`).
    pub(crate) fn ways_to_pay(
        &self,
        player: usize,
        cost: i32,
        most_steel: i32,
        most_titanium: i32,
    ) -> Vec<Payment> {
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
        self.pay(player, payment);
        let own = &mut self.players[player];
        own.hand.remove(card);
        own.played.insert(card);
        self.log.push(LogEvent::PlayedCard { player, card, payment });
        let effects = CARD_CATALOG[card].implemented_effects();
        self.carry_out(player, effects);
        // Keeping the cards looked at comes first; once it is done, the Production change follows.
        if !self.look_at_cards(player, card, effects.look_at, false) {
            self.choose_production_change(player, card);
        }
    }

    /// `player` makes the Production change `card`, which they are playing, lets them choose, if
    /// it has any; then its Tiles follow. With only one change to make, they have nothing to
    /// choose.
    pub(crate) fn choose_production_change(&mut self, player: usize, card: usize) {
        match self.production_options(player, card)[..] {
            [] => self.place_card_tiles(card),
            [DecisionOption::ChangeProduction { change, .. }] => {
                self.change_production_as_chosen(player, card, change)
            }
            _ => self.wait_on(Waiting::Production(card)),
        }
    }

    /// `player` makes `change` for `card`, which they are playing, and the card's Tiles follow.
    pub(crate) fn change_production_as_chosen(
        &mut self,
        player: usize,
        card: usize,
        change: ProductionChange,
    ) {
        self.waiting = None;
        match change {
            ProductionChange::Alternative(index) => {
                self.change_productions(player, CARD_CATALOG[card].production_alternative(index))
            }
            ProductionChange::CopyBox(copied) => self.copy_production_box(player, copied),
            ProductionChange::HeatForMegaCredits(steps) => {
                self.change_productions(player, insulation_change(steps))
            }
        }
        self.place_card_tiles(card);
    }

    /// The Tiles of `card`, which is being played, are placed one at a time; then the Action ends.
    fn place_card_tiles(&mut self, card: usize) {
        if !CARD_CATALOG[card].implemented_effects().tiles.is_empty() {
            self.placing_for = Some(CardTiles { card, placed: 0 });
        }
        self.finish_unless_placing();
    }

    /// Starts placing the next Tile of the card being played, if it has one left. An Ocean
    /// once all 9 are placed is skipped, as for Aquifer (see docs/rules-notes.md).
    pub(crate) fn place_next_card_tile(&mut self) {
        while let Some(CardTiles { card, placed }) = self.placing_for {
            let Some(&placement) = CARD_CATALOG[card].implemented_effects().tiles.get(placed) else {
                self.placing_for = None;
                return;
            };
            self.placing_for = Some(CardTiles { card, placed: placed + 1 });
            self.place_card_tile(placement);
            if self.is_placing() {
                return;
            }
        }
    }

    /// `player` pays `payment`.
    pub(crate) fn pay(&mut self, player: usize, payment: Payment) {
        let own = &mut self.players[player].resources;
        own.megacredits -= payment.megacredits;
        own.steel -= payment.steel;
        own.titanium -= payment.titanium;
    }

    /// The current Player has a card's Tile to make `placement` with. An Ocean once all 9 are
    /// placed is skipped, as for Aquifer (see docs/rules-notes.md).
    pub(crate) fn place_card_tile(&mut self, placement: Placement) {
        if placement.tile == TileKind::Ocean {
            self.place_ocean(placement.on);
        } else {
            self.place(placement);
        }
    }

    /// Carries out `effects` for `player`, in the order `Effects` gives, up to the cards looked
    /// at: what follows them is for the card or action to carry on with.
    pub(crate) fn carry_out(&mut self, player: usize, effects: &Effects) {
        self.change_resources(player, effects.resources);
        if let Some(ResourcesPer { resource, amount, per, of }) = effects.resources_per {
            let mut gained = Resources::default();
            gained[resource] = self.for_every(player, amount, per, of);
            self.change_resources(player, gained);
        }
        self.change_productions(player, effects.production);
        self.change_production_per(player, effects.production_per);
        if let Some(ProductionAtLeast { resource, steps, at_least, of }) = effects.production_at_least
            && self.count_of(player, of) >= at_least
        {
            self.change_production(player, resource, steps);
        }
        for _ in 0..effects.temperature {
            self.raise_temperature(player);
        }
        for _ in 0..effects.oxygen {
            self.raise_oxygen(player);
        }
        self.raise_terraform_rating_by(player, effects.terraform_rating);
        if let Some(TerraformRatingPer { steps, per, of }) = effects.terraform_rating_per {
            self.raise_terraform_rating_by(player, self.for_every(player, steps, per, of));
        }
        if effects.draw > 0 {
            self.log.push(LogEvent::DrewCards { player, count: effects.draw });
            self.draw(player, effects.draw);
        }
    }

    /// Raises `player`'s Terraform Rating `by` so many steps, if any.
    fn raise_terraform_rating_by(&mut self, player: usize, by: i32) {
        if by != 0 {
            self.players[player].terraform_rating += by;
            self.log.push(LogEvent::TerraformRatingRaised { player, by });
        }
    }

    /// Raises `player`'s Production by `per` what they have, if the card has such an effect.
    pub(crate) fn change_production_per(&mut self, player: usize, per: Option<ProductionPer>) {
        if let Some(ProductionPer { resource, steps, per, of }) = per {
            let by = self.for_every(player, steps, per, of);
            if by != 0 {
                self.change_production(player, resource, by);
            }
        }
    }

    /// Changes each of `player`'s Resources `by` so many, gained or lost.
    pub(crate) fn change_resources(&mut self, player: usize, by: Resources) {
        for resource in Resource::ALL {
            if by[resource] != 0 {
                self.players[player].resources[resource] += by[resource];
                self.log.push(LogEvent::ResourceChanged { player, resource, by: by[resource] });
            }
        }
    }

    /// Changes each of `player`'s Productions `by` so many steps.
    pub(crate) fn change_productions(&mut self, player: usize, by: Resources) {
        for resource in Resource::ALL {
            if by[resource] != 0 {
                self.change_production(player, resource, by[resource]);
            }
        }
    }
}

/// How many cubes worth `value` each it takes to pay `cost` on their own.
fn cubes_to_pay(cost: i32, value: i32) -> i32 {
    (cost + value - 1) / value
}
