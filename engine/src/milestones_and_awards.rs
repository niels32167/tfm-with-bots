//! The five Tharsis Milestones and five Tharsis Awards: what each one measures, and how
//! far each Player is towards it.

use serde::{Deserialize, Serialize};

use crate::board::TileKind;
use crate::game::Game;

/// What claiming a Milestone costs, in MegaCredits.
pub const MILESTONE_COST: i32 = 8;
pub const MAX_MILESTONES_CLAIMED: usize = 3;

/// Victory Points for each Milestone a Player has claimed.
pub const MILESTONE_VICTORY_POINTS: i32 = 5;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Milestone {
    Terraformer,
    Mayor,
    Gardener,
    Builder,
    Planner,
}

impl Milestone {
    /// In the order printed on the board.
    pub const ALL: [Milestone; 5] = [
        Milestone::Terraformer,
        Milestone::Mayor,
        Milestone::Gardener,
        Milestone::Builder,
        Milestone::Planner,
    ];

    /// Its position in `ALL`.
    pub fn index(self) -> usize {
        self as usize
    }

    /// How Option details and the view name it: "terraformer".
    pub fn id(self) -> String {
        self.name().to_lowercase()
    }

    pub fn name(self) -> &'static str {
        match self {
            Milestone::Terraformer => "Terraformer",
            Milestone::Mayor => "Mayor",
            Milestone::Gardener => "Gardener",
            Milestone::Builder => "Builder",
            Milestone::Planner => "Planner",
        }
    }

    /// What a Player needs to claim it, as printed.
    pub fn condition(self) -> &'static str {
        match self {
            Milestone::Terraformer => "Having a Terraform Rating of at least 35",
            Milestone::Mayor => "Owning at least 3 Cities",
            Milestone::Gardener => "Owning at least 3 Greeneries",
            Milestone::Builder => "Having at least 8 building Tags in play",
            Milestone::Planner => "Having at least 16 cards in hand",
        }
    }

    /// The count a Player needs to reach to claim it.
    pub fn target(self) -> i32 {
        match self {
            Milestone::Terraformer => 35,
            Milestone::Mayor | Milestone::Gardener => 3,
            Milestone::Builder => 8,
            Milestone::Planner => 16,
        }
    }

    /// How far `player` is towards it: their Terraform Rating, Cities, Greeneries, building
    /// Tags or cards in hand. Tags and hands come with the cards (ticket 08), so Builder and
    /// Planner count 0 until then.
    pub fn count(self, game: &Game, player: usize) -> i32 {
        match self {
            Milestone::Terraformer => game.players[player].terraform_rating,
            Milestone::Mayor => game.board.owned(player, TileKind::City) as i32,
            Milestone::Gardener => game.board.owned(player, TileKind::Greenery) as i32,
            Milestone::Builder | Milestone::Planner => 0,
        }
    }
}

/// What funding an Award costs, in MegaCredits: 8 for the first Award funded, 14 for the
/// second and 20 for the third. No more can be funded after that.
pub const AWARD_COSTS: [i32; 3] = [8, 14, 20];

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Award {
    Landlord,
    Banker,
    Scientist,
    Thermalist,
    Miner,
}

impl Award {
    /// In the order printed on the board.
    pub const ALL: [Award; 5] =
        [Award::Landlord, Award::Banker, Award::Scientist, Award::Thermalist, Award::Miner];

    /// Its position in `ALL`.
    pub fn index(self) -> usize {
        self as usize
    }

    /// How Option details and the view name it: "landlord".
    pub fn id(self) -> String {
        self.name().to_lowercase()
    }

    pub fn name(self) -> &'static str {
        match self {
            Award::Landlord => "Landlord",
            Award::Banker => "Banker",
            Award::Scientist => "Scientist",
            Award::Thermalist => "Thermalist",
            Award::Miner => "Miner",
        }
    }

    /// What the leader has most of, as printed.
    pub fn condition(self) -> &'static str {
        match self {
            Award::Landlord => "Owning the most Tiles in play",
            Award::Banker => "Having the highest MegaCredit Production",
            Award::Scientist => "Having the most science Tags in play",
            Award::Thermalist => "Having the most heat",
            Award::Miner => "Having the most steel and titanium",
        }
    }

    /// What `player` has of what it measures: the Tiles they own, their MegaCredit
    /// Production, science Tags, heat, or steel and titanium together. Tags come with the
    /// cards (ticket 08), so Scientist counts 0 until then.
    pub fn count(self, game: &Game, player: usize) -> i32 {
        let resources = game.players[player].resources;
        match self {
            Award::Landlord => game.board.tiles_of(player).count() as i32,
            Award::Banker => game.players[player].production.megacredits,
            Award::Scientist => 0,
            Award::Thermalist => resources.heat,
            Award::Miner => resources.steel + resources.titanium,
        }
    }

    /// A count of what it measures, as the game log writes it: "2 Tiles", "MegaCredit
    /// Production 3", "1 science Tag", "4 heat", "5 steel and titanium".
    pub fn counted(self, count: i32) -> String {
        let plural = if count == 1 { "" } else { "s" };
        match self {
            Award::Landlord => format!("{count} Tile{plural}"),
            Award::Banker => format!("MegaCredit Production {count}"),
            Award::Scientist => format!("{count} science Tag{plural}"),
            Award::Thermalist => format!("{count} heat"),
            Award::Miner => format!("{count} steel and titanium"),
        }
    }
}
