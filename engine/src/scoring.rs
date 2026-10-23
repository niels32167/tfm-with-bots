//! Final scoring: each Player's Victory Points once the Game is over, how they add up, and
//! who wins.

use serde::Serialize;

use crate::board::TileKind;
use crate::game::Game;
use crate::milestones_and_awards::{Award, MILESTONE_VICTORY_POINTS};

/// One Player's final score. Terraform Rating, Milestones, Awards, Greeneries, Cities and
/// cards add up to the total.
#[derive(Clone, Debug, Serialize)]
pub struct Score {
    pub player: usize,
    pub terraform_rating: i32,
    /// 5 for each Milestone they claimed.
    pub milestones: i32,
    /// From first and second places in the funded Awards.
    pub awards: i32,
    /// 1 for each Greenery they own.
    pub greeneries: i32,
    /// 1 for each Greenery next to each of their Cities, whoever owns the Greenery.
    pub cities: i32,
    /// The Victory Points on the cards they have played.
    pub cards: i32,
    pub total: i32,
    /// The tiebreak: of Players tied on Victory Points, the one with more MegaCredits ranks higher.
    pub megacredits: i32,
    /// 1 for the winner. Players tied on both Victory Points and MegaCredits share a rank.
    pub rank: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Place {
    First,
    Second,
}

impl Place {
    /// As the game log names it, before "place": "first".
    pub fn name(self) -> &'static str {
        match self {
            Place::First => "first",
            Place::Second => "second",
        }
    }

    pub fn victory_points(self) -> i32 {
        match self {
            Place::First => 5,
            Place::Second => 2,
        }
    }
}

/// A Player's place in a funded Award.
#[derive(Clone, Copy, Debug)]
pub struct AwardPlace {
    pub award: Award,
    pub player: usize,
    pub place: Place,
    /// What they have of what the Award measures.
    pub count: i32,
    /// Whether other Players tied with them for this place.
    pub shared: bool,
}

/// Each Player's final score.
pub fn final_scores(game: &Game) -> Vec<Score> {
    let mut awards = vec![0; game.players.len()];
    for place in funded_award_places(game) {
        awards[place.player] += place.place.victory_points();
    }
    let mut scores: Vec<Score> = game
        .players
        .iter()
        .enumerate()
        .map(|(index, player)| {
            let claimed = game.claimed_milestones.iter().filter(|&&by| by == Some(index)).count();
            let milestones = MILESTONE_VICTORY_POINTS * claimed as i32;
            let greeneries = game.board.owned(index, TileKind::Greenery) as i32;
            let cities = game
                .board
                .tiles_of(index)
                .filter(|&(_, kind)| kind == TileKind::City)
                .map(|(area, _)| game.board.adjacent(area, TileKind::Greenery) as i32)
                .sum();
            let cards = game.card_victory_points(index);
            Score {
                player: index,
                terraform_rating: player.terraform_rating,
                milestones,
                awards: awards[index],
                greeneries,
                cities,
                cards,
                total: player.terraform_rating + milestones + awards[index] + greeneries + cities + cards,
                megacredits: player.resources.megacredits,
                rank: 0,
            }
        })
        .collect();
    let ranks: Vec<usize> = scores
        .iter()
        .map(|score| 1 + scores.iter().filter(|other| ranks_above(other, score)).count())
        .collect();
    for (score, rank) in scores.iter_mut().zip(ranks) {
        score.rank = rank;
    }
    scores
}

/// Whether `one` ranks above `other`: more Victory Points, or as many and more MegaCredits.
fn ranks_above(one: &Score, other: &Score) -> bool {
    one.total > other.total || (one.total == other.total && one.megacredits > other.megacredits)
}

/// How a Player who ranks first won.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Win {
    /// With more Victory Points than anyone else.
    Outright,
    /// Tied on Victory Points, but with the most MegaCredits.
    OnMegaCredits,
    /// Tied with others on both Victory Points and MegaCredits.
    Shared,
}

/// Every Player who ranks first, and how they won.
pub fn winners(scores: &[Score]) -> Vec<(usize, Win)> {
    let first: Vec<&Score> = scores.iter().filter(|score| score.rank == 1).collect();
    first
        .iter()
        .map(|winner| {
            let tied_on_victory_points =
                scores.iter().filter(|score| score.total == winner.total).count() > 1;
            let win = if first.len() > 1 {
                Win::Shared
            } else if tied_on_victory_points {
                Win::OnMegaCredits
            } else {
                Win::Outright
            };
            (winner.player, win)
        })
        .collect()
}

/// Every place taken in the funded Awards, Award by Award in the order printed on the board.
pub fn funded_award_places(game: &Game) -> Vec<AwardPlace> {
    Award::ALL
        .into_iter()
        .filter(|award| game.funded_awards[award.index()].is_some())
        .flat_map(|award| award_places(game, award))
        .collect()
}

/// Who takes first and second place in `award`. Every Player tied for a place takes it, even
/// at 0. A tie for first leaves no second place, and 2-player Games have none (see
/// docs/rules-notes.md).
fn award_places(game: &Game, award: Award) -> Vec<AwardPlace> {
    let counts: Vec<i32> = (0..game.players.len()).map(|player| award.count(game, player)).collect();
    let mut places = tied_at(award, &counts, counts.iter().max().copied(), Place::First);
    let one_leader = places.len() == 1;
    if one_leader && counts.len() > 2 {
        let leader = places[0].count;
        let runner_up = counts.iter().filter(|&&count| count < leader).max().copied();
        places.extend(tied_at(award, &counts, runner_up, Place::Second));
    }
    places
}

/// `place` for every Player whose count is `count`.
fn tied_at(award: Award, counts: &[i32], count: Option<i32>, place: Place) -> Vec<AwardPlace> {
    let Some(count) = count else { return Vec::new() };
    let tied: Vec<usize> = (0..counts.len()).filter(|&player| counts[player] == count).collect();
    let shared = tied.len() > 1;
    tied.into_iter().map(|player| AwardPlace { award, player, place, count, shared }).collect()
}
