//! The card catalog: the printed data of every card in the v1 set (ADR 0003), the 208 Project
//! Cards and 12 Corporations. It comes from the card file, `engine/cards/cards.json`, which
//! `tools/card_import.py` imports from the fan-made card list (ADR 0005) and which is built
//! into the engine. The catalog is read once, the first time it is needed, and never changes,
//! so a Game can refer to cards without copying them (ADR 0004).

use std::sync::LazyLock;

use serde::{Deserialize, Serialize};

use crate::board::{Placement, TileKind};
use crate::card_code::CARDS_WITH_CODE;
use crate::card_set::CardSet;
use crate::resources::{Resource, Resources};

const CARD_FILE: &str = include_str!("../cards/cards.json");

/// How many Project Cards there are. They come first in the catalog, in number order, so a
/// Project Card's index in the catalog is its number minus 1. A Game names cards by that index.
pub const PROJECT_CARDS: usize = 208;

/// Every card: the Project Cards in number order, then the Corporations.
pub static CARD_CATALOG: LazyLock<Vec<Card>> = LazyLock::new(|| {
    let file: CardFile = serde_json::from_str(CARD_FILE)
        .unwrap_or_else(|error| panic!("engine/cards/cards.json is not a valid card file: {error}"));
    for (card, id) in CARDS_WITH_CODE {
        assert_eq!(
            file.cards[card].id, id,
            "card {card} of the catalog is not the card its Rust code is for"
        );
    }
    file.cards
});

/// The index of the Project Card whose id is `id`, if there is one.
pub fn find_project_card(id: &str) -> Option<usize> {
    CARD_CATALOG[..PROJECT_CARDS].iter().position(|card| card.id == id)
}

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
    /// What the card does when played, as far as effect data describes it (ADR 0009), and its
    /// action if it has one. Written by hand; a card without it is not implemented yet, and is
    /// never offered.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub effects: Option<Effects>,
}

impl Card {
    pub fn has_tag(&self, tag: Tag) -> bool {
        self.tags.contains(&tag)
    }

    /// A Project Card's cost in MegaCredits. Corporations have none.
    pub fn project_cost(&self) -> i32 {
        self.cost.expect("only Project Cards have a cost")
    }

    /// The effects of a card that is implemented, as every card played is.
    pub fn implemented_effects(&self) -> &Effects {
        self.effects.as_ref().expect("only implemented cards are played")
    }

    /// Whether its effect data has a production box, which is fixed Production or Production
    /// per Tag or Tile. A card that is not implemented has none.
    pub fn has_production_box(&self) -> bool {
        self.effects.as_ref().is_some_and(|effects| {
            effects.production != Resources::default()
                || effects.production_per.is_some()
                || !effects.any_player_production().is_zero()
        })
    }

    /// The Production change at `index` among those its Player chooses from.
    pub fn production_alternative(&self, index: usize) -> Resources {
        self.implemented_effects().production_choice[index]
    }

    /// The action of an implemented card, if it has one.
    pub fn action(&self) -> Option<&Effects> {
        self.effects.as_ref().and_then(|effects| effects.action.as_deref())
    }

    /// The action of a card that has one, as every card whose action is used does.
    pub fn implemented_action(&self) -> &Effects {
        self.action().expect("only cards with an action have their action used")
    }
}

