//! A Scenario: a described position to start a Game from instead of normal setup.
//! Tests (and later the dev panel's state editor) build Games this way. Anything a
//! Scenario leaves out takes the normal defaults; an unknown field is an error, so a
//! typo in a test fails loudly instead of being ignored.

use std::collections::BTreeMap;

use serde::{Deserialize, Deserializer, Serialize};

use crate::board::{Reservation, Tile, TileKind, find_area, printed};
use crate::game::{
    Game, MAX_OCEANS, MAX_OXYGEN, MAX_TEMPERATURE, MIN_TEMPERATURE, Player, STARTING_TERRAFORM_RATING,
    TEMPERATURE_STEP, check_player_count, check_seed, starting_resources,
};
use crate::log::player_name;
use crate::milestones_and_awards::{AWARD_COSTS, Award, MAX_MILESTONES_CLAIMED, Milestone};
use crate::replay::Start;
use crate::resources::{Resource, Resources};

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
    /// The Milestones claimed so far, and by whom.
    pub milestones: Vec<ClaimedMilestone>,
    /// The Awards funded so far, and by whom.
    pub awards: Vec<FundedAward>,
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
            milestones: Vec::new(),
            awards: Vec::new(),
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

/// A Milestone and who claimed it, such as `{"milestone": "mayor", "claimed_by": 1}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClaimedMilestone {
    pub milestone: Milestone,
    pub claimed_by: usize,
}

/// An Award and who funded it, such as `{"award": "landlord", "funded_by": 0}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FundedAward {
    pub award: Award,
    pub funded_by: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ScenarioPlayer {
    /// The Resources given, such as `{"plants": 8}`; the rest are what a Player starts with.
    #[serde(deserialize_with = "over_starting_resources")]
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
}

impl Default for ScenarioPlayer {
    fn default() -> ScenarioPlayer {
        ScenarioPlayer {
            resources: starting_resources(),
            production: Resources::default(),
            terraform_rating: STARTING_TERRAFORM_RATING,
        }
    }
}

impl ScenarioPlayer {
    /// Whether the rules allow these Resources and this Production for Player `index`.
    fn check(&self, index: usize) -> Result<(), String> {
        let name = player_name(index);
        for resource in Resource::ALL {
            let amount = self.resources[resource];
            if amount < 0 {
                return Err(format!("{name} cannot have {}", resource.counted(amount)));
            }
            let (production, minimum) = (self.production[resource], resource.min_production());
            if production < minimum {
                return Err(format!(
                    "{name}'s {} Production must be {minimum} or more, not {production}",
                    resource.name()
                ));
            }
        }
        Ok(())
    }
}

/// Reads a Scenario Player's Resources given in part, such as `{"plants": 8}`: the
/// Resources left out keep what a Player starts with.
fn over_starting_resources<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Resources, D::Error> {
    let given = BTreeMap::<Resource, i32>::deserialize(deserializer)?;
    let mut resources = starting_resources();
    for (resource, amount) in given {
        resources[resource] = amount;
    }
    Ok(resources)
}

impl Scenario {
    /// The Game this Scenario describes, or why it can't be set up.
    pub fn start(self) -> Result<Game, String> {
        check_player_count(self.players.len())?;
        check_seed(self.seed)?;
        if self.generation < 1 {
            return Err("the Generation must be 1 or more".to_string());
        }
        check_player(self.first_player, self.players.len(), "the first player")?;
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
        for (index, player) in self.players.iter().enumerate() {
            player.check(index)?;
        }
        let players = self
            .players
            .iter()
            .map(|player| Player {
                resources: player.resources,
                production: player.production,
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
        if self.milestones.len() > MAX_MILESTONES_CLAIMED {
            return Err(format!(
                "at most {MAX_MILESTONES_CLAIMED} Milestones can be claimed, not {}",
                self.milestones.len()
            ));
        }
        for claim in &self.milestones {
            let name = claim.milestone.name();
            check_player(claim.claimed_by, self.players.len(), &format!("whoever claimed {name}"))?;
            let claimed_by = &mut game.claimed_milestones[claim.milestone.index()];
            if claimed_by.is_some() {
                return Err(format!("the {name} Milestone can be claimed only once"));
            }
            *claimed_by = Some(claim.claimed_by);
        }
        if self.awards.len() > AWARD_COSTS.len() {
            return Err(format!(
                "at most {} Awards can be funded, not {}",
                AWARD_COSTS.len(),
                self.awards.len()
            ));
        }
        for funding in &self.awards {
            let name = funding.award.name();
            check_player(funding.funded_by, self.players.len(), &format!("whoever funded {name}"))?;
            let funded_by = &mut game.funded_awards[funding.award.index()];
            if funded_by.is_some() {
                return Err(format!("the {name} Award can be funded only once"));
            }
            *funded_by = Some(funding.funded_by);
        }
        game.begin(self.generation, self.first_player);
        Ok(game)
    }
}

/// Whether `player` is one of the `players` Players; `who` names them in the error.
fn check_player(player: usize, players: usize, who: &str) -> Result<(), String> {
    if player < players {
        Ok(())
    } else {
        Err(format!("{who} must be one of the Players, indexed 0 to {}, not {player}", players - 1))
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
            Some(owner) => {
                check_player(owner, players, "the owner")?;
                Ok(area)
            }
        }
    }
}
