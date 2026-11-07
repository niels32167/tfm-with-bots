//! The card catalog: the printed data of the base box's 208 Project Cards and 12 Corporations
//! (ADR 0003), and of Prelude's 47 cards (ADR 0011). It comes from the card file,
//! `engine/cards/cards.json`, which `tools/card_import.py` imports from the fan-made card list
//! (ADR 0005) and which is built into the engine. The catalog is read once, the first time it is
//! needed, and never changes, so a Game can refer to cards without copying them (ADR 0004).

use std::sync::LazyLock;

use serde::{Deserialize, Serialize};

use crate::board::{Placement, SpecialTile, TileKind};
use crate::card_code::CARDS_WITH_CODE;
use crate::card_resources::CARDS_HOLDING_CARD_RESOURCES;
use crate::card_set::CardSet;
use crate::resources::{Resource, Resources};

const CARD_FILE: &str = include_str!("../cards/cards.json");

/// How many Project Cards the base box has. They come first in the catalog, in number order, so
/// such a card's index in the catalog is its number minus 1. A Game names cards by that index.
pub const PROJECT_CARDS: usize = 208;

/// How many Corporations the base box has. They follow its Project Cards in the catalog.
pub const CORPORATIONS: usize = 12;

/// How many cards the base box has: the only ones a Game holds until it can have Prelude, whose
/// cards follow them in the catalog so that no card of the base box ever changes its index.
pub const BASE_BOX_CARDS: usize = PROJECT_CARDS + CORPORATIONS;

/// How many cards the Prelude box has: 7 Project Cards, 5 Corporations and 35 Prelude Cards, in that
/// order.
pub const PRELUDE_BOX_CARDS: usize = 47;

/// How many cards the catalog has.
pub const CATALOG_CARDS: usize = BASE_BOX_CARDS + PRELUDE_BOX_CARDS;

/// How many Project Cards the Prelude box has. They come first among its cards, so a Game with Prelude
/// has the Project Cards from 0 to `PROJECT_CARDS` and from `BASE_BOX_CARDS` to `PRELUDE_PROJECT_CARDS_END`.
pub const PRELUDE_PROJECT_CARDS: usize = 7;
pub const PRELUDE_PROJECT_CARDS_END: usize = BASE_BOX_CARDS + PRELUDE_PROJECT_CARDS;

/// How many Corporations the Prelude box has, after its Project Cards.
pub const PRELUDE_CORPORATIONS: usize = 5;

/// The first Prelude Card in the catalog. The 35 of them come last.
pub const FIRST_PRELUDE_CARD: usize = PRELUDE_PROJECT_CARDS_END + PRELUDE_CORPORATIONS;
pub const PRELUDE_CARDS: usize = CATALOG_CARDS - FIRST_PRELUDE_CARD;

/// Every card: the base box's Project Cards in number order and its Corporations, then Prelude's
/// Project Cards in number order, its Corporations, and its Prelude Cards in number order.
pub static CARD_CATALOG: LazyLock<Vec<Card>> = LazyLock::new(|| {
    let file: CardFile = serde_json::from_str(CARD_FILE)
        .unwrap_or_else(|error| panic!("engine/cards/cards.json is not a valid card file: {error}"));
    assert_eq!(file.cards.len(), CATALOG_CARDS, "the card file does not hold the whole catalog");
    for (card, printed) in file.cards.iter().enumerate() {
        let is_project_card =
            matches!(printed.card_type, CardType::Automated | CardType::Active | CardType::Event);
        let in_order = if card < PROJECT_CARDS || (BASE_BOX_CARDS..PRELUDE_PROJECT_CARDS_END).contains(&card)
        {
            is_project_card
        } else if card < FIRST_PRELUDE_CARD {
            printed.card_type == CardType::Corporation
        } else {
            printed.card_type == CardType::Prelude
        };
        assert!(in_order, "card {card} of the catalog is out of the catalog's order");
    }
    for (card, id) in CARDS_WITH_CODE {
        assert_eq!(
            file.cards[card].id, id,
            "card {card} of the catalog is not the card its Rust code is for"
        );
    }
    for tile in SpecialTile::ALL {
        let id = serde_json::to_value(tile).expect("a special Tile is written as its card's id");
        assert_eq!(
            file.cards[tile.card()].id,
            id,
            "card {} of the catalog does not place {tile:?}",
            tile.card()
        );
    }
    file.cards
});

/// The Project Cards of a Game with Prelude or without.
pub fn project_cards_with(prelude: bool) -> CardSet {
    if prelude { CARDS_OF_TYPE.project_cards } else { CARDS_OF_TYPE.base_project_cards }
}

