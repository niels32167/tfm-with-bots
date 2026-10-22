//! A Scenario: a described position to start a Game from instead of normal setup.
//! Tests (and later the dev panel's state editor) build Games this way. Anything a
//! Scenario leaves out takes the normal defaults; an unknown field is an error, so a
//! typo in a test fails loudly instead of being ignored.

use serde::{Deserialize, Serialize};

use crate::game::{
    Game, MAX_TEMPERATURE, MIN_TEMPERATURE, Player, STARTING_MEGACREDITS, STARTING_TERRAFORM_RATING,
    TEMPERATURE_STEP, check_player_count, check_seed,
};
use crate::replay::Start;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Scenario {
    pub seed: u64,
    pub generation: u32,
    /// Who holds the first-player marker. The Scenario starts with their Turn.
    pub first_player: usize,
    pub temperature: i32,
    pub players: Vec<ScenarioPlayer>,
}

impl Default for Scenario {
    fn default() -> Scenario {
        Scenario {
            seed: 0,
            generation: 1,
            first_player: 0,
            temperature: MIN_TEMPERATURE,
            players: vec![ScenarioPlayer::default(); 2],
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ScenarioPlayer {
    pub megacredits: i32,
    pub production: ScenarioProduction,
    pub terraform_rating: i32,
}

impl Default for ScenarioPlayer {
    fn default() -> ScenarioPlayer {
        ScenarioPlayer {
            megacredits: STARTING_MEGACREDITS,
            production: ScenarioProduction::default(),
            terraform_rating: STARTING_TERRAFORM_RATING,
        }
    }
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ScenarioProduction {
    pub megacredits: i32,
}

impl Scenario {
    /// The Game this Scenario describes, or why it can't be set up.
    pub fn start(self) -> Result<Game, String> {
        check_player_count(self.players.len())?;
        check_seed(self.seed)?;
        if self.generation < 1 {
            return Err("the Generation must be 1 or more".to_string());
        }
        if self.first_player >= self.players.len() {
            return Err(format!(
                "the first player must be one of the Players, indexed 0 to {}, not {}",
                self.players.len() - 1,
                self.first_player
            ));
        }
        let on_track = (MIN_TEMPERATURE..=MAX_TEMPERATURE).contains(&self.temperature)
            && (self.temperature - MIN_TEMPERATURE) % TEMPERATURE_STEP == 0;
        if !on_track {
            return Err(format!(
                "Temperature must be a step on the track from {MIN_TEMPERATURE} to {MAX_TEMPERATURE} °C, not {}",
                self.temperature
            ));
        }
        let players = self
            .players
            .iter()
            .map(|player| Player {
                megacredits: player.megacredits,
                megacredit_production: player.production.megacredits,
                terraform_rating: player.terraform_rating,
                passed: false,
            })
            .collect();
        let mut game = Game::prepare(Start::Scenario(self.clone()), self.temperature, players);
        game.begin(self.generation, self.first_player);
        Ok(game)
    }
}
