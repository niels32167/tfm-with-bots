//! Card Resources: the markers kept on a card rather than with a Player, such as microbes or
//! science. A card holds one kind of them if its effect data says so (`Effects::holds`), and only
//! once it is played. They are counted in one small array, so copying a Game stays a plain value
//! copy (ADR 0004).

use crate::cards::{AddToAnother, CARD_CATALOG, CARDS_WITH};
use crate::game::{DecisionOption, Game, Waiting};
use crate::log::LogEvent;

/// How many cards can hold Card Resources, Prelude's Psychrophiles included, and so the room a Game
/// keeps for them.
pub const CARDS_HOLDING_CARD_RESOURCES: usize = 19;

/// The Card Resources still to add to other cards for `card`, which the current Player is playing
/// or using the action of.
#[derive(Clone, Copy, Debug)]
pub struct Adding {
    pub card: usize,
    pub additions: &'static [AddToAnother],
}

/// How many Card Resources are on each card that can hold them, in card-number order among those
/// cards. They are 0 on a card that isn't played.
#[derive(Clone, Copy, Debug, Default)]
pub struct CardResources {
    counts: [u16; CARDS_HOLDING_CARD_RESOURCES],
}

impl CardResources {
    /// How many are on `card`: none on a card that holds none.
    pub fn on(&self, card: usize) -> i32 {
        let holders = CARDS_WITH.card_resources;
        if holders.contains(card) { i32::from(self.counts[holders.rank(card)]) } else { 0 }
    }

    /// Puts exactly `amount` on `card`, which holds them.
    pub fn set(&mut self, card: usize, amount: i32) {
        self.counts[CARDS_WITH.card_resources.rank(card)] = amount as u16;
    }
}

impl Game {
    /// Adds Card Resources to `card`, which `player` has played, or removes them below zero.
    pub(crate) fn change_card_resources(&mut self, player: usize, card: usize, by: i32) {
        if by != 0 {
            self.card_resources.set(card, self.card_resources.on(card) + by);
            self.log.push(LogEvent::CardResourcesChanged { player, card, by });
        }
    }

    /// The cards of `player`'s that may get what `add` adds, in card-number order.
    pub(crate) fn cards_to_add_to(&self, player: usize, add: AddToAnother) -> impl Iterator<Item = usize> {
        self.players[player].cards_holding_card_resources().iter().filter(move |&card| {
            add.kind.is_none_or(|kind| CARD_CATALOG[card].holds() == Some(kind))
                && self.card_resources.on(card) >= add.at_least
        })
    }

    /// Offers the current Player the card to add the next Card Resources due to, and returns whether
    /// the Game now waits on it. With one card, they go on it without a Decision; with none, they
    /// are lost.
    pub(crate) fn offer_card_to_add_to(&mut self) -> bool {
        while let Some(Adding { card, additions: [add, rest @ ..] }) = self.adding {
            self.adding = Some(Adding { card, additions: rest });
            let player = self.current_player;
            match self.add_to_card_options(card, *add)[..] {
                [] => self.log.push(LogEvent::NoCardToAddTo { player, add: *add }),
                [DecisionOption::AddToCard { to, amount, .. }] => {
                    self.change_card_resources(player, to, amount)
                }
                _ => {
                    self.wait_on(Waiting::AddToCard { card, add: *add });
                    return true;
                }
            }
        }
        self.adding = None;
        false
    }

    /// Every card the current Player may add what `add` adds to, for `card`.
    pub(crate) fn add_to_card_options(&self, card: usize, add: AddToAnother) -> Vec<DecisionOption> {
        let cards = self.cards_to_add_to(self.current_player, add);
        cards.map(|to| DecisionOption::AddToCard { card, to, amount: add.amount }).collect()
    }

    /// The current Player adds `amount` Card Resources to `to`, and the Action goes on.
    pub(crate) fn add_to_card(&mut self, to: usize, amount: i32) {
        self.waiting = None;
        self.change_card_resources(self.current_player, to, amount);
        self.finish_unless_placing();
    }
}