/// The index of the card whose id is `id`, if there is one.
pub fn find_card(id: &str) -> Option<usize> {
    CARD_CATALOG.iter().position(|card| card.id == id)
}

/// The index of the Project Card whose id is `id` in a Game with Prelude or without, if there is one.
pub fn find_project_card(id: &str, prelude: bool) -> Option<usize> {
    find_card(id).filter(|&card| project_cards_with(prelude).contains(card))
}

/// The index of the Prelude Card whose id is `id`, if there is one.
pub fn find_prelude_card(id: &str) -> Option<usize> {
    find_card(id).filter(|&card| CARD_CATALOG[card].card_type == CardType::Prelude)
}

/// The Corporations of a Game with Prelude or without.
pub fn corporations_with(prelude: bool) -> CardSet {
    if prelude { CARDS_OF_TYPE.corporations } else { CARDS_OF_TYPE.base_corporations }
}

/// The index of the Corporation whose id is `id` in a Game with Prelude or without, if there is one.
pub fn find_corporation(id: &str, prelude: bool) -> Option<usize> {
    find_card(id).filter(|&card| corporations_with(prelude).contains(card))
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
    /// 1 to 208 for the base box's Project Cards. Prelude numbers its own: 1 to 35 for Prelude
    /// Cards and 36 to 42 for its Project Cards, printed as #P01 to #P42. Corporations have no
    /// printed number.
    pub number: Option<u16>,
    pub name: String,
    #[serde(rename = "type")]
    pub card_type: CardType,
    pub corporate_era: bool,
    pub expansion: Expansion,
    /// In MegaCredits. Corporations and Prelude Cards have no cost.
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

    /// The kind of Card Resource it holds, if it is implemented and holds any.
    pub fn holds(&self) -> Option<CardResource> {
        self.effects.as_ref().and_then(|effects| effects.holds)
    }

    /// The kind of Card Resource it holds, as every card that gets or loses them does.
    pub fn held(&self) -> CardResource {
        self.holds().expect("only a card that holds Card Resources gets or loses them")
    }

    /// The action of an implemented card, if it has one.
    pub fn action(&self) -> Option<&Effects> {
        self.effects.as_ref().and_then(|effects| effects.action.as_deref())
    }

    /// The effects its Player chooses one of when it is played (Imported Hydrogen) or for its action
    /// (Regolith Eaters). No card has both.
    pub fn alternatives(&self) -> &[Effects] {
        let effects = self.implemented_effects();
        match &effects.action {
            Some(action) if effects.choice.is_empty() => &action.choice,
            _ => &effects.choice,
        }
    }

    /// The first action of a Corporation that has one.
    pub fn first_action(&self) -> Option<&Effects> {
        self.effects.as_ref().and_then(|effects| effects.first_action.as_deref())
    }

    /// The action of a card that has one, as every card whose action is used does.
    pub fn implemented_action(&self) -> &Effects {
        self.action().expect("only cards with an action have their action used")
    }
}

