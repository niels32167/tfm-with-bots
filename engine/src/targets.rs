//! Taking from any Player: a card that lowers any Player's Production or removes any Player's
//! Resources (a red-bordered icon) lets its Player pick whom it hits, once its other effects and
//! its Tiles are done. It is effect data (`cards::AnyPlayer`), plus Flooding's Rust code in
//! `card_code`, which takes only from the owners of Tiles next to its Ocean.
//!
//! The target Decision leaves out every Option that only does worse for its Player (see
//! docs/rules-notes.md, "Taking from any Player"): lowering their own Production while an opponent
//! can lose it, removing their own Resources or Card Resources while an opponent has some, and taking
//! less than the card allows. Pets' animals can't be removed by anyone, and Protected Habitats keeps
//! its Player's plants, animals and microbes from opponents.

use crate::board::adjacent_areas;
use crate::card_code::{PETS, PROTECTED_HABITATS};
use crate::cards::{AnyPlayer, CARD_CATALOG, CardResource, Effects, Removal};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::LogEvent;
use crate::resources::{Resource, Resources};

/// A card's taking from any Player, due once the card being played is done with its Tiles: the card
/// whose `any_player` effect it is (Heat Trappers' too, when Robotic Workforce copies its
/// production box), and for Flooding, the Area of its Ocean, next to which its targets own a Tile.
#[derive(Clone, Copy, Debug)]
pub struct Targeting {
    pub card: usize,
    pub next_to: Option<usize>,
}

/// What the card takes from the Player targeted: Production steps, or Resources removed or stolen,
/// each written as the change to that Player (below zero).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Taking {
    Production(Resources),
    Resources { resources: Resources, stolen: bool },
}

/// The `any_player` effect of `card` or of its action, which every card with a taking has.
fn any_player(card: usize) -> &'static AnyPlayer {
    let printed = &CARD_CATALOG[card];
    let taking = printed.implemented_effects().any_player.as_ref();
    taking
        .or_else(|| printed.implemented_action().any_player.as_ref())
        .expect("only a card with a taking takes")
}

/// Whether `card` steals the Resources it removes (Hired Raiders).
pub fn steals(card: usize) -> bool {
    matches!(any_player(card), AnyPlayer::Steal(_))
}

impl Game {
    /// Whether someone can lose every step of the Production that `effects` lowers on any Player,
    /// once `player` has made its own Production change: an opponent, or `player` themselves. True
    /// for effects that lower none. Raising their own Production first is never worse for the
    /// Player than lowering it first, so it is checked that way (see docs/rules-notes.md).
    pub(crate) fn someone_can_lose_production(&self, player: usize, effects: &Effects) -> bool {
        let lowered = effects.any_player_production();
        if lowered.is_zero() {
            return true;
        }
        let mut both = effects.production;
        for resource in Resource::ALL {
            both[resource] += lowered[resource];
        }
        self.opponents(player).any(|other| self.can_change_production(other, lowered))
            || self.can_change_production(player, both)
    }

    /// Every Player other than `player`, in player number order.
    pub(crate) fn opponents(&self, player: usize) -> impl Iterator<Item = usize> + use<> {
        (0..self.players.len()).filter(move |&other| other != player)
    }

    /// The card being played takes from any Player once its Tiles are placed: Robotic Workforce's
    /// copy of Heat Trappers' box included.
    pub(crate) fn take_from_any_player_later(&mut self, card: usize) {
        self.targeting = Some(Targeting { card, next_to: None });
    }

    /// Offers the current Player, done with the card's Tiles, the target of its taking if one is
    /// due, and returns whether the Game now waits on it. With one Option only, which is a target
    /// for their Production, it is taken without a Decision; with nobody to take from, nothing is.
    pub(crate) fn offer_target(&mut self) -> bool {
        let Some(targeting) = self.targeting.take() else { return false };
        match self.target_options(targeting)[..] {
            [] => false,
            [DecisionOption::Target { card, player, alternative }] => {
                self.take_from(card, player, alternative);
                false
            }
            [DecisionOption::MoveCardResource { card, owner, from }] => {
                self.move_card_resource(card, owner, from);
                false
            }
            _ => {
                self.wait_on(Waiting::Target(targeting));
                true
            }
        }
    }

