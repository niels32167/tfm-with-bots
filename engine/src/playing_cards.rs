//! The central rules for Project Cards: whether a card can be played, how it can be paid
//! for, and carrying out its effects. Card effects written as data (ADR 0009) all go through
//! here, so no card checks these rules for itself.

use std::cmp::Reverse;

use serde::Serialize;

use crate::board::{Placement, SpecialTile, TileKind};
use crate::card_code::{FLOODING, HELION, IMMIGRANT_CITY, INSULATION, ROBOTIC_WORKFORCE, insulation_change};
use crate::card_resources::Adding;
use crate::cards::{
    CARD_CATALOG, CARDS_WITH, CardType, Counted, CubeValues, Effects, Limit, NextCard, Owner,
    ProductionAtLeast, ProductionPer, Requirement, ResourcesPer, Tag, TerraformRatingPer, VictoryPoints,
};
use crate::game::{DecisionOption, Game, TEMPERATURE_STEP, Waiting};
use crate::log::{LogEvent, listed};
use crate::resources::{Resource, Resources};
use crate::triggers::Happened;

/// What a steel cube pays towards a card with a building Tag, unless a card raises it.
pub const STEEL_VALUE: i32 = 2;
/// What a titanium cube pays towards a card with a space Tag, unless a card raises it.
pub const TITANIUM_VALUE: i32 = 3;

/// How a card is paid for.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub struct Payment {
    pub megacredits: i32,
    pub steel: i32,
    pub titanium: i32,
    /// Heat used as MegaCredits (Helion).
    pub heat: i32,
}

impl Payment {
    /// Nothing paid, for an action that costs no MegaCredits.
    pub const NOTHING: Payment = Payment { megacredits: 0, steel: 0, titanium: 0, heat: 0 };