/// The simple effects of a card, or of its action, which are carried out in this order: the
/// action's payment, Card Resources on the card itself, Resources (fixed, then per Tag or Tile),
/// Production (fixed, then per Tag or Tile, then for having at least so many), Temperature and
/// Oxygen steps, Terraform Rating (fixed, then per Tag), cards drawn, cards looked at to keep or buy
/// some of, the Production or Resource change the Player chooses, an action's effects the Player
/// chooses, the Tiles one at a time, a played card's effects the Player chooses, Card Resources added
/// to other cards, and then what it takes from any Player. Claiming an
/// Area (Land Claim) is a card's only effect. For the cards described this way the order never
/// changes the outcome; a card whose effects depend on their order gets its own Rust code.
#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Effects {
    /// For an action, the MegaCredits it costs, which steel or titanium may pay as for a card with a
    /// building or space Tag (Aquifer Pumping, Water Import from Europa). For a Prelude Card, its
    /// price ("Pay 6 M€"), paid once its other effects are done (Business Empire).
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
    /// Effects the Player chooses one of, each carried out as `Effects` are: for an action, before its
    /// Tile (Regolith Eaters' 1 microbe added, or 2 removed to raise Oxygen); for a card being played,
    /// once its Tiles are placed (Imported Hydrogen's 3 plants, 3 microbes or 2 animals). Empty with
    /// no such choice.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub choice: Vec<Effects>,
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
    /// What it takes from one Player of its Player's picking (a red-bordered icon), once its Tiles
    /// are placed. An action only moves a Card Resource (Ants). None for a card that takes nothing.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub any_player: Option<AnyPlayer>,
    /// Cards looked at from the top of the deck, some of them kept and the rest discarded
    /// (Business Contacts, Invention Contest).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub look_at: Option<LookAt>,
    /// The Tiles to place, in order, each on the Areas it may go on. An action places at most
    /// one.
    pub tiles: Vec<Placement>,
    /// Only for a card when played: whether its Player claims an Area that only they may place a
    /// Tile on from then on (Land Claim).
    #[serde(skip_serializing_if = "is_false")]
    pub claim_area: bool,
    /// Card Resources added to other cards of the Player's, one at a time, once the Tiles are placed.
    /// Each goes on a card of their picking.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub add_to_another: Vec<AddToAnother>,
    /// Only for an Active card: the kind of Card Resource it holds. None for a card that holds none.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub holds: Option<CardResource>,
    /// Card Resources added to the card itself, or removed from it below zero.
    #[serde(skip_serializing_if = "is_zero")]
    pub card_resources: i32,
    /// Only for a card when played: its action, which its Player may use once per Generation
    /// (an Active card's or a Corporation's red arrow). None for a card without one.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub action: Option<Box<Effects>>,
    /// Only for a card in play: MegaCredits off every card its Player plays from then on, or only
    /// off those with a Tag (Space Station's 2 off each card with a space Tag).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub discount: Option<Discount>,
    /// Only for a card in play: how many MegaCredits more each steel and each titanium pays for
    /// its Player from then on, towards whatever they may pay for (Advanced Alloys).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cube_values: Option<CubeValues>,
    /// Only for a card in play: how many steps easier each of its Player's Requirements on a
    /// Global Parameter is to meet from then on (Adaptation Technology).
    #[serde(skip_serializing_if = "is_zero")]
    pub requirement_steps: i32,
    /// Only for a Prelude Card: the cards revealed from the top of the deck once its other effects are
    /// done, until so many with a Tag are found, which its Player takes into their hand; the rest are
    /// discarded (Acquired Space Agency).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reveal: Option<Reveal>,
    /// Only for a Corporation: what its Player must do as their first action in the Game (Inventrix's
    /// 3 cards, Tharsis Republic's City), carried out as `Effects` are, cards drawn, then the Tile, or
    /// the Award funded (Vitor).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub first_action: Option<Box<Effects>>,
    /// Only for a Corporation's first action: how many Prelude Cards its Player draws from the Prelude
    /// deck, to play one of them and discard the rest (Valley Trust).
    #[serde(skip_serializing_if = "is_zero")]
    pub prelude_cards: i32,
    /// Only for a Corporation's first action: whether its Player funds an Award of their choice for free
    /// (Vitor). It can be carried out only while fewer than 3 Awards are funded.
    #[serde(skip_serializing_if = "is_false")]
    pub fund_award: bool,
    /// Only for a card in play: how many plants fewer its Player pays to place a Greenery (EcoLine).
    #[serde(skip_serializing_if = "is_zero")]
    pub greenery_discount: i32,
    /// For an Event, what it changes about the next card its Player plays this Generation
    /// (Indentured Workers, Special Design). For a Prelude Card, its Player plays a card from their
    /// hand once its other effects are done, changed this way (Ecology Experts, Excentric Sponsor).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_card: Option<NextCard>,
    /// Only for a card in play: what its Player gains from then on, each time something happens
    /// (Arctic Algae's 2 plants when anyone places an Ocean). Empty for a card without one.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub when: Vec<Trigger>,
}

/// What a card's Player gains each time something happens, as `on` says, for as long as the card
/// is in play: Resources, Production, Card Resources on the card itself, or cards drawn (Point
/// Luna). A card whose gain is a
/// Decision (Mars University) has its own Rust code.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Trigger {
    pub on: TriggerCondition,
    #[serde(default)]
    pub resources: Resources,
    #[serde(default)]
    pub production: Resources,
    #[serde(default, skip_serializing_if = "is_zero")]
    pub card_resources: i32,
    #[serde(default, skip_serializing_if = "is_zero")]
    pub draw: i32,
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

/// `amount` Card Resources added to one of the Player's played cards that hold them. No card that
/// adds to another holds any itself, so each of those cards counts as ANOTHER card.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AddToAnother {
    /// The kind added, or left out for whichever the card picked holds (CEO's Favorite Project).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub kind: Option<CardResource>,
    pub amount: i32,
    /// Only a card with at least this many on it may get them.
    #[serde(default, skip_serializing_if = "is_zero")]
    pub at_least: i32,
    /// Whether the effects can be carried out only with such a card. Otherwise, without one, they
    /// are lost, and the rest is still carried out.
    #[serde(default, skip_serializing_if = "is_false")]
    pub must_have_card: bool,
}

