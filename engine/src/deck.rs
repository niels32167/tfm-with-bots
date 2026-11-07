//! The deck: the Project Cards face down, in order. It is a fixed-size array, so copying a
//! Game stays a plain value copy (ADR 0004), and only the Game's own seeded random numbers
//! ever shuffle it (ADR 0010).

use crate::card_set::CardSet;
use crate::cards::{PRELUDE_PROJECT_CARDS, PRELUDE_PROJECT_CARDS_END, PROJECT_CARDS};
use crate::random::RandomNumbers;

/// The most cards a deck holds: every Project Card of a Game with Prelude.
const MOST_CARDS: usize = PROJECT_CARDS + PRELUDE_PROJECT_CARDS;

const _: () = assert!(PRELUDE_PROJECT_CARDS_END <= u8::MAX as usize, "a Project Card's index fits in a byte");

#[derive(Clone, Copy, Debug)]
pub struct Deck {
    /// The cards from the bottom up, so the top card is `cards[size - 1]`.
    cards: [u8; MOST_CARDS],
    size: u8,
}

impl Deck {
    pub const EMPTY: Deck = Deck { cards: [0; MOST_CARDS], size: 0 };

    /// Every one of the Game's `project_cards` neither `outside` the deck nor in `top`, shuffled,
    /// beneath the cards of `top`, the first of which is drawn first.
    pub fn shuffled(
        project_cards: CardSet,
        outside: CardSet,
        top: &[usize],
        random_numbers: &mut RandomNumbers,
    ) -> Deck {
        let beneath = project_cards.without(outside).iter().filter(|card| !top.contains(card)).collect();
        let mut deck = Deck::shuffled_from(beneath, random_numbers);
        for &card in top.iter().rev() {
            deck.put_on_top(card);
        }
        deck
    }

    /// A deck of exactly `cards`, shuffled.
    pub fn shuffled_from(cards: CardSet, random_numbers: &mut RandomNumbers) -> Deck {
        let mut deck = Deck::EMPTY;
        for card in cards.iter() {
            deck.put_on_top(card);
        }
        random_numbers.shuffle(&mut deck.cards[..deck.size as usize]);
        deck
    }

    fn put_on_top(&mut self, card: usize) {
        self.cards[self.size as usize] = card as u8;
        self.size += 1;
    }

    /// Takes the top card, unless the deck is empty.
    pub fn draw(&mut self) -> Option<usize> {
        self.size = self.size.checked_sub(1)?;
        Some(self.cards[self.size as usize] as usize)
    }

    pub fn len(&self) -> usize {
        self.size as usize
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    /// The cards from the top down.
    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.cards[..self.size as usize].iter().rev().map(|&card| card as usize)
    }
}
