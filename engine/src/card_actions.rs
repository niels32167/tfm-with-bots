//! Card actions: the action of a played Active card or a Corporation (its red arrow), which its Player
//! may use as an Action once per Generation. Actions are effect data like a card's play effects (ADR
//! 0009), carried out by the same rules, plus Power Infrastructure's, Search for Life's and United
//! Nations Mars Initiative's Rust code in `card_code`. What the Player chooses between for an action works the same for a card being played
//! (Imported Hydrogen), so that is here too.

use crate::card_code::{
    POWER_INFRASTRUCTURE, ROBINSON_INDUSTRIES, SEARCH_FOR_LIFE, UNITED_NATIONS_MARS_INITIATIVE,
    energy_for_megacredits,
};
use crate::cards::{ActionCost, CARD_CATALOG};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::LogEvent;
use crate::playing_cards::Payment;
use crate::resources::{Resource, Resources};

/// A Resource change the Player chooses for the action they are using.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ResourceChange {
    /// The action's own Resource alternative at this index (Electro Catapult).
    Alternative(usize),
    /// This much energy spent for as many MegaCredits (Power Infrastructure).
    EnergyForMegaCredits(i32),
}

impl ResourceChange {
    /// The Resources it changes, for the action of `card`.
    pub fn resources(self, card: usize) -> Resources {
        match self {
            ResourceChange::Alternative(index) => {
                CARD_CATALOG[card].implemented_action().resources_choice[index]
            }
            ResourceChange::EnergyForMegaCredits(amount) => energy_for_megacredits(amount),
        }
    }
}

impl Game {
    /// The actions the current Player may use now, by card, in card-number order.
    pub(crate) fn usable_actions(&self) -> impl Iterator<Item = usize> {
        let player = self.current_player;
        let own = &self.players[player];
        own.played.without(own.used_actions).iter().filter(move |&card| self.can_use_action(player, card))
    }

    /// Whether `player` may use the action of `card`, one of their played cards whose action they
    /// haven't used this Generation: they can pay for it and carry it out, a Resource change to
    /// choose included.
    fn can_use_action(&self, player: usize, card: usize) -> bool {
        let Some(action) = CARD_CATALOG[card].action() else { return false };
        action.pay.is_none_or(|cost| {
            self.spendable(player, cost.steel, cost.titanium, action.resources.heat) >= cost.megacredits
        }) && self.can_carry_out(player, action)
            && self.can_make_a_resource_change(player, card)
            && self.can_move_a_card_resource(player, action)
            && (card != SEARCH_FOR_LIFE || self.can_draw())
            && (card != UNITED_NATIONS_MARS_INITIATIVE || self.players[player].terraform_rating_raised)
            && (action.choice.is_empty() || self.alternatives(player, card).next().is_some())
    }

    /// The effects `player` may choose between for `card` or its action, by index: those they can
    /// carry out in full.
    fn alternatives(&self, player: usize, card: usize) -> impl Iterator<Item = usize> {
        let alternatives = CARD_CATALOG[card].alternatives();
        (0..alternatives.len()).filter(move |&index| {
            let alternative = &alternatives[index];
            self.can_carry_out(player, alternative)
                && self.card_resources.on(card) + alternative.card_resources >= 0
        })
    }

    /// Every alternative the current Player may choose for `card` or its action.
    pub(crate) fn alternative_options(&self, card: usize) -> Vec<DecisionOption> {
        self.alternatives(self.current_player, card)
            .map(|alternative| DecisionOption::ChooseEffects { card, alternative })
            .collect()
    }

    /// `player` chooses what the action of `card` does, unless only one alternative is left.
    fn choose_action_alternative(&mut self, player: usize, card: usize) {
        match self.alternative_options(card)[..] {
            [DecisionOption::ChooseEffects { alternative, .. }] => {
                self.carry_out_alternative(player, card, alternative)
            }
            _ => self.wait_on(Waiting::Effects(card)),
        }
    }

    /// `player` carries out the alternative of `card` or its action at `alternative`. The action
    /// ends, or the card being played goes on.
    pub(crate) fn carry_out_alternative(&mut self, player: usize, card: usize, alternative: usize) {
        self.waiting = None;
        self.carry_out(player, card, &CARD_CATALOG[card].alternatives()[alternative]);
        if CARD_CATALOG[card].action().is_some() {
            self.finish_card_action(card);
        } else {
            self.finish_unless_placing();
        }
    }

    /// Offers the current Player what the card they are playing lets them choose, once its Tiles are
    /// placed, and returns whether the Game now waits on it: placing them first is never worse, as
    /// their placement bonus may show a card drawn. With one alternative left, it is carried out
    /// without a Decision.
    pub(crate) fn offer_alternatives(&mut self) -> bool {
        let Some(card) = self.choosing_for.take() else { return false };
        match self.alternative_options(card)[..] {
            [DecisionOption::ChooseEffects { alternative, .. }] => {
                let effects = &CARD_CATALOG[card].alternatives()[alternative];
                self.carry_out(self.current_player, card, effects);
                false
            }
            _ => {
                self.wait_on(Waiting::Effects(card));
                true
            }
        }
    }

