//! The rules: the state of a Game, the Decision it is waiting on, and what each Option does.
//!
//! The Game is always either over or waiting on exactly one Decision for one Player
//! (ADR 0002). Picking one of that Decision's Options is the only way it moves forward.
//! The state is a plain value with no shared references, so copying a Game is cheap
//! (ADR 0004), and nothing in it depends on the clock or on hash-map order (ADR 0010).

use std::fmt;

use serde::{Deserialize, Serialize};

use crate::log::LogEvent;
use crate::random::RandomNumbers;
use crate::replay::{Replay, Start};

pub const MIN_PLAYERS: usize = 2;
pub const MAX_PLAYERS: usize = 5;

/// The largest seed. Replays travel as JSON, and some JSON readers (the browser's among
/// them) hold numbers as doubles, which are exact only up to 2^53 - 1.
pub const MAX_SEED: u64 = (1 << 53) - 1;

/// Temperature is in °C. It starts at -30 and rises in steps of 2 up to +8.
pub const MIN_TEMPERATURE: i32 = -30;
pub const MAX_TEMPERATURE: i32 = 8;
pub const TEMPERATURE_STEP: i32 = 2;

pub const STARTING_TERRAFORM_RATING: i32 = 20;

/// Temporary until Corporations exist: every Player starts with this many MegaCredits,
/// the amount the Beginner Corporation gives.
pub const STARTING_MEGACREDITS: i32 = 42;

pub const ACTIONS_PER_TURN: u32 = 2;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Settings {
    pub players: usize,
    pub seed: u64,
}

#[derive(Clone, Debug)]
pub struct Player {
    pub megacredits: i32,
    pub megacredit_production: i32,
    pub terraform_rating: i32,
    /// Passed for the rest of this Generation's Action phase.
    pub passed: bool,
}

