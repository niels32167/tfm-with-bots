//! What crosses into Python: the current Decision and the Player View, as plain
//! JSON-shaped values. Every Option gets a readable label for people and structured
//! details for programs (the GUI, and later the AI).

use serde::Serialize;

use crate::game::{Decision, DecisionKind, DecisionOption, Game, Phase, Score};
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
    StandardProject { project: String, cost: i32 },
    EndTurn,
    Pass,
}

/// What one Player is allowed to know (their Player View), or everything (the full
/// view, which has no viewer).
#[derive(Serialize)]
pub struct View {
    /// The Player whose view this is, or None for the full view.
    pub viewer: Option<usize>,
    pub generation: u32,
    pub phase: &'static str,
    pub temperature: i32,
    /// Who holds the first-player marker.
    pub first_player: usize,
    /// Whose Turn it is, or None once the Game is over.
    pub current_player: Option<usize>,
    /// How many Actions the current Player has taken in this Turn.
    pub actions_this_turn: u32,
    pub players: Vec<PlayerBoard>,
    /// Each Player's final score once the Game is over, otherwise None.
    pub scores: Option<Vec<Score>>,
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

pub fn player_view(game: &Game, viewer: usize) -> View {
    view(game, Some(viewer))
}

/// Everything about the Game, for Hotseat and the dev panel. Until there is hidden
/// information (hands, the deck), it shows the same as every Player View.
pub fn full_view(game: &Game) -> View {
    view(game, None)
}

fn view(game: &Game, viewer: Option<usize>) -> View {
    View {
        viewer,
        generation: game.generation,
        phase: match game.phase {
            Phase::Action => "action",
            Phase::Over => "over",
        },
        temperature: game.temperature,
        first_player: game.first_player,
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
        scores: game.scores(),
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
        DecisionOption::UseStandardProject(project) => {
            format!("{} ({} MegaCredits)", project.name(), project.cost())
        }
        DecisionOption::EndTurn => "End Turn".to_string(),
        DecisionOption::Pass => "Pass".to_string(),
    }
}

fn details(option: &DecisionOption) -> OptionDetails {
    match option {
        DecisionOption::UseStandardProject(project) => {
            OptionDetails::StandardProject { project: project.name().to_lowercase(), cost: project.cost() }
        }
        DecisionOption::EndTurn => OptionDetails::EndTurn,
        DecisionOption::Pass => OptionDetails::Pass,
    }
}