impl AddToAnother {
    /// As labels and the game log write it: "2 microbes", or "1" for any kind.
    pub fn amount_text(self) -> String {
        self.kind.map_or(self.amount.to_string(), |kind| kind.counted(self.amount))
    }
}

/// One of the alternatives a card removes from one Player: up to these Resources, or up to `amount`
/// Card Resources of this kind from one of their cards (Virus' 2 animals).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged, deny_unknown_fields)]
pub enum Removal {
    FromACard { card_resource: CardResource, amount: i32 },
    Resources(Resources),
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
    /// Removed as one of these alternatives: Asteroid's 3 plants, or Sabotage's 3 titanium, 4 steel or
    /// 7 MegaCredits, or Virus' 2 animals or 5 plants.
    Remove(Vec<Removal>),
    /// Like `Remove`, but the card's Player gains what is removed, which is Resources only (Hired
    /// Raiders).
    Steal(Vec<Removal>),
    /// Only for an action: 1 Card Resource of this kind moved from any card to this one (Ants,
    /// Predators). It is the action's cost, so unlike `Remove` it can't be left undone.
    MoveCardResource(CardResource),
}

/// What sets a card's Trigger off.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum TriggerCondition {
    /// A Tile of this kind placed by the card's Player, or by anyone; with `on_mars`, only on Mars.
    TilePlaced {
        tile: TileKind,
        by: Owner,
        #[serde(default, skip_serializing_if = "is_false")]
        on_mars: bool,
    },
    /// The card's Player plays a card of this type (any, if left out) with this Tag (any, if
    /// left out).
    CardPlayed {
        #[serde(default, rename = "type", skip_serializing_if = "Option::is_none")]
        card_type: Option<CardType>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        tag: Option<Tag>,
    },
    /// The card's Player plays one of these Tags: once for each such Tag on the card they play.
    TagPlayed(Vec<Tag>),
    /// Anyone plays one of these Tags: once for each such Tag on the card they play. A Corporation's
    /// Tags are played when it is revealed.
    TagPlayedByAnyone(Vec<Tag>),
    /// The card's Player pays for a Standard Project, Sell Patents excepted.
    StandardProject,
    /// The card's Player pays for a card or a Standard Project with at least this printed cost.
    CostAtLeast(i32),
    /// The card's Player gets a placement bonus with any of these Resources: once for each Tile
    /// placed, however much it gives.
    PlacementBonus(Vec<Resource>),
    /// The card's Player plays a card printed with a Victory Point icon that isn't negative, or reveals
    /// their Corporation ("including this": Vitor).
    CardWithVictoryPoints,
}

/// What an Event changes about the next card its Player plays this Generation, or a Prelude Card
/// about the card from hand it plays: MegaCredits off its cost, how many steps easier its
/// Requirements on a Global Parameter are to meet, or whether those are ignored.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct NextCard {
    #[serde(skip_serializing_if = "is_zero")]
    pub discount: i32,
    #[serde(skip_serializing_if = "is_zero")]
    pub requirement_steps: i32,
    #[serde(skip_serializing_if = "is_false")]
    pub ignores_global_requirements: bool,
}

pub(crate) fn is_zero(value: &i32) -> bool {
    *value == 0
}

fn is_false(value: &bool) -> bool {
    !*value
}

/// MegaCredits added to what a steel cube and a titanium cube pay.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct CubeValues {
    pub steel: i32,
    pub titanium: i32,
}

/// MegaCredits off the cost of each card played, or only of each card with `tag`, or with `per_tag`
/// off it for each such Tag on it (Valley Trust's 4 off Research, which has 2 science Tags). A card's
/// own discount never applies to itself, as it is paid for before it is in play.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Discount {
    pub megacredits: i32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tag: Option<Tag>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub per_tag: bool,
}

/// The cards with each kind of ongoing effect, so that the Game looks only at a Player's played
/// cards among them.
pub struct CardsWith {
    pub discount: CardSet,
    pub cube_values: CardSet,
    pub requirement_steps: CardSet,
    pub greenery_discount: CardSet,
    pub triggers: CardSet,
    pub card_resources: CardSet,
    /// The cards with a wild Tag (Research Network).
    pub wild_tag: CardSet,
}