/// The simple effects of a card, or of its action, which are carried out in this order: the
/// action's payment, Resources (fixed, then per Tag or Tile), Production (fixed, then per Tag or
/// Tile, then for having at least so many), Temperature and Oxygen steps, Terraform Rating
/// (fixed, then per Tag), cards drawn, cards looked at to keep or buy some of, the Production or
/// Resource change the Player chooses, the Tiles one at a time, and then what it takes from any
/// Player. For the cards described this way the order never changes the outcome; a card whose
/// effects depend on their order gets its own Rust code.
#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Effects {
    /// Only for an action: the MegaCredits it costs, which steel or titanium may pay as for a card
    /// with a building or space Tag (Aquifer Pumping, Water Import from Europa).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pay: Option<ActionCost>,
    /// Resources gained, or lost below zero. An action's cost in Resources is written here.
    pub resources: Resources,
    /// Resources gained for what the Player has, such as 1 MegaCredit for each City on Mars
    /// (Martian Rails).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resources_per: Option<ResourcesPer>,
    /// Production steps raised, or lowered below zero.
    pub production: Resources,
    /// Production raised by what the Player has, counted once the card is played, so its own
    /// Tags count ("including this").
    #[serde(skip_serializing_if = "Option::is_none")]
    pub production_per: Option<ProductionPer>,
    /// Production raised only if the Player has at least so many of something, counted once the
    /// card is played: Nitrogen-Rich Asteroid's 3 more plant Production steps with 3 plant Tags.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub production_at_least: Option<ProductionAtLeast>,
    /// Production changes the Player chooses one of, such as 1 plant Production step or 2 energy
    /// Production steps (Artificial Photosynthesis). Empty for a card with no such choice.
    pub production_choice: Vec<Resources>,
    /// Only for an action: Resource changes the Player chooses one of, such as 1 plant or 1 steel
    /// for 7 MegaCredits (Electro Catapult). Empty for an action with no such choice.
    pub resources_choice: Vec<Resources>,
    /// Temperature steps raised.
    pub temperature: i32,
    /// Oxygen steps raised.
    pub oxygen: i32,
    /// Terraform Rating steps raised.
    pub terraform_rating: i32,
    /// Terraform Rating raised by what the Player has, counted once the card is played, so its
    /// own Tags count (Terraforming Ganymede).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub terraform_rating_per: Option<TerraformRatingPer>,
    /// Cards drawn.
    pub draw: i32,
    /// Only for a card when played: what it takes from one Player of its Player's picking (a
    /// red-bordered icon), once its Tiles are placed. None for a card that takes nothing.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub any_player: Option<AnyPlayer>,
    /// Cards looked at from the top of the deck, some of them kept and the rest discarded
    /// (Business Contacts, Invention Contest).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub look_at: Option<LookAt>,
    /// The Tiles to place, in order, each on the Areas it may go on. An action places at most
    /// one.
    pub tiles: Vec<Placement>,
    /// Only for a card when played: its action, which its Player may use once per Generation
    /// (an Active card's red arrow). None for a card without one.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub action: Option<Box<Effects>>,
    /// Only for an Active card: MegaCredits off every card its Player plays from then on, or only
    /// off those with a Tag (Space Station's 2 off each card with a space Tag).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub discount: Option<Discount>,
    /// Only for an Active card: how many MegaCredits more each steel and each titanium pays for
    /// its Player from then on, towards whatever they may pay for (Advanced Alloys).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cube_values: Option<CubeValues>,
    /// Only for an Active card: how many steps easier each of its Player's Requirements on a
    /// Global Parameter is to meet from then on (Adaptation Technology).
    #[serde(skip_serializing_if = "is_zero")]
    pub requirement_steps: i32,
    /// Only for an Event: what it changes about the next card its Player plays this Generation
    /// (Indentured Workers, Special Design).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_card: Option<NextCard>,
    /// Only for an Active card: what its Player gains from then on, each time something happens
    /// (Arctic Algae's 2 plants when anyone places an Ocean). Empty for a card without one.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub when: Vec<Trigger>,
}

/// What a card's Player gains each time something happens, as `on` says, for as long as the card
/// is in play. A card whose gain is a Decision (Mars University) has its own Rust code.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Trigger {
    pub on: TriggerCondition,
    #[serde(default)]
    pub resources: Resources,
    #[serde(default)]
    pub production: Resources,
}

impl Effects {
    /// The Production the card lowers on any Player, if any: part of its production box (Heat
    /// Trappers), which Robotic Workforce copies.
    pub fn any_player_production(&self) -> Resources {
        match self.any_player {
            Some(AnyPlayer::Production(lowered)) => lowered,
            _ => Resources::default(),
        }
    }
}

/// What a card takes from one Player, whom its Player picks. Lowering Production must be carried
/// out in full, on a Player who can lose every step, the card's Player included. Removing
/// Resources is up to the amounts written, from whoever has some, and may be left undone (see
/// docs/rules-notes.md, "Taking from any Player").
#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum AnyPlayer {
    /// Production steps lowered, written below zero: Heat Trappers' `{"heat": -2}`.
    Production(Resources),
    /// Resources removed, up to these amounts, as one of these alternatives: Asteroid's 3 plants,
    /// or Sabotage's 3 titanium, 4 steel or 7 MegaCredits.
    Remove(Vec<Resources>),
    /// Like `Remove`, but the card's Player gains what is removed (Hired Raiders).
    Steal(Vec<Resources>),
}

/// What sets a card's Trigger off.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum TriggerCondition {
    /// A Tile of this kind placed by the card's Player, or by anyone.
    TilePlaced { tile: TileKind, by: Owner },
    /// The card's Player plays a card of this type (any, if left out) with this Tag (any, if
    /// left out).
    CardPlayed {
        #[serde(default, rename = "type", skip_serializing_if = "Option::is_none")]
        card_type: Option<CardType>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        tag: Option<Tag>,
    },
    /// The card's Player plays this Tag: once for each such Tag on the card they play.
    TagPlayed(Tag),
    /// The card's Player pays for a Standard Project, Sell Patents excepted.
    StandardProject,
}

