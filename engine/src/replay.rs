//! Replays: where a Game started, plus the index of every Option picked, in order.
//! Replaying them always gives the same Game (ADR 0010); save files, undo and bug
//! reports all rely on that. A Game keeps its own Replay up to date as it is played.

use serde::de::Error;
use serde::{Deserialize, Deserializer, Serialize};

use crate::game::{Game, Settings};
use crate::scenario::Scenario;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Replay {
    pub start: Start,
    /// The index of the Option picked for each Decision, in order.
    pub picks: Vec<usize>,
}

/// Where a Game starts: normal setup from its settings, or a Scenario.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Start {
    Settings(Settings),
    Scenario(#[serde(deserialize_with = "scenario_saved_before_the_draft_without_it")] Box<Scenario>),
}

/// Reads a Replay's Scenario. One saved before the Draft existed has no `draft`, and was played
/// without it, though a Scenario has the Draft unless switched off.
fn scenario_saved_before_the_draft_without_it<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> Result<Box<Scenario>, D::Error> {
    let mut scenario = serde_json::Map::deserialize(deserializer)?;
    scenario.entry("draft").or_insert(false.into());
    serde_json::from_value(scenario.into()).map(Box::new).map_err(D::Error::custom)
}

impl Start {
    /// The Game as it stands before any Option is picked.
    pub fn begin(self) -> Result<Game, String> {
        match self {
            Start::Settings(settings) => Game::new(settings),
            Start::Scenario(scenario) => (*scenario).start(),
        }
    }

    pub fn settings(&self) -> Settings {
        match self {
            Start::Settings(settings) => settings.clone(),
            Start::Scenario(scenario) => Settings {
                players: scenario.players.len(),
                seed: scenario.seed,
                implemented_cards_first: false,
                draft: scenario.draft,
                // A Scenario starts past setup: nobody is dealt any, whichever a Player has.
                corporations: false,
            },
        }
    }
}

impl Replay {
    /// The Game after the first `step` picks: step 0 is the start, and `None` means every pick.
    pub fn rebuild(&self, step: Option<usize>) -> Result<Game, String> {
        let step = step.unwrap_or(self.picks.len());
        if step > self.picks.len() {
            return Err(format!("there is no step {step}; the Replay has {} picks", self.picks.len()));
        }
        let mut game = self.start.clone().begin()?;
        for (number, &index) in self.picks[..step].iter().enumerate() {
            game.pick(index, None).map_err(|error| format!("pick {} of the Replay: {error}", number + 1))?;
        }
        Ok(game)
    }
}