/// Read from the card catalog the first time it is needed, like the catalog itself.
pub static CARDS_WITH: LazyLock<CardsWith> = LazyLock::new(|| {
    let having = |has: fn(&Effects) -> bool| -> CardSet {
        (0..CARD_CATALOG.len()).filter(|&card| CARD_CATALOG[card].effects.as_ref().is_some_and(has)).collect()
    };
    let card_resources = having(|effects| effects.holds.is_some());
    assert!(
        card_resources.len() <= CARDS_HOLDING_CARD_RESOURCES,
        "a Game has room for every card's Card Resources"
    );
    CardsWith {
        discount: having(|effects| effects.discount.is_some()),
        cube_values: having(|effects| effects.cube_values.is_some()),
        requirement_steps: having(|effects| effects.requirement_steps != 0),
        greenery_discount: having(|effects| effects.greenery_discount != 0),
        triggers: having(|effects| !effects.when.is_empty()),
        card_resources,
        wild_tag: (0..CARD_CATALOG.len()).filter(|&card| CARD_CATALOG[card].has_tag(Tag::Wild)).collect(),
    }
});

/// The cards of each kind, so that the Game can tell a Player's played cards apart.
pub struct CardsOfType {
    /// Every Project Card: those of a Game with Prelude.
    pub project_cards: CardSet,
    /// The base box's Project Cards: those of a Game without Prelude.
    pub base_project_cards: CardSet,
    /// Every Corporation: those of a Game with Prelude.
    pub corporations: CardSet,
    /// The base box's Corporations: those of a Game without Prelude.
    pub base_corporations: CardSet,
    pub prelude_cards: CardSet,
}

/// Read from the card catalog the first time it is needed, like the catalog itself.
pub static CARDS_OF_TYPE: LazyLock<CardsOfType> = LazyLock::new(|| {
    let of_type = |kinds: &[CardType]| -> CardSet {
        (0..CARD_CATALOG.len()).filter(|&card| kinds.contains(&CARD_CATALOG[card].card_type)).collect()
    };
    CardsOfType {
        project_cards: of_type(&[CardType::Automated, CardType::Active, CardType::Event]),
        base_project_cards: (0..PROJECT_CARDS).collect(),
        corporations: of_type(&[CardType::Corporation]),
        base_corporations: (PROJECT_CARDS..BASE_BOX_CARDS).collect(),
        prelude_cards: of_type(&[CardType::Prelude]),
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

/// Cards revealed until `count` cards with `tag` are found (Acquired Space Agency's 2 with a space Tag).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reveal {
    pub tag: Tag,
    pub count: i32,
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
    Prelude,
}

/// The box a card comes in. Corporate Era's cards are in the base box.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Expansion {
    Base,
    Prelude,
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
    Wild,
}

impl Tag {
    /// The Tags that count when played, in the order the card list's filters give them, and the
    /// wild Tag, which counts only for an action (see `Game::tags_for_an_action`). The Event Tag
    /// never counts (see `Game::tags`).
    pub const COUNTED: [Tag; 11] = [
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
        Tag::Wild,
    ];

    /// As the game log writes it: "space", "jovian".
    pub fn name(self) -> &'static str {
        match self {
            Tag::Building => "building",
            Tag::Space => "space",
            Tag::Power => "power",
            Tag::Science => "science",
            Tag::Jovian => "jovian",
            Tag::Earth => "earth",
            Tag::Plant => "plant",
            Tag::Microbe => "microbe",
            Tag::Animal => "animal",
            Tag::City => "city",
            Tag::Event => "event",
            Tag::Wild => "wild",
        }
    }
}

/// A kind of marker kept on a card rather than with a Player.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CardResource {
    Animal,
    Microbe,
    Science,
    Fighter,
}

impl CardResource {
    /// "1 microbe", "2 microbes", "2 science".
    pub fn counted(self, amount: i32) -> String {
        let (name, plural) = match self {
            CardResource::Animal => ("animal", "s"),
            CardResource::Microbe => ("microbe", "s"),
            CardResource::Science => ("science", ""),
            CardResource::Fighter => ("fighter", "s"),
        };
        format!("{amount} {name}{}", if amount == 1 { "" } else { plural })
    }
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

impl VictoryPoints {
    /// The number printed in its icon: 1 for "1 VP per 2 animals", -2 for Nuclear Zone.
    pub fn icon(self) -> i32 {
        match self {
            VictoryPoints::Fixed(points)
            | VictoryPoints::Per { points, .. }
            | VictoryPoints::AtLeast { points, .. } => points,
        }
    }
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