    /// The targets the current Player may pick for `targeting`. Lowering Production: each
    /// opponent who can lose every step, or if none can, the Player themselves. Removing
    /// Resources: each opponent who has some of an alternative's Resources (for Flooding, only the
    /// owners of a Tile next to its Ocean) or a card with some of its Card Resources, unless
    /// Protected Habitats keeps them, and removing nothing, unless there is nobody to take from.
    /// Moving a Card Resource: `cards_to_take_from`.
    pub(crate) fn target_options(&self, targeting: Targeting) -> Vec<DecisionOption> {
        let Targeting { card, next_to } = targeting;
        let player = self.current_player;
        let target =
            |other: usize, alternative: usize| DecisionOption::Target { card, player: other, alternative };
        let alternatives = match any_player(card) {
            &AnyPlayer::Production(lowered) => {
                let opponents: Vec<DecisionOption> = self
                    .opponents(player)
                    .filter(|&other| self.can_change_production(other, lowered))
                    .map(|other| target(other, 0))
                    .collect();
                if !opponents.is_empty() || !self.can_change_production(player, lowered) {
                    return opponents;
                }
                return vec![target(player, 0)];
            }
            &AnyPlayer::MoveCardResource(kind) => {
                let cards = self.cards_to_take_from(player, kind);
                let moving = |(owner, from)| DecisionOption::MoveCardResource { card, owner, from };
                return cards.into_iter().map(moving).collect();
            }
            AnyPlayer::Remove(alternatives) | AnyPlayer::Steal(alternatives) => alternatives,
        };
        let owns_a_tile_next_to = |other: usize| {
            next_to.is_none_or(|area| {
                adjacent_areas(area)
                    .any(|next| self.board.tile(next).is_some_and(|tile| tile.owner == Some(other)))
            })
        };
        let mut options = Vec::new();
        for other in self.opponents(player).filter(|&other| owns_a_tile_next_to(other)) {
            for (alternative, removal) in alternatives.iter().enumerate() {
                match *removal {
                    Removal::Resources(amounts) => {
                        if !self.removable_from_opponent(other, amounts).is_zero() {
                            options.push(target(other, alternative));
                        }
                    }
                    Removal::FromACard { card_resource, amount } => {
                        options.extend(self.cards_to_remove_from(other, card_resource, player).map(|from| {
                            let amount = amount.min(self.card_resources.on(from));
                            DecisionOption::RemoveFromCard { card, owner: other, from, amount }
                        }));
                    }
                }
            }
        }
        if !options.is_empty() {
            options.push(DecisionOption::RemoveNothing(card));
        }
        options
    }

    /// Whether Protected Habitats keeps `owner`'s plants, animals and microbes from their opponents.
    fn is_protected(&self, owner: usize) -> bool {
        self.players[owner].played.contains(PROTECTED_HABITATS)
    }

    /// The cards of `owner`'s that `by` may remove a Card Resource of this kind from: those with some
    /// on them, but for Pets, whose animals nobody may remove, and none of an opponent's with
    /// Protected Habitats.
    fn cards_to_remove_from(
        &self,
        owner: usize,
        kind: CardResource,
        by: usize,
    ) -> impl Iterator<Item = usize> {
        let kept = owner != by
            && self.is_protected(owner)
            && matches!(kind, CardResource::Animal | CardResource::Microbe);
        self.players[owner].cards_holding_card_resources().iter().filter(move |&card| {
            !kept
                && card != PETS
                && CARD_CATALOG[card].holds() == Some(kind)
                && self.card_resources.on(card) > 0
        })
    }

    /// The cards `player` may move a Card Resource of this kind from, and their owners: the
    /// opponents' cards they may remove from, or if there are none, their own, the card getting it
    /// included.
    fn cards_to_take_from(&self, player: usize, kind: CardResource) -> Vec<(usize, usize)> {
        let of_owner =
            |owner: usize| self.cards_to_remove_from(owner, kind, player).map(move |card| (owner, card));
        let opponents: Vec<(usize, usize)> = self.opponents(player).flat_map(of_owner).collect();
        if opponents.is_empty() { of_owner(player).collect() } else { opponents }
    }

    /// Whether `player` can find a Card Resource for `action` to move: true for an action that moves
    /// none.
    pub(crate) fn can_move_a_card_resource(&self, player: usize, action: &Effects) -> bool {
        match action.any_player {
            Some(AnyPlayer::MoveCardResource(kind)) => (0..self.players.len())
                .any(|owner| self.cards_to_remove_from(owner, kind, player).next().is_some()),
            _ => true,
        }
    }

