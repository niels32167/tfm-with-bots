//! The card catalog: the printed data of every card in the v1 set (ADR 0003), the 208 Project
//! Cards and 12 Corporations. It comes from the card file, `engine/cards/cards.json`, which
//! `tools/card_import.py` imports from the fan-made card list (ADR 0005) and which is built
//! into the engine. The catalog is read once, the first time it is needed, and never changes,
//! so a Game can refer to cards without copying them (ADR 0004).

use std::sync::LazyLock;

use serde::{Deserialize, Serialize};

use crate::board::TileKind;
use crate::resources::Resource;

const CARD_FILE: &str = include_str!("../cards/cards.json");

/// Every card: the Project Cards in number order, then the Corporations.
pub static CARD_CATALOG: LazyLock<Vec<Card>> = LazyLock::new(|| {
    let file: CardFile = serde_json::from_str(CARD_FILE)
        .unwrap_or_else(|error| panic!("engine/cards/cards.json is not a valid card file: {error}"));
    file.cards
});

#[derive(Deserialize)]
struct CardFile {
    cards: Vec<Card>,
}

/// One card as printed.
#[derive(Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Card {
    /// How Scenarios, Option details and Replays name it: "black_polar_dust".
    pub id: String,
    /// 1 to 208 for Project Cards. Corporations have no printed number.
    pub number: Option<u16>,
    pub name: String,
    #[serde(rename = "type")]
    pub card_type: CardType,
    pub corporate_era: bool,
    /// In MegaCredits. Corporations have no cost.
    pub cost: Option<i32>,
    /// In the order printed, from the top right corner leftwards.
    pub tags: Vec<Tag>,
    /// All of them must be met to play the card.
    pub requirements: Vec<Requirement>,
    pub victory_points: Option<VictoryPoints>,
    pub text: String,
    /// The card's middle part as the card list draws it. Only the GUI reads it.
    pub face: serde_json::Value,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CardType {
    Automated,
    Active,
    Event,
    Corporation,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Tag {
    Building,
    Space,
    Power,
    Science,
    Jovian,
    Earth,
    Plant,
    Microbe,
    Animal,
    City,
    Event,
}

/// A Card Resource that Victory Points can count.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CardResource {
    Animal,
    Microbe,
    Science,
    Fighter,
}

/// A condition that must hold before the card can be played.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub enum Requirement {
    /// Oxygen in %.
    Oxygen(Limit),
    /// Temperature in °C.
    Temperature(Limit),
    /// Ocean Tiles placed.
    Oceans(Limit),
    /// At least `min` of the Player's own Tags of this kind.
    Tag { tag: Tag, min: i32 },
    /// At least `min` steps of the Player's own Production of `resource`.
    Production { resource: Resource, min: i32 },
    /// At least `min` Tiles of this kind, the Player's own or anyone's.
    Tiles { tile: TileKind, owner: Owner, min: i32 },
}

/// The lowest or the highest a Global Parameter may be.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Limit {
    Min(i32),
    Max(i32),
}

/// Whose Tiles a Requirement counts.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Owner {
    You,
    Anyone,
}

/// The Victory Points a card scores at the end of the Game.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum VictoryPoints {
    /// A fixed number, which may be negative.
    Fixed(i32),
    /// `points` for every `per` of something, such as 1 for every 2 microbes on the card.
    Per { points: i32, per: i32, of: Counted },
    /// `points` once there are at least `at_least` of something.
    AtLeast { points: i32, at_least: i32, of: Counted },
}

/// What Victory Points count.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Counted {
    /// Card Resources on the card itself.
    CardResource(CardResource),
    /// The Player's own Tags.
    Tag(Tag),
    /// Tiles next to the card's own Tile.
    Adjacent(TileKind),
    /// Tiles on the board, whoever owns them.
    TilesInPlay(TileKind),
}
