//! The game log. The Game records small events as it goes, and they are turned into
//! plain-language lines only when someone reads the log. Events are plain values,
//! so the log adds little to the cost of copying a Game.

use crate::board::{BonusItem, TileKind, area_label};
use crate::game::{MAX_OCEANS, OCEAN_ADJACENCY_BONUS, PLANTS_PER_GREENERY, StandardProject};

#[derive(Clone, Copy, Debug)]
pub enum LogEvent {
    GenerationBegins { generation: u32, first_player: usize },
    UsedStandardProject { player: usize, project: StandardProject },
    TemperatureRaised { player: usize, temperature: i32 },
    ConvertedPlants { player: usize },
    MegacreditProductionRaised { player: usize, by: i32 },
    TemperatureAlreadyAtMaximum,
    OxygenRaised { player: usize, oxygen: i32 },
    OxygenAlreadyAtMaximum,
    PlacedTile { player: usize, tile: TileKind, area: usize },
    OceansRaised { player: usize, oceans: usize },
    OceansAlreadyAtMaximum,
    PlacementBonus { player: usize, item: BonusItem, amount: i32 },
    AdjacentOceans { player: usize, oceans: usize },
    EndedTurn { player: usize },
    Passed { player: usize },
    ProductionPhase,
    Income { player: usize, terraform_rating: i32, megacredit_production: i32 },
    GameOver,
    FinalScore { player: usize, victory_points: i32 },
}

impl LogEvent {
    pub fn text(&self) -> String {
        match *self {
            LogEvent::GenerationBegins { generation, first_player } => {
                format!("Generation {generation} begins, with {} as first player.", player_name(first_player))
            }
            LogEvent::UsedStandardProject { player, project } => format!(
                "{} uses the {} Standard Project for {} MegaCredits.",
                player_name(player),
                project.name(),
                project.cost()
            ),
            LogEvent::TemperatureRaised { player, temperature } => format!(
                "{} raises Temperature to {temperature} °C and gains 1 Terraform Rating.",
                player_name(player)
            ),
            LogEvent::TemperatureAlreadyAtMaximum => {
                "Temperature is already at its maximum, so it does not rise.".to_string()
            }
            LogEvent::MegacreditProductionRaised { player, by } => {
                format!("{} raises their MegaCredit Production by {by}.", player_name(player))
            }
            LogEvent::ConvertedPlants { player } => {
                format!("{} converts {PLANTS_PER_GREENERY} plants into a Greenery.", player_name(player))
            }
            LogEvent::OxygenRaised { player, oxygen } => {
                format!("{} raises Oxygen to {oxygen} % and gains 1 Terraform Rating.", player_name(player))
            }
            LogEvent::OxygenAlreadyAtMaximum => {
                "Oxygen is already at its maximum, so it does not rise.".to_string()
            }
            LogEvent::PlacedTile { player, tile, area } => {
                format!("{} places {} on {}.", player_name(player), tile.with_article(), area_label(area))
            }
            LogEvent::OceansRaised { player, oceans } => {
                format!(
                    "{} raises Oceans to {oceans} of {MAX_OCEANS} and gains 1 Terraform Rating.",
                    player_name(player)
                )
            }
            LogEvent::OceansAlreadyAtMaximum => {
                format!("All {MAX_OCEANS} Oceans are already placed, so no Ocean is placed.")
            }
            LogEvent::PlacementBonus { player, item: BonusItem::Card, amount } => format!(
                "{} would draw {} from the placement bonus, but there is no deck yet.",
                player_name(player),
                counted(amount, "card", "cards")
            ),
            LogEvent::PlacementBonus { player, item, amount } => format!(
                "{} gains {} from the placement bonus.",
                player_name(player),
                match item {
                    BonusItem::Plant => counted(amount, "plant", "plants"),
                    _ => format!("{amount} {}", item.name()),
                }
            ),
            LogEvent::AdjacentOceans { player, oceans } => format!(
                "{} gains {} MegaCredits for {}.",
                player_name(player),
                OCEAN_ADJACENCY_BONUS * oceans as i32,
                counted(oceans as i32, "adjacent Ocean", "adjacent Oceans")
            ),
            LogEvent::EndedTurn { player } => format!("{} ends their Turn.", player_name(player)),
            LogEvent::Passed { player } => format!("{} passes.", player_name(player)),
            LogEvent::ProductionPhase => "Production phase.".to_string(),
            LogEvent::Income { player, terraform_rating, megacredit_production } => format!(
                "{} gains {} MegaCredits (Terraform Rating {terraform_rating} + MegaCredit Production {megacredit_production}).",
                player_name(player),
                terraform_rating + megacredit_production
            ),
            LogEvent::GameOver => "The Game is over.".to_string(),
            LogEvent::FinalScore { player, victory_points } => {
                format!("{} finishes with {victory_points} Victory Points.", player_name(player))
            }
        }
    }
}

/// "1 plant", "2 plants".
fn counted(amount: i32, one: &str, many: &str) -> String {
    format!("{amount} {}", if amount == 1 { one } else { many })
}

/// Players are numbered from 1 for people, but indexed from 0 everywhere else.
pub fn player_name(index: usize) -> String {
    format!("Player {}", index + 1)
}