impl Player {
    pub fn new() -> Player {
        Player {
            megacredits: STARTING_MEGACREDITS,
            megacredit_production: 0,
            terraform_rating: STARTING_TERRAFORM_RATING,
            passed: false,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Action,
    Over,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StandardProject {
    Asteroid,
}

impl StandardProject {
    pub fn name(self) -> &'static str {
        match self {
            StandardProject::Asteroid => "Asteroid",
        }
    }

    /// The printed price in MegaCredits.
    pub fn cost(self) -> i32 {
        match self {
            StandardProject::Asteroid => 14,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecisionKind {
    /// Choose an Action, end the Turn, or Pass.
    Action,
}

/// One of the answers a Decision offers. (Named `DecisionOption` because Rust already has `Option`.)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecisionOption {
    UseStandardProject(StandardProject),
    EndTurn,
    Pass,
}

#[derive(Clone, Debug)]
pub struct Decision {
    pub player: usize,
    pub kind: DecisionKind,
    /// How many Options have been picked before this Decision. A pick may name it, so a
    /// stale pick (say, a double click) is rejected instead of answering the next Decision.
    pub sequence: u64,
    pub options: Vec<DecisionOption>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Score {
    pub player: usize,
    pub terraform_rating: i32,
    pub total: i32,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PickError {
    GameOver,
    StaleDecision { current: u64, given: u64 },
    NoSuchOption { index: usize, count: usize },
}

impl fmt::Display for PickError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            PickError::GameOver => write!(f, "the Game is over, so there is no Decision to answer"),
            PickError::StaleDecision { current, given } => write!(
                f,
                "stale pick: it answers Decision {given}, but the Game is waiting on Decision {current}"
            ),
            PickError::NoSuchOption { index, count } => {
                write!(f, "there is no Option {index}; the Decision has {count} Options")
            }
        }
    }
}

#[derive(Clone, Debug)]
pub struct Game {
    pub settings: Settings,
    pub generation: u32,
    pub phase: Phase,
    pub temperature: i32,
    pub players: Vec<Player>,
    /// Who holds the first-player marker, and so takes the first Turn of this Generation.
    pub first_player: usize,
    /// Whose Turn it is during the Action phase.
    pub current_player: usize,
    /// How many Actions the current Player has taken in this Turn.
    pub actions_this_turn: u32,
    pub log: Vec<LogEvent>,
    /// Seeded from the settings; every random event in the Game draws from it.
    pub random_numbers: RandomNumbers,
    /// Where this Game started and every Option picked since.
    pub replay: Replay,
}

impl Game {
    /// A new Game from its settings, at the start of Generation 1.
    pub fn new(settings: Settings) -> Result<Game, String> {
        check_player_count(settings.players)?;
        check_seed(settings.seed)?;
        let players = vec![Player::new(); settings.players];
        let mut game = Game::prepare(Start::Settings(settings), MIN_TEMPERATURE, players);
        let first_player = game.random_numbers.below(game.players.len());
        game.begin(1, first_player);
        Ok(game)
    }

    /// A Game with everything in place, waiting for `begin` to start its first Generation.
    pub fn prepare(start: Start, temperature: i32, players: Vec<Player>) -> Game {
        let settings = start.settings();
        Game {
            random_numbers: RandomNumbers::new(settings.seed),
            replay: Replay { start, picks: Vec::new() },
            settings,
            generation: 0,
            phase: Phase::Action,
            temperature,
            players,
            first_player: 0,
            current_player: 0,
            actions_this_turn: 0,
            log: Vec::new(),
        }
    }

    pub fn is_over(&self) -> bool {
        self.phase == Phase::Over
    }

    /// The Decision the Game is waiting on, or `None` once it is over.
    pub fn decision(&self) -> Option<Decision> {
        match self.phase {
            Phase::Over => None,
            Phase::Action => Some(Decision {
                player: self.current_player,
                kind: DecisionKind::Action,
                sequence: self.replay.picks.len() as u64,
                options: self.action_options(),
            }),
        }
    }

    /// Answers the current Decision with its Option at `index`. If `sequence` is given,
    /// it must be the current Decision's sequence number.
    pub fn pick(&mut self, index: usize, sequence: Option<u64>) -> Result<(), PickError> {
        let decision = self.decision().ok_or(PickError::GameOver)?;
        if let Some(given) = sequence
            && given != decision.sequence
        {
            return Err(PickError::StaleDecision { current: decision.sequence, given });
        }
        let count = decision.options.len();
        let option = *decision.options.get(index).ok_or(PickError::NoSuchOption { index, count })?;
        self.replay.picks.push(index);
        self.resolve(option);
        Ok(())
    }

    /// Each Player's final score, once the Game is over. For now it is just Terraform Rating.
    pub fn scores(&self) -> Option<Vec<Score>> {
        if !self.is_over() {
            return None;
        }
        let scores = self
            .players
            .iter()
            .enumerate()
            .map(|(index, player)| Score {
                player: index,
                terraform_rating: player.terraform_rating,
                total: player.terraform_rating,
            })
            .collect();
        Some(scores)
    }

    fn action_options(&self) -> Vec<DecisionOption> {
        let player = &self.players[self.current_player];
        let mut options = Vec::new();
        // Asteroid is still offered at maximum Temperature, where it does nothing (see docs/rules-notes.md).
        let asteroid = StandardProject::Asteroid;
        if player.megacredits >= asteroid.cost() {
            options.push(DecisionOption::UseStandardProject(asteroid));
        }
        // Once everyone else has passed, ending the Turn would only start another one.
        if self.actions_this_turn > 0 && self.another_player_still_in() {
            options.push(DecisionOption::EndTurn);
        }
        options.push(DecisionOption::Pass);
        options
    }

    fn resolve(&mut self, option: DecisionOption) {
        let player = self.current_player;
        match option {
            DecisionOption::UseStandardProject(project) => {
                self.players[player].megacredits -= project.cost();
                self.log.push(LogEvent::UsedStandardProject { player, project });
                match project {
                    StandardProject::Asteroid => self.raise_temperature(player),
                }
                self.finish_action();
            }
            DecisionOption::EndTurn => {
                self.log.push(LogEvent::EndedTurn { player });
                self.end_turn();
            }
            DecisionOption::Pass => {
                self.players[player].passed = true;
                self.log.push(LogEvent::Passed { player });
                self.end_turn();
            }
        }
    }

    fn finish_action(&mut self) {
        self.actions_this_turn += 1;
        if self.actions_this_turn == ACTIONS_PER_TURN {
            self.end_turn();
        }
    }

    /// The next Player who hasn't passed takes a Turn. Once everyone has passed,
    /// the Production phase follows.
    fn end_turn(&mut self) {
        self.actions_this_turn = 0;
        match self.next_player_still_in() {
            Some(next) => self.current_player = next,
            None => self.production_phase(),
        }
    }

    /// Looks round the table from the Player after the current one, ending with the current one.
    fn next_player_still_in(&self) -> Option<usize> {
        let count = self.players.len();
        (1..=count)
            .map(|offset| (self.current_player + offset) % count)
            .find(|&index| !self.players[index].passed)
    }

    fn another_player_still_in(&self) -> bool {
        self.players.iter().enumerate().any(|(index, player)| index != self.current_player && !player.passed)
    }

    fn production_phase(&mut self) {
        self.log.push(LogEvent::ProductionPhase);
        for (index, player) in self.players.iter_mut().enumerate() {
            player.megacredits += player.terraform_rating + player.megacredit_production;
            self.log.push(LogEvent::Income {
                player: index,
                terraform_rating: player.terraform_rating,
                megacredit_production: player.megacredit_production,
            });
        }
        if self.temperature >= MAX_TEMPERATURE {
            self.end_game();
        } else {
            // The first-player marker passes clockwise, to the next Player.
            self.first_player = (self.first_player + 1) % self.players.len();
            self.begin_generation(self.generation + 1);
        }
    }

    /// Hands the first-player marker to `first_player` and begins `generation`.
    pub fn begin(&mut self, generation: u32, first_player: usize) {
        self.first_player = first_player;
        self.begin_generation(generation);
    }

    /// The first Player takes the first Turn, and everyone is back in the Action phase.
    fn begin_generation(&mut self, generation: u32) {
        self.generation = generation;
        for player in &mut self.players {
            player.passed = false;
        }
        self.current_player = self.first_player;
        self.actions_this_turn = 0;
        self.log.push(LogEvent::GenerationBegins { generation, first_player: self.first_player });
    }

    fn end_game(&mut self) {
        self.phase = Phase::Over;
        self.log.push(LogEvent::GameOver);
        for score in self.scores().unwrap_or_default() {
            self.log.push(LogEvent::FinalScore { player: score.player, victory_points: score.total });
        }
    }

    /// Raises Temperature one step, which gives `player` one Terraform Rating.
    /// At its maximum, Temperature stays put and nobody gains anything.
    fn raise_temperature(&mut self, player: usize) {
        if self.temperature >= MAX_TEMPERATURE {
            self.log.push(LogEvent::TemperatureAlreadyAtMaximum);
            return;
        }
        self.temperature += TEMPERATURE_STEP;
        self.players[player].terraform_rating += 1;
        self.log.push(LogEvent::TemperatureRaised { player, temperature: self.temperature });
    }
}

pub fn check_seed(seed: u64) -> Result<(), String> {
    if seed <= MAX_SEED {
        Ok(())
    } else {
        Err(format!("the seed must be a whole number from 0 to {MAX_SEED}, not {seed}"))
    }
}

pub fn check_player_count(players: usize) -> Result<(), String> {
    if (MIN_PLAYERS..=MAX_PLAYERS).contains(&players) {
        Ok(())
    } else {
        Err(format!("a Game needs {MIN_PLAYERS} to {MAX_PLAYERS} Players, not {players}"))
    }
}
