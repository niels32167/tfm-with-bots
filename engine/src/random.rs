//! The Game's one source of randomness, seeded from the Game's seed (ADR 0010).
//!
//! It is SplitMix64 (Steele, Lea and Flood, 2014), written out here rather than taken
//! from a crate: a Replay must give the same Game on any machine and after any
//! dependency update, so the exact sequence of numbers is part of the rules.

#[derive(Clone, Debug)]
pub struct RandomNumbers {
    state: u64,
}

impl RandomNumbers {
    pub fn new(seed: u64) -> RandomNumbers {
        RandomNumbers { state: seed }
    }

    /// A whole number from 0 to `count - 1`, each equally likely.
    pub fn below(&mut self, count: usize) -> usize {
        assert!(count > 0, "there is nothing to pick from");
        let count = count as u64;
        // Numbers at the very top of the range would favour the low results, so draw again.
        let fair_limit = u64::MAX - u64::MAX % count;
        loop {
            let number = self.next();
            if number < fair_limit {
                return (number % count) as usize;
            }
        }
    }

    /// Puts `items` in a random order, each order equally likely (Fisher and Yates, as
    /// Durstenfeld wrote it).
    pub fn shuffle<T>(&mut self, items: &mut [T]) {
        for last in (1..items.len()).rev() {
            items.swap(last, self.below(last + 1));
        }
    }

    fn next(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
}
