//! What crosses into Python: the current Decision and the Player View, as plain
//! JSON-shaped values. Every Option gets a readable label for people and structured
//! details for programs (the GUI, and later the AI).

use serde::Serialize;

use crate::game::{ASTEROID_COST, Decision, DecisionKind, DecisionOption, Game, Phase, StandardProject};
use crate::log::player_name;

#[derive(Serialize)]
pub struct DecisionView {
    pub player: usize,
    pub kind: &'static str,
    pub sequence: u64,
    pub options: Vec<OptionView>,
}

#[derive(Serialize)]
pub struct OptionView {
    pub index: usize,
    pub label: String,
    pub details: OptionDetails,
}

#[derive(Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum OptionDetails {
    StandardProject { project: &'static str, cost: i32 },
    EndTurn,
    Pass,
}

/// Everything one Player is allowed to know.
#[derive(Serialize)]
pub struct PlayerView {
    pub viewer: usize,
    pub generation: u32,
    pub phase: &'static str,
    pub temperature: i32,
    /// Whose Turn it is, or None once the Game is over.
    pub current_player: Option<usize>,
    /// How many Actions the current Player has taken in this Turn.
    pub actions_this_turn: u32,
    pub players: Vec<PlayerBoard>,
    /// Each Player's final score once the Game is over, otherwise None.
    pub scores: Option<Vec<ScoreView>>,
}

/// What everyone can see of a Player.
#[derive(Serialize)]
pub struct PlayerBoard {
    pub name: String,
    pub megacredits: i32,
    pub production: Production,
    pub terraform_rating: i32,
    pub passed: bool,
}

#[derive(Serialize)]
pub struct Production {
    pub megacredits: i32,
}

#[derive(Serialize)]
pub struct ScoreView {
    pub player: usize,
    pub terraform_rating: i32,
    pub total: i32,
}

pub fn scores(game: &Game) -> Option<Vec<ScoreView>> {
    let scores = game.scores()?;
    let views = scores
        .iter()
        .map(|score| ScoreView {
            player: score.player,
            terraform_rating: score.terraform_rating,
            total: score.total,
        })
        .collect();
    Some(views)
}

pub fn player_view(game: &Game, viewer: usize) -> PlayerView {
    PlayerView {
        viewer,
        generation: game.generation,
        phase: match game.phase {
            Phase::Action => "action",
            Phase::Over => "over",
        },
        temperature: game.temperature,
        current_player: if game.is_over() { None } else { Some(game.current_player) },
        actions_this_turn: game.actions_this_turn,
        players: game
            .players
            .iter()
            .enumerate()
            .map(|(index, player)| PlayerBoard {
                name: player_name(index),
                megacredits: player.megacredits,
                production: Production { megacredits: player.megacredit_production },
                terraform_rating: player.terraform_rating,
                passed: player.passed,
            })
            .collect(),
        scores: scores(game),
    }
}

pub fn decision(game: &Game) -> Option<DecisionView> {
    game.decision().map(|decision| decision_view(&decision))
}

fn decision_view(decision: &Decision) -> DecisionView {
    DecisionView {
        player: decision.player,
        kind: match decision.kind {
            DecisionKind::Action => "action",
        },
        sequence: decision.sequence,
        options: decision
            .options
            .iter()
            .enumerate()
            .map(|(index, option)| OptionView { index, label: label(option), details: details(option) })
            .collect(),
    }
}

fn label(option: &DecisionOption) -> String {
    match option {
        DecisionOption::UseStandardProject(StandardProject::Asteroid) => {
            format!("Asteroid ({ASTEROID_COST} MegaCredits)")
        }
        DecisionOption::EndTurn => "End Turn".to_string(),
        DecisionOption::Pass => "Pass".to_string(),
    }
}

fn details(option: &DecisionOption) -> OptionDetails {
    match option {
        DecisionOption::UseStandardProject(StandardProject::Asteroid) => {
            OptionDetails::StandardProject { project: "asteroid", cost: ASTEROID_COST }
        }
        DecisionOption::EndTurn => OptionDetails::EndTurn,
        DecisionOption::Pass => OptionDetails::Pass,
    }
}