    /// Every way the current Player may pay for the action of `card`.
    pub(crate) fn action_payment_options(&self, card: usize) -> Vec<DecisionOption> {
        self.action_payments(self.current_player, card)
            .into_iter()
            .map(|payment| DecisionOption::PayForAction { card, payment })
            .collect()
    }

    /// Every way `player` may pay for the action of `card`, with the steel or titanium its cost
    /// lets them use, the most MegaCredits first.
    fn action_payments(&self, player: usize, card: usize) -> Vec<Payment> {
        let action = CARD_CATALOG[card].implemented_action();
        let ActionCost { megacredits, steel, titanium } =
            action.pay.expect("only an action with a cost is paid for");
        let (steel, titanium) = self.usable_cubes(player, steel, titanium);
        self.ways_to_pay(
            player,
            megacredits,
            steel,
            titanium,
            self.usable_heat(player, action.resources.heat),
            0,
        )
    }

    /// `player` uses the action of `card`: it counts as used for this Generation, they pay for it
    /// (asked how, if there is more than one way), and it is carried out.
    pub(crate) fn use_action(&mut self, player: usize, card: usize) {
        self.players[player].used_actions.insert(card);
        self.log.push(LogEvent::UsedAction { player, card });
        if CARD_CATALOG[card].implemented_action().pay.is_none() {
            return self.carry_out_action(player, card, Payment::NOTHING);
        }
        match self.action_payments(player, card)[..] {
            [only_way] => self.carry_out_action(player, card, only_way),
            _ => self.wait_on(Waiting::ActionPayment(card)),
        }
    }

    /// `player` pays `payment` for the action of `card` and carries it out, in the order `Effects`
    /// gives: what it changes, the cards looked at, the Resource change chosen, then its Tile.
    pub(crate) fn carry_out_action(&mut self, player: usize, card: usize, payment: Payment) {
        self.waiting = None;
        if payment != Payment::NOTHING {
            self.pay(player, payment);
            self.log.push(LogEvent::PaidForAction { player, payment });
        }
        let action = CARD_CATALOG[card].implemented_action();
        self.carry_out(player, card, action);
        if action.any_player.is_some() {
            self.take_from_any_player_later(card);
        }
        if card == SEARCH_FOR_LIFE {
            self.search_for_life(player);
        }
        if card == ROBINSON_INDUSTRIES {
            // One of the six Productions is always the lowest, so there is a change to make.
            return self.choose_production_change(player, card);
        }
        if self.look_at_cards(player, card, action.look_at, true) {
            return;
        }
        if !action.choice.is_empty() {
            return self.choose_action_alternative(player, card);
        }
        match self.resource_change_options(player, card)[..] {
            [] => self.finish_card_action(card),
            [DecisionOption::ChangeResources { change, .. }] => {
                self.change_resources_as_chosen(player, card, change)
            }
            _ => self.wait_on(Waiting::Resources(card)),
        }
    }

    /// The Resource changes `player` may choose between for the action of `card`: none for an
    /// action that offers no such choice.
    pub(crate) fn resource_change_options(&self, player: usize, card: usize) -> Vec<DecisionOption> {
        let changes: Vec<ResourceChange> = if card == POWER_INFRASTRUCTURE {
            (1..=self.players[player].resources.energy).map(ResourceChange::EnergyForMegaCredits).collect()
        } else {
            let alternatives = &CARD_CATALOG[card].implemented_action().resources_choice;
            (0..alternatives.len())
                .filter(|&index| self.can_change_resources(player, alternatives[index]))
                .map(ResourceChange::Alternative)
                .collect()
        };
        changes.into_iter().map(|change| DecisionOption::ChangeResources { card, change }).collect()
    }

    /// Whether `player` can carry out the action of `card` as far as its Resource change goes: true
    /// for an action that has none to choose, and otherwise whether `resource_change_options` has
    /// one, but quicker, as it stops at the first.
    fn can_make_a_resource_change(&self, player: usize, card: usize) -> bool {
        if card == POWER_INFRASTRUCTURE {
            return self.players[player].resources.energy > 0;
        }
        let alternatives = &CARD_CATALOG[card].implemented_action().resources_choice;
        alternatives.is_empty() || alternatives.iter().any(|&by| self.can_change_resources(player, by))
    }

    /// Whether changing `player`'s Resources `by` this leaves none below 0.
    fn can_change_resources(&self, player: usize, by: Resources) -> bool {
        let resources = self.players[player].resources;
        Resource::ALL.into_iter().all(|resource| resources[resource] + by[resource] >= 0)
    }

    /// `player` makes `change` for the action of `card`, and the action ends.
    pub(crate) fn change_resources_as_chosen(&mut self, player: usize, card: usize, change: ResourceChange) {
        self.waiting = None;
        self.change_resources(player, change.resources(card));
        self.finish_card_action(card);
    }

    /// The action of `card` places its Tile, if it has one, and then ends.
    pub(crate) fn finish_card_action(&mut self, card: usize) {
        if let Some(&placement) = CARD_CATALOG[card].implemented_action().tiles.first() {
            self.place_card_tile(card, placement);
        }
        self.finish_unless_placing();
    }
}
