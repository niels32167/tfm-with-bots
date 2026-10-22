//! The game log. The Game records small events as it goes, and they are turned into
//! plain-language lines only when someone reads the log. Events are plain values,
//! so the log adds little to the cost of copying a Game.

use crate::game::StandardProject;

#[derive(Clone, Copy, Debug)]
pub enum LogEvent {
    GenerationBegins { generation: u32 },
    UsedStandardProject { player: usize, project: StandardProject, cost: i32 },
    TemperatureRaised { player: usize, temperature: i32 },
    TemperatureAlreadyAtMaximum,
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
            LogEvent::GenerationBegins { generation } => format!("Generation {generation} begins."),
            LogEvent::UsedStandardProject { player, project, cost } => format!(
                "{} uses the {} Standard Project for {cost} MegaCredits.",
                player_name(player),
                standard_project_name(project)
            ),
            LogEvent::TemperatureRaised { player, temperature } => format!(
                "{} raises Temperature to {temperature} °C and gains 1 Terraform Rating.",
                player_name(player)
            ),
            LogEvent::TemperatureAlreadyAtMaximum => {
                "Temperature is already at its maximum, so it does not rise.".to_string()
            }
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

/// Players are numbered from 1 for people, but indexed from 0 everywhere else.
pub fn player_name(index: usize) -> String {
    format!("Player {}", index + 1)
}

pub fn standard_project_name(project: StandardProject) -> &'static str {
    match project {
        StandardProject::Asteroid => "Asteroid",
    }
}
