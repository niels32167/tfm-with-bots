//! The deck: the Project Cards face down, in order. It is a fixed-size array, so copying a
//! Game stays a plain value copy (ADR 0004), and only the Game's own seeded random numbers
//! ever shuffle it (ADR 0010).

use crate::card_set::CardSet;
use crate::cards::PROJECT_CARDS;
use crate::random::RandomNumbers;

const _: () = assert!(PROJECT_CARDS <= u8::MAX as usize, "a card index fits in a byte");

#[derive(Clone, Copy, Debug)]
pub struct Deck {
    /// The cards from the bottom up, so the top card is `cards[size - 1]`.
    cards: [u8; PROJECT_CARDS],
    size: u8,
}

impl Deck {
    pub const EMPTY: Deck = Deck { cards: [0; PROJECT_CARDS], size: 0 };

    /// Every Project Card neither `outside` the deck nor in `top`, shuffled, beneath the
    /// cards of `top`, the first of which is drawn first.
    pub fn shuffled(outside: CardSet, top: &[usize], random_numbers: &mut RandomNumbers) -> Deck {
        let mut deck = Deck::EMPTY;
        for card in 0..PROJECT_CARDS {
            if !outside.contains(card) && !top.contains(&card) {
                deck.put_on_top(card);
            }
        }
        random_numbers.shuffle(&mut deck.cards[..deck.size as usize]);
        for &card in top.iter().rev() {
            deck.put_on_top(card);
        }
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

    /// The cards from the top down.
    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.cards[..self.size as usize].iter().rev().map(|&card| card as usize)
    }
}