    /// The current Player moves 1 Card Resource from `from`, a card of `owner`'s, to `card`.
    fn move_card_resource(&mut self, card: usize, owner: usize, from: usize) {
        self.card_resources.set(from, self.card_resources.on(from) - 1);
        self.card_resources.set(card, self.card_resources.on(card) + 1);
        self.log.push(LogEvent::MovedCardResource { player: self.current_player, owner, from, card });
    }

    /// The current Player removes `amount` Card Resources from `from`, a card of `owner`'s, and the
    /// Action goes on.
    pub(crate) fn remove_from_card(&mut self, owner: usize, from: usize, amount: i32) {
        self.waiting = None;
        self.card_resources.set(from, self.card_resources.on(from) - amount);
        self.log.push(LogEvent::RemovedFromCard { player: self.current_player, owner, from, amount });
        self.finish_unless_placing();
    }

    /// The current Player picks `from`, a card of `owner`'s, for the action of `card`, and the
    /// Action goes on.
    pub(crate) fn move_card_resource_as_picked(&mut self, card: usize, owner: usize, from: usize) {
        self.waiting = None;
        self.move_card_resource(card, owner, from);
        self.finish_unless_placing();
    }

    /// What `card` takes from `target` with its alternative at `alternative` (0 for Production):
    /// its Production steps, or as much of each Resource as they have, up to the amount written.
    pub fn taking(&self, card: usize, target: usize, alternative: usize) -> Taking {
        match any_player(card) {
            &AnyPlayer::Production(lowered) => Taking::Production(lowered),
            AnyPlayer::Remove(alternatives) | AnyPlayer::Steal(alternatives) => {
                let Removal::Resources(amounts) = alternatives[alternative] else {
                    panic!("removing from a card takes from a card, not a Player")
                };
                Taking::Resources {
                    resources: self.removable(target, amounts).times(-1),
                    stolen: steals(card),
                }
            }
            AnyPlayer::MoveCardResource(_) => {
                panic!("moving a Card Resource takes from a card, not a Player")
            }
        }
    }

    /// `removable`, leaving out the plants Protected Habitats keeps from `target`'s opponents.
    fn removable_from_opponent(&self, target: usize, amounts: Resources) -> Resources {
        let mut removable = self.removable(target, amounts);
        if self.is_protected(target) {
            removable.plants = 0;
        }
        removable
    }

    /// As much of each of `amounts` as `target` has.
    fn removable(&self, target: usize, amounts: Resources) -> Resources {
        let mut removable = Resources::default();
        for resource in Resource::ALL {
            removable[resource] = amounts[resource].min(self.players[target].resources[resource]);
        }
        removable
    }

    /// The current Player takes what `card` takes from `target`, with its alternative at
    /// `alternative`.
    pub(crate) fn take_from(&mut self, card: usize, target: usize, alternative: usize) {
        let player = self.current_player;
        match self.taking(card, target, alternative) {
            Taking::Production(by) => {
                for resource in Resource::ALL.into_iter().filter(|&resource| by[resource] != 0) {
                    self.players[target].production[resource] += by[resource];
                    self.log.push(LogEvent::LoweredProductionOf {
                        player,
                        target,
                        resource,
                        by: -by[resource],
                    });
                }
            }
            Taking::Resources { resources, stolen } => {
                for resource in Resource::ALL.into_iter().filter(|&resource| resources[resource] != 0) {
                    let amount = -resources[resource];
                    self.players[target].resources[resource] -= amount;
                    if stolen {
                        self.players[player].resources[resource] += amount;
                    }
                    self.log.push(LogEvent::RemovedResources { player, target, resource, amount, stolen });
                }
            }
        }
    }

    /// The current Player picks `target` for the taking the Game waits on, and the Action goes on.
    pub(crate) fn take_as_picked(&mut self, card: usize, target: usize, alternative: usize) {
        self.waiting = None;
        self.take_from(card, target, alternative);
        self.finish_unless_placing();
    }

    /// The current Player removes, or steals, nothing with `card`, and the Action goes on.
    pub(crate) fn remove_nothing(&mut self, card: usize) {
        self.waiting = None;
        self.log.push(LogEvent::RemovedNothing { player: self.current_player, card, stolen: steals(card) });
        self.finish_unless_placing();
    }
}
