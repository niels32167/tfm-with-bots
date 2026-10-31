//! A set of Project Cards, such as a hand or the cards a Player has played. It is one bit per
//! card, so copying a Game stays a plain value copy (ADR 0004), and its cards always come out
//! in card-number order, never in an order that could differ between runs (ADR 0010).

use crate::cards::PROJECT_CARDS;

const WORDS: usize = 4;
const _: () = assert!(PROJECT_CARDS <= WORDS * 64, "a CardSet has room for every Project Card");

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

    /// The cards in card-number order.
    pub fn iter(self) -> impl Iterator<Item = usize> {
        (0..WORDS).flat_map(move |word| {
            let mut bits = self.bits[word];
            std::iter::from_fn(move || {
                if bits == 0 {
                    return None;
                }
                let bit = bits.trailing_zeros() as usize;
                bits &= bits - 1;
                Some(word * 64 + bit)
            })
        })
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
