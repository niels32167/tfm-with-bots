//! What crosses into Python: the current Decision and the Player View, as plain
//! JSON-shaped values. Every Option gets a readable label for people and structured
//! details for programs (the GUI, and later the AI).

use serde::Serialize;

use crate::board::{AREA_COUNT, Board, TileKind, area_id, area_label, printed, row_and_position};
use crate::game::{
    Decision, DecisionKind, DecisionOption, Game, HEAT_PER_TEMPERATURE_STEP, PLANTS_PER_GREENERY, Phase,
    Score,
};
use crate::log::player_name;
use crate::resources::Resources;

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
    StandardProject {
        project: String,
        cost: i32,
    },
    ConvertPlants {
        plants: i32,
    },
    ConvertHeat {
        heat: i32,
    },
    EndTurn,
    Pass,
    Done,
    /// An Area for the Tile being placed.
    Area {
        area: String,
        tile: TileKind,
    },
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
    /// In percent.
    pub oxygen: i32,
    /// How many Ocean Tiles have been placed.
    pub oceans: usize,
    /// Every Area, on Mars row by row from the top and each row from the left, then off Mars.
    pub board: Vec<AreaView>,
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

/// One Area: what is printed on it, and its Tile if it has one.
#[derive(Serialize)]
pub struct AreaView {
    /// Its name: "E3" on Mars, or "phobos_space_haven" off Mars.
    pub area: String,
    /// The name printed on it, such as "Noctis City", if any.
    pub name: Option<&'static str>,
    /// Its row from the top and position from the left on Mars, both counted from 1,
    /// matching its name. None off Mars.
    pub row: Option<usize>,
    pub position: Option<usize>,
    /// What the Area is kept for: "ocean", or a card's Tile such as "noctis_city".
    pub reserved: Option<&'static str>,
    /// The placement bonus, one entry per item: "steel", "titanium", "plant" or "card".
    pub bonus: Vec<&'static str>,
    pub tile: Option<TileView>,
}

#[derive(Serialize)]
pub struct TileView {
    #[serde(rename = "type")]
    pub kind: TileKind,
    /// The owning Player, or None for an Ocean.
    pub owner: Option<usize>,
}

/// What everyone can see of a Player.
#[derive(Serialize)]
pub struct PlayerBoard {
    pub name: String,
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
    pub passed: bool,
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
            Phase::FinalGreenery => "final_greenery",
            Phase::Over => "over",
        },
        temperature: game.temperature,
        oxygen: game.oxygen,
        oceans: game.board.oceans(),
        board: board_view(&game.board),
        first_player: game.first_player,
        current_player: if game.is_over() { None } else { Some(game.current_player) },
        actions_this_turn: game.actions_this_turn,
        players: game
            .players
            .iter()
            .enumerate()
            .map(|(index, player)| PlayerBoard {
                name: player_name(index),
                resources: player.resources,
                production: player.production,
                terraform_rating: player.terraform_rating,
                passed: player.passed,
            })
            .collect(),
        scores: game.scores(),
    }
}

fn board_view(board: &Board) -> Vec<AreaView> {
    (0..AREA_COUNT)
        .map(|area| {
            let printed = printed(area);
            let row_and_position = row_and_position(area);
            AreaView {
                area: area_id(area),
                name: printed.name,
                row: row_and_position.map(|(row, _)| row + 1),
                position: row_and_position.map(|(_, position)| position + 1),
                reserved: printed.reserved.map(|reservation| reservation.name()),
                bonus: printed.bonus.iter().map(|item| item.name()).collect(),
                tile: board.tile(area).map(|tile| TileView { kind: tile.kind, owner: tile.owner }),
            }
        })
        .collect()
}

pub fn decision(game: &Game) -> Option<DecisionView> {
    game.decision().map(|decision| decision_view(&decision))
}

fn decision_view(decision: &Decision) -> DecisionView {
    DecisionView {
        player: decision.player,
        kind: match decision.kind {
            DecisionKind::Action => "action",
            DecisionKind::Area => "area",
            DecisionKind::FinalGreenery => "final_greenery",
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
        DecisionOption::ConvertPlants => format!("Convert {PLANTS_PER_GREENERY} plants into a Greenery"),
        DecisionOption::ConvertHeat => {
            format!("Convert {HEAT_PER_TEMPERATURE_STEP} heat into a Temperature step")
        }
        DecisionOption::EndTurn => "End Turn".to_string(),
        DecisionOption::Pass => "Pass".to_string(),
        DecisionOption::Done => "Done".to_string(),
        DecisionOption::PlaceTile { tile, area } => {
            format!("Place the {} on {}", tile.name(), area_label(*area))
        }
    }
}

fn details(option: &DecisionOption) -> OptionDetails {
    match option {
        DecisionOption::UseStandardProject(project) => {
            OptionDetails::StandardProject { project: project.id(), cost: project.cost() }
        }
        DecisionOption::ConvertPlants => OptionDetails::ConvertPlants { plants: PLANTS_PER_GREENERY },
        DecisionOption::ConvertHeat => OptionDetails::ConvertHeat { heat: HEAT_PER_TEMPERATURE_STEP },
        DecisionOption::EndTurn => OptionDetails::EndTurn,
        DecisionOption::Pass => OptionDetails::Pass,
        DecisionOption::Done => OptionDetails::Done,
        DecisionOption::PlaceTile { tile, area } => OptionDetails::Area { area: area_id(*area), tile: *tile },
    }
}
