//! A chosen deal: the first player, and the Corporations, Prelude Cards and Project Cards in the order
//! they are dealt and drawn, instead of shuffled. Replaying a Recorded Game through the engine needs it
//! (ticket 10 of phase 2). Cards a deal leaves out are shuffled beneath those it names, with the Game's
//! own seeded random numbers. A deal is part of the settings, so a Replay still reproduces its Game
//! (ADR 0010), and a Game without one draws its random numbers exactly as before.

use serde::{Deserialize, Serialize};

use crate::card_set::CardSet;
use crate::cards::{find_card, find_corporation, find_prelude_card, find_project_card};
use crate::game::Game;
use crate::random::RandomNumbers;

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Deal {
    /// Who holds the first-player marker in Generation 1, indexed from 0.
    pub first_player: usize,
    /// The Corporations, by catalog id, in the order dealt: each Player's in player order from the
    /// first player.
    pub corporations: Vec<String>,
    /// The Prelude Cards, by catalog id, in the order dealt at setup, and then drawn from the Prelude
    /// deck (Valley Trust's first action).
    pub prelude_cards: Vec<String>,
    /// The Project Cards, by catalog id, in the order drawn from the deck, from the setup deal on.
    pub project_cards: Vec<String>,
}

impl Deal {
    /// The Project Cards this deal names, in its order, or why a Game of `players` Players, with Prelude
    /// or without, can't be dealt what it names.
    pub fn project_cards(&self, players: usize, prelude: bool) -> Result<Vec<usize>, String> {
        if self.first_player >= players {
            return Err(format!(
                "the first player must be one of the Players, indexed 0 to {}, not {}",
                players - 1,
                self.first_player
            ));
        }
        let mut named = CardSet::default();
        let mut named_once = |ids: &[String], find: &dyn Fn(&str) -> Option<usize>, kind: &str| {
            ids.iter()
                .map(|id| {
                    let card = find(id).ok_or_else(|| format!("there is no {kind} '{id}'"))?;
                    if named.contains(card) {
                        return Err(format!("'{id}' can be dealt only once"));
                    }
                    named.insert(card);
                    Ok(card)
                })
                .collect::<Result<Vec<usize>, String>>()
        };
        let in_game_with_prelude = |id: &str| find_prelude_card(id).filter(|_| prelude);
        named_once(&self.corporations, &|id| find_corporation(id, prelude), "Corporation")?;
        named_once(&self.prelude_cards, &in_game_with_prelude, "Prelude Card")?;
        named_once(&self.project_cards, &|id| find_project_card(id, prelude), "Project Card")
    }

    /// The cards of `ids`, one of this deal's lists, in its order. Only ever asked of a deal already checked.
    pub fn order(ids: &[String]) -> Vec<usize> {
        ids.iter().filter_map(|id| find_card(id)).collect()
    }
}

/// `cards` in the order to deal or draw them: those of `first` among them, in its order, then the rest
/// shuffled.
fn stacked(
    cards: impl Iterator<Item = usize>,
    first: &[usize],
    random_numbers: &mut RandomNumbers,
) -> Vec<usize> {
    let cards: Vec<usize> = cards.collect();
    let mut rest: Vec<usize> = cards.iter().copied().filter(|card| !first.contains(card)).collect();
    random_numbers.shuffle(&mut rest);
    first.iter().copied().filter(|card| cards.contains(card)).chain(rest).collect()
}

impl Game {
    /// `cards` in the order to deal or draw them: shuffled, but with a deal, those its list `named` names come
    /// first, in its order. Without a deal this draws the same random numbers as shuffling them all.
    pub(crate) fn dealing_order(
        &mut self,
        cards: impl Iterator<Item = usize>,
        named: fn(&Deal) -> &Vec<String>,
    ) -> Vec<usize> {
        let first = self.settings.deal.as_deref().map(|deal| Deal::order(named(deal))).unwrap_or_default();
        stacked(cards, &first, &mut self.random_numbers)
    }
}
