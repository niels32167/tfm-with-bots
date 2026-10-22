//! A Scenario: a described position to start a Game from instead of normal setup.
//! Tests (and later the dev panel's state editor) build Games this way. Anything a
//! Scenario leaves out takes the normal defaults; an unknown field is an error, so a
//! typo in a test fails loudly instead of being ignored.

use serde::{Deserialize, Serialize};

use crate::board::{Reservation, Tile, TileKind, find_area, printed};
use crate::game::{
    Game, MAX_OCEANS, MAX_OXYGEN, MAX_TEMPERATURE, MIN_TEMPERATURE, Player, STARTING_MEGACREDITS,
    STARTING_TERRAFORM_RATING, TEMPERATURE_STEP, check_player_count, check_seed,
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
    pub oxygen: i32,
    /// The Tiles on the board. The number of Oceans is the number of Ocean Tiles.
    pub tiles: Vec<ScenarioTile>,
    pub players: Vec<ScenarioPlayer>,
}

impl Default for Scenario {
    fn default() -> Scenario {
        Scenario {
            seed: 0,
            generation: 1,
            first_player: 0,
            temperature: MIN_TEMPERATURE,
            oxygen: 0,
            tiles: Vec::new(),
            players: vec![ScenarioPlayer::default(); 2],
        }
    }
}

/// A Tile on an Area, such as `{"area": "C3", "tile": "city", "owner": 0}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScenarioTile {
    pub area: String,
    pub tile: TileKind,
    /// The owning Player; Oceans have none.
    #[serde(default)]
    pub owner: Option<usize>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ScenarioPlayer {
    pub megacredits: i32,
    pub steel: i32,
    pub titanium: i32,
    pub plants: i32,
    pub production: ScenarioProduction,
    pub terraform_rating: i32,
}

impl Default for ScenarioPlayer {
    fn default() -> ScenarioPlayer {
        ScenarioPlayer {
            megacredits: STARTING_MEGACREDITS,
            steel: 0,
            titanium: 0,
            plants: 0,
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
        if !(0..=MAX_OXYGEN).contains(&self.oxygen) {
            return Err(format!(
                "Oxygen must be a step on the track from 0 to {MAX_OXYGEN} %, not {}",
                self.oxygen
            ));
        }
        let players = self
            .players
            .iter()
            .map(|player| Player {
                megacredits: player.megacredits,
                steel: player.steel,
                titanium: player.titanium,
                plants: player.plants,
                megacredit_production: player.production.megacredits,
                terraform_rating: player.terraform_rating,
                passed: false,
            })
            .collect();
        let mut game = Game::prepare(Start::Scenario(self.clone()), players);
        game.temperature = self.temperature;
        game.oxygen = self.oxygen;
        for tile in &self.tiles {
            let area = tile.check(self.players.len())?;
            if game.board.tile(area).is_some() {
                return Err(format!("a Scenario cannot put two Tiles on {}", tile.area));
            }
            game.board.place(area, Tile { kind: tile.tile, owner: tile.owner });
        }
        if game.board.oceans() > MAX_OCEANS {
            return Err(format!(
                "a Scenario can have at most {MAX_OCEANS} Oceans, not {}",
                game.board.oceans()
            ));
        }
        game.begin(self.generation, self.first_player);
        Ok(game)
    }
}

impl ScenarioTile {
    /// The Area this Tile is on, or why the rules never allow it there.
    fn check(&self, players: usize) -> Result<usize, String> {
        let area = find_area(&self.area).ok_or_else(|| format!("there is no Area '{}'", self.area))?;
        let tile = self.tile.name();
        let reserved = printed(area).reserved;
        if self.tile == TileKind::Ocean {
            if reserved != Some(Reservation::Ocean) {
                return Err(format!(
                    "cannot put an Ocean on {}, which is not reserved for Oceans",
                    self.area
                ));
            }
            if self.owner.is_some() {
                return Err(format!(
                    "Oceans belong to nobody, so the Ocean on {} cannot have an owner",
                    self.area
                ));
            }
            return Ok(area);
        }
        match reserved {
            None => {}
            Some(Reservation::Ocean) => {
                return Err(format!("cannot put a {tile} on {}, which is reserved for Oceans", self.area));
            }
            Some(_) => {
                return Err(format!(
                    "cannot put a {tile} on {}, which is reserved for the {} card",
                    self.area,
                    printed(area).name.unwrap_or_default()
                ));
            }
        }
        match self.owner {
            None => Err(format!("a {tile} needs an owner: the {tile} on {} has none", self.area)),
            Some(owner) if owner >= players => Err(format!(
                "the owner must be one of the Players, indexed 0 to {}, not {owner}",
                players - 1
            )),
            Some(_) => Ok(area),
        }
    }
}