    /// As labels and the game log write it: "4 MegaCredits", "2 MegaCredits and 1 steel".
    pub fn text(self) -> String {
        let parts = [
            (Resource::MegaCredits, self.megacredits),
            (Resource::Steel, self.steel),
            (Resource::Titanium, self.titanium),
            (Resource::Heat, self.heat),
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

    /// Whether `requirement` holds for `player`. A Requirement on a Global Parameter is as many
    /// steps easier to meet as their cards make it (see `requirement_steps`).
    pub fn meets(&self, player: usize, requirement: &Requirement) -> bool {
        // Easier in the Player's favour, which is always their better choice of +2 or -2 steps.
        let within = |value: i32, limit: Limit, step: i32| match limit {
            Limit::Min(min) => value >= min - self.requirement_steps(player) * step,
            Limit::Max(max) => value <= max + self.requirement_steps(player) * step,
        };
        match *requirement {
            Requirement::Oxygen(limit) => within(self.oxygen, limit, 1),
            Requirement::Temperature(limit) => within(self.temperature, limit, TEMPERATURE_STEP),
            Requirement::Oceans(limit) => within(self.board.oceans() as i32, limit, 1),
            Requirement::Tag { tag, min } => self.tags(player, tag) >= min,
            Requirement::Production { resource, min } => self.players[player].production[resource] >= min,
            Requirement::Tiles { tile, owner, min } => self.tiles_counted(player, tile, owner) >= min,
        }
    }

    /// How many steps easier `player`'s Requirements on a Global Parameter are to meet: those
    /// their played cards give (Adaptation Technology), and those an Event gives the next card
    /// they play (Special Design).
    fn requirement_steps(&self, player: usize) -> i32 {
        let own = &self.players[player];
        let ongoing = own.played.intersection(CARDS_WITH.requirement_steps).iter();
        let steps: i32 = ongoing.map(|card| CARD_CATALOG[card].implemented_effects().requirement_steps).sum();
        steps + self.next_card_effect(player).requirement_steps
    }

    /// What the Event `player` played last changes about the next card they play this Generation,
    /// if anything.
    pub(crate) fn next_card_effect(&self, player: usize) -> NextCard {
        let event = self.players[player].next_card;
        event.and_then(|card| CARD_CATALOG[card].implemented_effects().next_card).unwrap_or_default()
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
        printed.requirements.iter().all(|requirement| self.meets(player, requirement))
            && self.spendable(
                player,
                printed.has_tag(Tag::Building),
                printed.has_tag(Tag::Space),
                effects.resources.heat,
            ) >= self.card_cost(player, card)
            && if card == IMMIGRANT_CITY {
                self.can_carry_out_immigrant_city(player)
            } else {
                self.can_carry_out_with_plants(
                    player,
                    effects,
                    self.plants_from_viral_enhancers(player, card),
                )
            }
            && self.can_make_a_production_change(player, card)
    }

    /// The steel and titanium `player` may put towards a cost: their steel if `steel` may pay it
    /// (a card with a building Tag, Aquifer Pumping's action), their titanium if `titanium` may (a
    /// card with a space Tag, Water Import from Europa's action).
    pub(crate) fn usable_cubes(&self, player: usize, steel: bool, titanium: bool) -> (i32, i32) {
        let resources = self.players[player].resources;
        (if steel { resources.steel } else { 0 }, if titanium { resources.titanium } else { 0 })
    }

    /// What `player` could spend on a cost that neither steel nor titanium may pay: `spendable`, but
    /// quicker, as an Action Decision asks for it for every Milestone.
    pub(crate) fn spendable_megacredits(&self, player: usize) -> i32 {
        self.players[player].resources.megacredits + self.usable_heat(player, 0)
    }

    /// The heat `player` may use as MegaCredits (Helion): all they have, but what the effects they are
    /// paying for change it by if that loses some, since those need it left to lose (Local Heat
    /// Trapping's 5 heat).
    pub(crate) fn usable_heat(&self, player: usize, heat_change: i32) -> i32 {
        if !self.players[player].played.contains(HELION) {
            return 0;
        }
        (self.players[player].resources.heat + heat_change.min(0)).max(0)
    }

    /// What `player` could spend on a cost that steel or titanium may pay as `usable_cubes` says, for
    /// effects that change their heat by `heat_change`: their MegaCredits, what those cubes are worth
    /// and the heat they may use.
    pub(crate) fn spendable(&self, player: usize, steel: bool, titanium: bool, heat_change: i32) -> i32 {
        let (steel, titanium) = self.usable_cubes(player, steel, titanium);
        let values = self.cube_values(player);
        self.players[player].resources.megacredits
            + values.steel * steel
            + values.titanium * titanium
            + self.usable_heat(player, heat_change)
    }

    /// What one steel and one titanium of `player`'s pay: `STEEL_VALUE` and `TITANIUM_VALUE`, plus
    /// what their played cards add (Advanced Alloys).
    pub(crate) fn cube_values(&self, player: usize) -> CubeValues {
        let mut values = CubeValues { steel: STEEL_VALUE, titanium: TITANIUM_VALUE };
        for card in self.players[player].played.intersection(CARDS_WITH.cube_values).iter() {
            let added = CARD_CATALOG[card].implemented_effects().cube_values.unwrap_or_default();
            values.steel += added.steel;
            values.titanium += added.titanium;
        }
        values
    }

    /// The Victory Points on the cards `player` has played.
    pub fn card_victory_points(&self, player: usize) -> i32 {
        self.players[player]
            .played
            .iter()
            .filter_map(|card| CARD_CATALOG[card].victory_points.map(|points| (card, points)))
            .map(|(card, points)| match points {
                VictoryPoints::Fixed(points) => points,
                VictoryPoints::Per { points, per, of } => {
                    points * (self.count_for_card(player, card, of) / per)
                }
                VictoryPoints::AtLeast { points, at_least, of } => {
                    if self.count_for_card(player, card, of) >= at_least { points } else { 0 }
                }
            })
            .sum()
    }

    /// How many of `what` there are for the Victory Points of `card`, which `player` has played:
    /// as `count_of` counts them, but Tiles next to the card's own Tile (Capital, Commercial
    /// District) and the Card Resources on the card too.
    fn count_for_card(&self, player: usize, card: usize, what: Counted) -> i32 {
        match what {
            Counted::Adjacent(kind) => {
                let own_tile = SpecialTile::of_card(card).and_then(|special| self.board.area_of(special));
                own_tile.map_or(0, |area| self.board.adjacent(area, kind) as i32)
            }
            Counted::CardResource(_) => self.card_resources.on(card),
            _ => self.count_of(player, what),
        }
    }

    /// `amount` for every `per` of `of` that `player` has: 2 for 5 Tags at 1 for every 2.
    fn for_every(&self, player: usize, amount: i32, per: i32, of: Counted) -> i32 {
        amount * (self.count_of(player, of) / per)
    }

    /// How many of `what` there are for `player`'s card Victory Points or Production. Only
    /// `count_for_card` knows which card's Tile to count next to and whose Card Resources to count.
    fn count_of(&self, player: usize, what: Counted) -> i32 {
        match what {
            Counted::Tag(tag) => self.tags(player, tag),
            Counted::TilesInPlay(kind) => self.board.in_play(kind) as i32,
            Counted::TilesOnMars(kind) => self.board.on_mars(kind) as i32,
            Counted::TagsOfOpponents(tag) => self.opponents(player).map(|other| self.tags(other, tag)).sum(),
            Counted::EventsPlayed => {
                let events = self.players.iter().flat_map(|each| each.played.iter());
                events.filter(|&card| CARD_CATALOG[card].card_type == CardType::Event).count() as i32
            }
            Counted::CardResource(_) | Counted::Adjacent(_) => 0,
        }
    }

    /// Whether `player` can carry out `effects`, as `can_carry_out_with_plants` says, with no plant
    /// gained first.
    pub(crate) fn can_carry_out(&self, player: usize, effects: &Effects) -> bool {
        self.can_carry_out_with_plants(player, effects, 0)
    }

    /// Whether `player` can carry out `effects`, having gained `plants` first (Viral Enhancers): on
    /// their own Resources and Production, with someone to lower the Production it lowers on any
    /// Player, with an Area for each Tile (an Ocean always, as Aquifer: see docs/rules-notes.md), with
    /// an Area to claim, and with a card for the Card Resources that need one. Resources lost are
    /// checked against what the Player holds before paying for the card; no card both costs steel or
    /// titanium and loses some, and heat that the card loses is left out of what may pay for it (see
    /// `usable_heat`).
    pub(crate) fn can_carry_out_with_plants(&self, player: usize, effects: &Effects, plants: i32) -> bool {
        let mut resources = self.players[player].resources;
        resources.plants += plants;
        Resource::ALL.into_iter().all(|resource| resources[resource] + effects.resources[resource] >= 0)
            && self.can_change_production(player, effects.production)
            && self.someone_can_lose_production(player, effects)
            && effects.tiles.iter().all(|&placement| self.can_take_action_placing(player, Some(placement)))
            && (!effects.claim_area || self.board.claimable_areas().next().is_some())
            && effects
                .add_to_another
                .iter()
                .all(|&add| !add.must_have_card || self.cards_to_add_to(player, add).next().is_some())
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
    pub(crate) fn can_make_a_production_change(&self, player: usize, card: usize) -> bool {
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
    /// steel, titanium, heat as MegaCredits (Helion) and MegaCredits for the rest. Steel and titanium
    /// may pay more than the cost, with no change, but a split with a cube the others make unneeded
    /// is never worth taking, so it is left out (see docs/rules-notes.md).
    pub(crate) fn payments(&self, player: usize, card: usize) -> Vec<Payment> {
        let printed = &CARD_CATALOG[card];
        let (steel, titanium) =
            self.usable_cubes(player, printed.has_tag(Tag::Building), printed.has_tag(Tag::Space));
        let heat = self.usable_heat(player, printed.implemented_effects().resources.heat);
        self.ways_to_pay(player, self.card_cost(player, card), steel, titanium, heat)
    }

    /// What `player` pays for `card` now: its printed cost less the discounts of their played
    /// cards and of an Event they played for their next card, but never below 0.
    pub fn card_cost(&self, player: usize, card: usize) -> i32 {
        let printed = &CARD_CATALOG[card];
        let discounts =
            self.players[player].played.intersection(CARDS_WITH.discount).iter().filter_map(|discounting| {
                let discount = CARD_CATALOG[discounting].implemented_effects().discount?;
                discount.tag.is_none_or(|tag| printed.has_tag(tag)).then_some(discount.megacredits)
            });
        let discount = discounts.sum::<i32>() + self.next_card_effect(player).discount;
        (printed.project_cost() - discount).max(0)
    }

    /// Every way `player` may pay `cost` with up to `most_steel` steel, `most_titanium` titanium and
    /// `most_heat` heat, the most MegaCredits first, leaving out a split with a cube or a heat the
    /// others make unneeded (see `payments`).
    pub(crate) fn ways_to_pay(
        &self,
        player: usize,
        cost: i32,
        most_steel: i32,
        most_titanium: i32,
        most_heat: i32,
    ) -> Vec<Payment> {
        let megacredits = self.players[player].resources.megacredits;
        let values = self.cube_values(player);
        let mut payments = Vec::new();
        for titanium in 0..=most_titanium.min(cubes_to_pay(cost, values.titanium)) {
            for steel in 0..=most_steel.min(cubes_to_pay(cost, values.steel)) {
                let covered = values.steel * steel + values.titanium * titanium;
                let unneeded = (steel > 0 && covered - values.steel >= cost)
                    || (titanium > 0 && covered - values.titanium >= cost);
                if unneeded {
                    continue;
                }
                let left = (cost - covered).max(0);
                // Each heat pays 1 MegaCredit, so there is one split for each amount of heat.
                for heat in (left - megacredits).max(0)..=most_heat.min(left) {
                    payments.push(Payment { megacredits: left - heat, steel, titanium, heat });
                }
            }
        }
        payments.sort_by_key(|payment| Reverse(payment.megacredits));
        payments
    }

    /// `player` pays for `card` and plays it from their hand: it joins their played cards and
    /// its effects are carried out. It uses up the effect an Event had on the next card played,
    /// and an Event with such an effect waits on the card after it.
    pub(crate) fn play_card(&mut self, player: usize, card: usize, payment: Payment) {
        self.pay(player, payment);
        let own = &mut self.players[player];
        own.hand.remove(card);
        own.next_card = CARD_CATALOG[card].implemented_effects().next_card.map(|_| card);
        self.log.push(LogEvent::PlayedCard { player, card, payment });
        self.put_into_play(player, card);
    }

    /// `card`, which `player` plays, joins their played cards, sets off Triggers, and its effects are
    /// carried out; once they are done, the Action ends (or with a Prelude Card, the next is played).
    pub(crate) fn put_into_play(&mut self, player: usize, card: usize) {
        self.players[player].played.insert(card);
        self.set_off(Happened::CardPlayed { player, card });
        let effects = CARD_CATALOG[card].implemented_effects();
        // Immigrant City lowers its Production only once its City is placed.
        if card != IMMIGRANT_CITY {
            self.carry_out(player, card, effects);
        }
        // Flooding's taking waits on its Ocean.
        if effects.any_player.is_some() && card != FLOODING {
            self.take_from_any_player_later(card);
        }
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

    /// The Tiles of `card`, which is being played, are placed one at a time, or the Area it claims
    /// is chosen; then the effects it lets its Player choose follow, and the Action ends.
    fn place_card_tiles(&mut self, card: usize) {
        let effects = CARD_CATALOG[card].implemented_effects();
        if !effects.tiles.is_empty() {
            self.placing_for = Some(CardTiles { card, placed: 0 });
        }
        if !effects.choice.is_empty() {
            self.choosing_for = Some(card);
        }
        if effects.claim_area {
            self.wait_on(Waiting::ClaimArea);
        }
        self.finish_unless_placing();
    }

    /// Starts placing the next Tile of the card being played, if it has one left. An Ocean
    /// once all 9 are placed is skipped, as for Aquifer (see docs/rules-notes.md).
    pub(crate) fn place_next_card_tile(&mut self) {
        while let Some(CardTiles { card, placed }) = self.placing_for {
            let effects = CARD_CATALOG[card].implemented_effects();
            let Some(&placement) = effects.tiles.get(placed) else {
                self.placing_for = None;
                if card == IMMIGRANT_CITY {
                    self.finish_immigrant_city();
                }
                return;
            };
            self.placing_for = Some(CardTiles { card, placed: placed + 1 });
            self.place_card_tile(card, placement);
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
        own.heat -= payment.heat;
    }

    /// The current Player has `card`'s Tile to make `placement` with, printed with the card's
    /// symbol if it is a special Tile. An Ocean once all 9 are placed is skipped, as for Aquifer
    /// (see docs/rules-notes.md).
    pub(crate) fn place_card_tile(&mut self, card: usize, placement: Placement) {
        if placement.tile == TileKind::Ocean {
            self.place_ocean(placement.on);
        } else {
            self.place(Placement { special: SpecialTile::of_card(card), ..placement });
        }
    }

    /// Carries out `effects` of `card` for `player`, in the order `Effects` gives, up to the cards
    /// looked at: what follows them is for the card or action to carry on with.
    pub(crate) fn carry_out(&mut self, player: usize, card: usize, effects: &'static Effects) {
        self.change_card_resources(player, card, effects.card_resources);
        if !effects.add_to_another.is_empty() {
            self.adding = Some(Adding { card, additions: &effects.add_to_another });
        }
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
            self.raise_terraform_rating(player, by);
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
