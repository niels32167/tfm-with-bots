//! The Random Bot inside the engine: it plays a Game on by picking one of the offered
//! Options at random, for the speed benchmark and, later, search (ADR 0004). Its picks go
//! into the Game's Replay like any others, so the Replay reproduces what it played.

use crate::game::Game;
use crate::random::RandomNumbers;

/// Picks random Options for every Player: `picks` of them, or until the Game is over. The
/// same `seed` always picks the same way from the same position. The picks draw on their
/// own random numbers, never the Game's, so they leave the Game's shuffles as they were.
pub fn play_randomly(game: &mut Game, seed: u64, picks: Option<usize>) {
    let mut random_numbers = RandomNumbers::new(seed);
    for _ in 0..picks.unwrap_or(usize::MAX) {
        let Some(decision) = game.decision() else { return };
        let index = random_numbers.below(decision.options.len());
        game.apply_pick(&decision, index);
    }
}