/// What an Event changes about the next card its Player plays this Generation: MegaCredits off
/// its cost, and how many steps easier its Requirements on a Global Parameter are to meet.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct NextCard {
    #[serde(skip_serializing_if = "is_zero")]
    pub discount: i32,
    #[serde(skip_serializing_if = "is_zero")]
    pub requirement_steps: i32,
}

fn is_zero(value: &i32) -> bool {
    *value == 0
}

/// MegaCredits added to what a steel cube and a titanium cube pay.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct CubeValues {
    pub steel: i32,
    pub titanium: i32,
}

/// MegaCredits off the cost of each card played, or only of each card with `tag`. A card's own
/// discount never applies to itself, as it is paid for before it is in play.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Discount {
    pub megacredits: i32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tag: Option<Tag>,
}

/// The cards with each kind of ongoing effect, so that the Game looks only at a Player's played
/// cards among them.
pub struct CardsWith {
    pub discount: CardSet,
    pub cube_values: CardSet,
    pub requirement_steps: CardSet,
    pub triggers: CardSet,
}

/// Read from the card catalog the first time it is needed, like the catalog itself.
pub static CARDS_WITH: LazyLock<CardsWith> = LazyLock::new(|| {
    let having = |has: fn(&Effects) -> bool| -> CardSet {
        (0..PROJECT_CARDS).filter(|&card| CARD_CATALOG[card].effects.as_ref().is_some_and(has)).collect()
    };
    CardsWith {
        discount: having(|effects| effects.discount.is_some()),
        cube_values: having(|effects| effects.cube_values.is_some()),
        requirement_steps: having(|effects| effects.requirement_steps != 0),
        triggers: having(|effects| !effects.when.is_empty()),
    }
});

/// What an action costs in MegaCredits, and whether steel or titanium may pay for it, worth as
/// much as towards a card with a building or space Tag.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActionCost {
    pub megacredits: i32,
    /// Whether steel may pay part of it.
    #[serde(default)]
    pub steel: bool,
    /// Whether titanium may pay part of it.
    #[serde(default)]
    pub titanium: bool,
}

/// `amount` of `resource` for every `per` of something, such as 1 MegaCredit for each City on
/// Mars (Martian Rails).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResourcesPer {
    pub resource: Resource,
    pub amount: i32,
    pub per: i32,
    pub of: Counted,
}

/// `steps` of Production of `resource` for every `per` of something, such as 1 MegaCredit
/// Production step for each Earth Tag (Miranda Resort).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProductionPer {
    pub resource: Resource,
    pub steps: i32,
    pub per: i32,
    pub of: Counted,
}

/// `steps` of Production of `resource` once there are at least `at_least` of something, such as
/// 3 plant Production steps with at least 3 plant Tags (Nitrogen-Rich Asteroid).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProductionAtLeast {
    pub resource: Resource,
    pub steps: i32,
    pub at_least: i32,
    pub of: Counted,
}

/// Look at the top `cards` cards of the deck, and either take `keep` of them into the hand or
/// buy up to `buy` of them at the card price; the rest are discarded. One of `keep` and `buy` is
/// written, and the other is 0.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LookAt {
    pub cards: i32,
    #[serde(default)]
    pub keep: i32,
    #[serde(default)]
    pub buy: i32,
}

/// `steps` of Terraform Rating for every `per` of something, such as 1 step for each jovian Tag
/// (Terraforming Ganymede).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TerraformRatingPer {
    pub steps: i32,
    pub per: i32,
    pub of: Counted,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CardType {
    Automated,
    Active,
    Event,
    Corporation,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
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

impl Tag {
    /// The Tags that count when played, in the order the card list's filters give them. The
    /// Event Tag never counts (see `Game::tags`).
    pub const COUNTED: [Tag; 10] = [
        Tag::Building,
        Tag::Space,
        Tag::Power,
        Tag::Science,
        Tag::Jovian,
        Tag::Earth,
        Tag::Plant,
        Tag::Microbe,
        Tag::Animal,
        Tag::City,
    ];
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

/// What Victory Points, or Resources, Production or Terraform Rating per Tag or Tile, count.
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
    /// Tiles on Mars, whoever owns them: not those off Mars (Phobos Space Haven and Ganymede
    /// Colony, ticket 18).
    TilesOnMars(TileKind),
    /// The Tags of this kind that the Player's opponents have in play (Toll Station).
    TagsOfOpponents(Tag),
    /// The Events every Player has played (Media Archives).
    EventsPlayed,
}
