//! A set of cards, such as a hand or the cards a Player has played. It is one bit per
//! card, so copying a Game stays a plain value copy (ADR 0004), and its cards always come out
//! in card-number order, never in an order that could differ between runs (ADR 0010).

use crate::cards::CATALOG_CARDS;

const WORDS: usize = 5;
const _: () = assert!(CATALOG_CARDS <= WORDS * 64, "a CardSet has room for every card");

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct CardSet {
    bits: [u64; WORDS],
}

impl CardSet {
    pub fn insert(&mut self, card: usize) {
        self.bits[card / 64] |= 1 << (card % 64);
    }

    pub fn remove(&mut self, card: usize) {
        self.bits[card / 64] &= !(1 << (card % 64));
    }

    pub fn contains(&self, card: usize) -> bool {
        self.bits[card / 64] & (1 << (card % 64)) != 0
    }

    /// The cards in this set or in `other`.
    pub fn union(self, other: CardSet) -> CardSet {
        CardSet { bits: std::array::from_fn(|word| self.bits[word] | other.bits[word]) }
    }

    /// The cards in both this set and `other`.
    pub fn intersection(self, other: CardSet) -> CardSet {
        CardSet { bits: std::array::from_fn(|word| self.bits[word] & other.bits[word]) }
    }

    /// The cards in this set but not in `other`.
    pub fn without(self, other: CardSet) -> CardSet {
        CardSet { bits: std::array::from_fn(|word| self.bits[word] & !other.bits[word]) }
    }

    pub fn len(&self) -> usize {
        self.bits.iter().map(|word| word.count_ones() as usize).sum()
    }

    pub fn is_empty(&self) -> bool {
        self.bits == [0; WORDS]
    }

    /// How many cards of this set come before `card` in card-number order.
    pub fn rank(&self, card: usize) -> usize {
        let words_before: u32 = self.bits[..card / 64].iter().map(|word| word.count_ones()).sum();
        let below_in_its_word = self.bits[card / 64] & ((1 << (card % 64)) - 1);
        (words_before + below_in_its_word.count_ones()) as usize
    }

    /// The cards in card-number order.
    pub fn iter(self) -> impl Iterator<Item = usize> {
        CardsInOrder { bits: self.bits, word: 0 }
    }
}

/// The cards of a set in card-number order. The Game goes through its sets all the time, and most
/// words are empty, so going straight to the next card keeps a larger set from costing more.
struct CardsInOrder {
    bits: [u64; WORDS],
    word: usize,
}

impl Iterator for CardsInOrder {
    type Item = usize;

    #[inline]
    fn next(&mut self) -> Option<usize> {
        while self.word < WORDS {
            let bits = self.bits[self.word];
            if bits != 0 {
                self.bits[self.word] = bits & (bits - 1);
                return Some(self.word * 64 + bits.trailing_zeros() as usize);
            }
            self.word += 1;
        }
        None
    }
}

impl FromIterator<usize> for CardSet {
    fn from_iter<I: IntoIterator<Item = usize>>(cards: I) -> CardSet {
        let mut set = CardSet::default();
        for card in cards {
            set.insert(card);
        }
        set
    }
}
