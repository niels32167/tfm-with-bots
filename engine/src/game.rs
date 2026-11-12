//! The rules: the state of a Game, the Decision it is waiting on, and what each Option does.
//!
//! The Game is always either over or waiting on exactly one Decision for one Player
//! (ADR 0002). Picking one of that Decision's Options is the only way it moves forward.
//! The state is a plain value with no shared references, so copying a Game is cheap
//! (ADR 0004), and nothing in it depends on the clock or on hash-map order (ADR 0010).

use std::fmt;

use serde::{Deserialize, Serialize};

use crate::board::{
    Areas, Board, BonusItem, Placement, SpecialTile, Tile, TileKind, printed, row_and_position,
};
use crate::card_actions::ResourceChange;
use crate::card_code::{FLOODING, THORGATE, ViralEnhancing};
use crate::card_flow::{Buying, Keeping};
use crate::card_resources::{Adding, CardResources};
use crate::card_set::CardSet;
use crate::cards::{
    AddToAnother, CARD_CATALOG, CARDS_OF_TYPE, CARDS_WITH, PROJECT_CARDS, project_cards_with,
};
use crate::corporations::ChoosingCorporation;
use crate::deck::Deck;
use crate::draft::{DraftPass, Drafting};
use crate::expenses::Expense;
use crate::log::LogEvent;
use crate::milestones_and_awards::{AWARD_COSTS, Award, MAX_MILESTONES_CLAIMED, MILESTONE_COST, Milestone};
use crate::playing_cards::{CardTiles, Payment, ProductionChange};
use crate::prelude_cards::{PreludeCards, PreludeSet};
use crate::random::RandomNumbers;
use crate::replay::{Replay, Start};
use crate::resources::{Resource, Resources};
use crate::scoring::{Score, final_scores, funded_award_places, winners};
use crate::targets::Targeting;
use crate::triggers::Happened;

pub const MIN_PLAYERS: usize = 2;
pub const MAX_PLAYERS: usize = 5;

/// The largest seed. Replays travel as JSON, and some JSON readers (the browser's among
/// them) hold numbers as doubles, which are exact only up to 2^53 - 1.
pub const MAX_SEED: u64 = (1 << 53) - 1;

/// Temperature is in °C. It starts at -30 and rises in steps of 2 up to +8.
pub const MIN_TEMPERATURE: i32 = -30;
pub const MAX_TEMPERATURE: i32 = 8;
pub const TEMPERATURE_STEP: i32 = 2;

/// Oxygen is in percent. It starts at 0 and rises in steps of 1 up to 14.
pub const MAX_OXYGEN: i32 = 14;

/// The track bonuses printed on the board. Each goes to the Player who reaches its step:
/// one heat Production at each of these Temperatures,
pub const HEAT_PRODUCTION_BONUS_TEMPERATURES: [i32; 2] = [-24, -20];
/// an Ocean to place at this Temperature,
pub const OCEAN_BONUS_TEMPERATURE: i32 = 0;
/// and a Temperature step at this Oxygen level.
pub const TEMPERATURE_BONUS_OXYGEN: i32 = 8;

pub const MAX_OCEANS: usize = 9;

/// How many plants a Player converts into a Greenery.
pub const PLANTS_PER_GREENERY: i32 = 8;

/// How much heat a Player converts into a Temperature step.
pub const HEAT_PER_TEMPERATURE_STEP: i32 = 8;

/// What placing a Tile next to an Ocean pays, in MegaCredits per Ocean.
pub const OCEAN_ADJACENCY_BONUS: i32 = 2;

pub const STARTING_TERRAFORM_RATING: i32 = 20;

/// What a Player holds without a Corporation: in a Scenario that gives them neither, and in a
/// Replay saved before Corporations existed, where they bought their setup cards with it.
pub const MEGACREDITS_WITHOUT_A_CORPORATION: i32 = 42;

pub const ACTIONS_PER_TURN: u32 = 2;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Settings {
    pub players: usize,
    pub seed: u64,
    /// Only a Replay saved before ticket 24 can have this on, as the setup screen had it on by
    /// default: the Project Cards were shuffled once more before the deck was. A new Game never has
    /// it, and only a Replay that has it on names it.
    #[serde(default, skip_serializing_if = "std::ops::Not::not")]
    pub implemented_cards_first: bool,
    /// The Draft variant in the Research phase. On by default (ADR 0003), but a Replay saved
    /// before the Draft existed has no such setting, and reads as off, as it was played.
    #[serde(default)]
    pub draft: bool,
    /// Whether each Player is dealt Corporations at setup. On by default (ADR 0003), but a Replay
    /// saved before they existed has no such setting, and reads as off, as it was played.
    #[serde(default)]
    pub corporations: bool,
    /// Whether the Game has Prelude (ADR 0011): Prelude Cards at setup, and Prelude's Project Cards in
    /// the deck. Off unless named; only the GUI's setup screen has it on by default. A Replay saved
    /// before Prelude existed has no such setting, and only a Replay that has it on names it, so a Game
    /// without Prelude saves as it did.
    #[serde(default, skip_serializing_if = "std::ops::Not::not")]
    pub prelude: bool,
}

#[derive(Clone, Debug)]
pub struct Player {
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
    /// Passed for the rest of this Generation's Action phase.
    pub passed: bool,
    pub hand: CardSet,
    /// The cards they have played, Events included, and their Corporation once it is revealed: its
    /// Tags and ongoing effects count as a played card's do.
    pub played: CardSet,
    /// The played cards whose action they have used this Generation.
    pub used_actions: CardSet,
    /// The Event they have played whose effect waits on the next card they play this Generation
    /// (Indentured Workers, Special Design), or the Prelude Card whose effect is on the card from the
    /// hand they are playing for it (Ecology Experts), if any.
    pub next_card: Option<usize>,
    /// In the setup or a Research phase, what they are buying from.
    pub buying: Buying,
    /// In the Draft, what they are drafting.
    pub drafting: Drafting,
    /// At setup, the Corporations dealt to them and the one they chose.
    pub choosing_corporation: ChoosingCorporation,
    /// With Prelude, the Prelude Cards dealt to them at setup and those they kept and have still to play.
    pub prelude_cards: PreludeCards,
    /// Whether they must still take their Corporation's first action.
    pub first_action_due: bool,
    /// Whether their Terraform Rating was raised this Generation.
    pub terraform_rating_raised: bool,
}

impl Player {
    /// The cards they have played that can hold Card Resources.
    pub fn cards_holding_card_resources(&self) -> CardSet {
        self.played.intersection(CARDS_WITH.card_resources)
    }

    /// Their Corporation, once it is revealed.
    pub fn corporation(&self) -> Option<usize> {
        self.played.intersection(CARDS_OF_TYPE.corporations).iter().next()
    }

    /// The Project Cards they have played, Events included: their played cards but their Corporation
    /// and their Prelude Cards.
    pub fn played_project_cards(&self) -> CardSet {
        self.played.intersection(CARDS_OF_TYPE.project_cards)
    }

    /// The Prelude Cards they have played.
    pub fn played_prelude_cards(&self) -> CardSet {
        self.played.intersection(CARDS_OF_TYPE.prelude_cards)
    }

    /// A Player before setup, holding `resources`.
    pub fn new(resources: Resources) -> Player {
        Player {
            resources,
            production: Resources::default(),
            terraform_rating: STARTING_TERRAFORM_RATING,
            passed: false,
            hand: CardSet::default(),
            played: CardSet::default(),
            used_actions: CardSet::default(),
            next_card: None,
            buying: Buying::default(),
            drafting: Drafting::default(),
            choosing_corporation: ChoosingCorporation::default(),
            prelude_cards: PreludeCards::default(),
            first_action_due: false,
            terraform_rating_raised: false,
        }
    }
}

/// What a Player holds without a Corporation: MegaCredits and nothing else.
pub fn resources_without_a_corporation() -> Resources {
    Resources { megacredits: MEGACREDITS_WITHOUT_A_CORPORATION, ..Resources::default() }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    /// Before Generation 1: Players buy from the cards dealt to them.
    Setup,
    /// From Generation 2 with the Draft on, the first part of the Research phase: Players draft
    /// the cards they will buy from.
    Draft,
    /// From Generation 2, before the Action phase: Players buy from the cards they drew or drafted.
    Research,
    /// With Prelude, after setup and before Generation 1's Action phase: Players play their Prelude
    /// Cards.
    PreludeCards,
    Action,
    /// After the final Production phase: Players may convert plants into Greeneries.
    FinalGreenery,
    Over,
}

impl Phase {
    /// Whether Players are buying cards: in the setup or a Research phase.
    pub fn is_buying(self) -> bool {
        matches!(self, Phase::Setup | Phase::Research)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StandardProject {
    SellPatents,
    PowerPlant,
    Asteroid,
    Aquifer,
    Greenery,
    City,
}

impl StandardProject {
    /// In the order printed on the board.
    pub const ALL: [StandardProject; 6] = [
        StandardProject::SellPatents,
        StandardProject::PowerPlant,
        StandardProject::Asteroid,
        StandardProject::Aquifer,
        StandardProject::Greenery,
        StandardProject::City,
    ];

    /// How Option details name it: "power_plant".
    pub fn id(self) -> String {
        self.name().to_lowercase().replace(' ', "_")
    }

    pub fn name(self) -> &'static str {
        match self {
            StandardProject::SellPatents => "Sell Patents",
            StandardProject::PowerPlant => "Power Plant",
            StandardProject::Asteroid => "Asteroid",
            StandardProject::Aquifer => "Aquifer",
            StandardProject::Greenery => "Greenery",
            StandardProject::City => "City",
        }
    }

    /// The printed price in MegaCredits. Sell Patents has none: it gains MegaCredits instead.
    pub fn cost(self) -> i32 {
        match self {
            StandardProject::SellPatents => 0,
            StandardProject::PowerPlant => 11,
            StandardProject::Asteroid => 14,
            StandardProject::Aquifer => 18,
            StandardProject::Greenery => 23,
            StandardProject::City => 25,
        }
    }

    /// The Tile it places, if any.
    pub fn tile(self) -> Option<TileKind> {
        match self {
            StandardProject::SellPatents | StandardProject::PowerPlant | StandardProject::Asteroid => None,
            StandardProject::Aquifer => Some(TileKind::Ocean),
            StandardProject::Greenery => Some(TileKind::Greenery),
            StandardProject::City => Some(TileKind::City),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecisionKind {
    /// Choose an Action, end the Turn, or Pass.
    Action,
    /// Choose the Area for a Tile, or the Area to claim with Land Claim.
    Area,
    /// Choose how to pay for the card being played.
    Payment,
    /// Choose the Production change the card being played makes.
    Production,
    /// Keep or buy one more of the cards the card being played, or the action being used, lets its
    /// Player look at.
    KeepCards,
    /// Choose the Resource change the action being used makes.
    Resources,
    /// Choose which effects the card being played, or the action being used, carries out.
    Effects,
    /// Choose which of the Player's cards gets the Card Resources being added.
    AddToCard,
    /// Choose one of the Corporations dealt at setup.
    Corporation,
    /// Keep one more of the Prelude Cards dealt at setup.
    PreludeCards,
    /// Play one of the Prelude Cards kept, before the other.
    PlayPreludeCard,
    /// Play a card from the hand for the Prelude Card being played (Ecology Experts).
    PlayCard,
    /// Keep one of the cards being drafted, and pass the rest on.
    Draft,
    /// Buy one more of the cards dealt, or be done, in the setup or a Research phase.
    BuyCards,
    /// Sell one more card from the hand, or be done, with the Sell Patents Standard Project.
    SellPatents,
    /// Discard a card from the hand to draw one, or be done (Mars University).
    DiscardToDraw,
    /// Add a science to Olympus Conference, or remove one to draw a card, or first discard a card
    /// to draw one with Mars University.
    OlympusConference,
    /// Add 1 Card Resource to the card played, or gain 1 plant (Viral Enhancers).
    ViralEnhancers,
    /// Choose whom the card being played takes Production or Resources from, or the card that the
    /// action being used takes a Card Resource from.
    Target,
    /// Convert plants into a Greenery once more, or be done, in the final Greenery conversion.
    FinalGreenery,
    /// Fund an Award for free, as the Corporation's first action (Vitor).
    FreeAward,
}

/// One of the answers a Decision offers. (Named `DecisionOption` because Rust already has `Option`.)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecisionOption {
    /// Play this Project Card from the hand, by its index in the card catalog.
    PlayCard(usize),
    /// Use the action of this played card.
    UseAction(usize),
    /// Take the first action of this Corporation, the Player's own.
    TakeFirstAction(usize),
    /// Choose this Corporation, one of those dealt at setup.
    ChooseCorporation(usize),
    /// Keep this Prelude Card, one of those dealt at setup.
    KeepPreludeCard(usize),
    /// Play this Prelude Card, one of those kept, or discard it for 15 MegaCredits if it can't be played.
    PlayPreludeCard(usize),
    /// Keep this card, one of those being drafted, and pass the rest on.
    DraftCard(usize),
    /// Buy this card, one of those dealt in the setup or a Research phase, or one of those the
    /// action being used lets its Player look at.
    BuyCard(usize),
    /// Sell this card from the hand, with the Sell Patents Standard Project.
    SellCard(usize),
    /// Discard this card from the hand to draw one (Mars University).
    DiscardCard(usize),
    /// Take what `card` takes from any Player from `player`, with the card's alternative at
    /// `alternative` (Sabotage's titanium, steel or MegaCredits).
    Target {
        card: usize,
        player: usize,
        alternative: usize,
    },
    /// Move 1 Card Resource from `from`, a card of `owner`'s, to `card`, whose action is being used.
    MoveCardResource {
        card: usize,
        owner: usize,
        from: usize,
    },
    /// Remove `amount` Card Resources with `card` from `from`, a card of `owner`'s (Virus).
    RemoveFromCard {
        card: usize,
        owner: usize,
        from: usize,
        amount: i32,
    },
    /// Remove, or steal, nothing with `card`, which may remove Resources from any Player.
    RemoveNothing(usize),
    /// Remove a science from Olympus Conference to draw a card (`draw`), or add one to it.
    OlympusConference {
        draw: bool,
    },
    /// Add 1 Card Resource to `card`, which is being played (`add`), or gain 1 plant (Viral Enhancers).
    ViralEnhancers {
        card: usize,
        add: bool,
    },
    /// Keep this card, one of those the card being played lets its Player look at.
    KeepCard(usize),
    /// Pay for `card`, which is being played, this way.
    Pay {
        card: usize,
        payment: Payment,
    },
    /// Make this Production change for `card`, which is being played.
    ChangeProduction {
        card: usize,
        change: ProductionChange,
    },
    /// Pay for what the Player is asked to pay for this way.
    PayExpense(Payment),
    /// Pay for the action of `card`, which is being used, this way.
    PayForAction {
        card: usize,
        payment: Payment,
    },
    /// Make this Resource change for the action of `card`, which is being used.
    ChangeResources {
        card: usize,
        change: ResourceChange,
    },
    /// Carry out the alternative at `alternative` of the effects `card`, which is being played, or
    /// its action, which is being used, chooses between.
    ChooseEffects {
        card: usize,
        alternative: usize,
    },
    /// Add `amount` Card Resources with `card` to `to`, one of the Player's played cards.
    AddToCard {
        card: usize,
        to: usize,
        amount: i32,
    },
    UseStandardProject(StandardProject),
    ClaimMilestone(Milestone),
    /// Fund `award` for `cost`, the price of the next Award funded.
    FundAward {
        award: Award,
        cost: i32,
    },
    /// Convert plants into a Greenery.
    ConvertPlants,
    /// Convert heat into a Temperature step.
    ConvertHeat,
    EndTurn,
    Pass,
    /// Finished buying cards, those dealt or those looked at, selling them, or converting plants in
    /// the final Greenery conversion.
    Done,
    /// Make the placement under way on this Area.
    PlaceTile {
        placement: Placement,
        area: usize,
    },
    /// Claim this Area with Land Claim.
    ClaimArea(usize),
}

/// What the current Player's Decision is about, other than the one their Phase asks for.
#[derive(Clone, Copy, Debug)]
pub enum Waiting {
    /// Which of the Corporations dealt to them they choose.
    Corporation,
    /// Which of the Prelude Cards dealt to them they keep.
    PreludeCards,
    /// The Area for this Tile, on the Areas it may go on.
    Area(Placement),
    /// How they pay for this card, which they are playing.
    Payment(usize),
    /// The Production change this card, which they are playing, makes.
    Production(usize),
    /// Which of the cards they are looking at they keep or buy.
    KeepCards(Keeping),
    /// How they pay for this, other than a card or a card's action.
    Expense(Expense),
    /// How they pay for the action of this card, which they are using.
    ActionPayment(usize),
    /// The Resource change the action of this card, which they are using, makes.
    Resources(usize),
    /// Which effects this card, which they are playing, or its action, which they are using, carries
    /// out.
    Effects(usize),
    /// Which of their cards gets the Card Resources that `card` adds.
    AddToCard { card: usize, add: AddToAnother },
    /// Which card they sell next with Sell Patents, having sold this many so far.
    SellPatents(usize),
    /// Whether, and which card, they discard from their hand to draw one (Mars University).
    DiscardToDraw,
    /// What Olympus Conference does for a science Tag played, or which card they discard first.
    OlympusConference,
    /// What Viral Enhancers does for a Tag played.
    ViralEnhancers,
    /// Whom a card takes Production or Resources from, or the card it takes a Card Resource from.
    Target(Targeting),
    /// Which Area they claim with Land Claim, which they are playing.
    ClaimArea,
    /// Which card they play from their hand for the Prelude Card they are playing, which their
    /// `next_card` names (Ecology Experts).
    CardFromHand,
    /// Which Award they fund for free, as their Corporation's first action (Vitor).
    FreeAward,
    /// Which of the Prelude Cards they drew they play, as their Corporation's first action, the rest
    /// being discarded (Valley Trust). Their Prelude Cards kept hold those drawn.
    DrawnPreludeCards,
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
    pub oxygen: i32,
    pub board: Board,
    pub deck: Deck,
    /// The cards discarded, face down. A set, since the pile is only ever shuffled into a new deck.
    pub discard: CardSet,
    /// The cards each Player has passed on in the Draft, in the order passed.
    pub draft_passes: Vec<DraftPass>,
    pub players: Vec<Player>,
    /// Who holds the first-player marker, and so takes the first Turn of this Generation.
    pub first_player: usize,
    /// Whose Turn it is during the Action phase.
    pub current_player: usize,
    /// How many Actions the current Player has taken in this Turn.
    pub actions_this_turn: u32,
    /// What the current Player's Decision is about, while it is not the one their Phase asks
    /// for (an Action, a Draft pick, a buy, a final Greenery).
    pub waiting: Option<Waiting>,
    /// The card whose Tiles the current Player is placing, while it has any left to place.
    pub placing_for: Option<CardTiles>,
    /// The card the current Player is playing, while the effects it lets them choose are still due.
    pub choosing_for: Option<usize>,
    /// The Prelude Card the current Player is playing, while its effects are carried out (its Tiles
    /// placed, say). Once they are done, what follows them begins: the cards it reveals, its price, or
    /// the card from the hand it plays (see `Game::finish_prelude_card`).
    pub playing_prelude_card: Option<usize>,
    /// How many more times the current Player may discard a card from their hand to draw one
    /// (Mars University), once the card they are playing is done.
    pub discards_to_draw: u32,
    /// How many more times the current Player chooses what Olympus Conference does, once the card
    /// they are playing is done.
    pub olympus_conference_due: u32,
    /// What Viral Enhancers still asks about for the card the current Player is playing, once it is
    /// done.
    pub viral_enhancing: Option<ViralEnhancing>,
    /// What a card takes from any Player, due once the card the current Player is playing is done
    /// with its Tiles.
    pub targeting: Option<Targeting>,
    /// The Area of a Tile whose placement bonus waits until the Tile being placed is down:
    /// a Greenery's waits for the Ocean its 0 °C step gave (see docs/rules-notes.md).
    pub waiting_bonus: Option<usize>,
    /// The Prelude Cards nobody was dealt, which Valley Trust's first action draws from. Empty in a
    /// Game without Prelude.
    pub prelude_deck: PreludeSet,
    /// The Card Resources on the cards played.
    pub card_resources: CardResources,
    /// The Card Resources still to add to other cards, due once the card the current Player is
    /// playing is done with its Tiles, or the action they are using with its Tile.
    pub adding: Option<Adding>,
    /// Who claimed each Milestone, by its index in `Milestone::ALL`.
    pub claimed_milestones: [Option<usize>; Milestone::ALL.len()],
    /// Who funded each Award, by its index in `Award::ALL`.
    pub funded_awards: [Option<usize>; Award::ALL.len()],
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
        let holding =
            if settings.corporations { Resources::default() } else { resources_without_a_corporation() };
        let players = vec![Player::new(holding); settings.players];
        let mut game = Game::prepare(Start::Settings(settings), players);
        game.first_player = game.random_numbers.below(game.players.len());
        game.generation = 1;
        let mut on_top = Vec::new();
        if game.settings.implemented_cards_first {
            on_top = (0..PROJECT_CARDS).collect();
            game.random_numbers.shuffle(&mut on_top);
        }
        let project_cards = project_cards_with(game.settings.prelude);
        game.deck = Deck::shuffled(project_cards, CardSet::default(), &on_top, &mut game.random_numbers);
        game.begin_setup();
        Ok(game)
    }

    /// A Game at normal setup, with an empty deck, waiting for `begin` to start its first Generation.
    pub fn prepare(start: Start, players: Vec<Player>) -> Game {
        let settings = start.settings();
        Game {
            random_numbers: RandomNumbers::new(settings.seed),
            replay: Replay { start, picks: Vec::new() },
            settings,
            generation: 0,
            phase: Phase::Action,
            temperature: MIN_TEMPERATURE,
            oxygen: 0,
            board: Board::new(),
            deck: Deck::EMPTY,
            discard: CardSet::default(),
            draft_passes: Vec::new(),
            players,
            first_player: 0,
            current_player: 0,
            actions_this_turn: 0,
            waiting: None,
            placing_for: None,
            choosing_for: None,
            playing_prelude_card: None,
            discards_to_draw: 0,
            olympus_conference_due: 0,
            viral_enhancing: None,
            targeting: None,
            waiting_bonus: None,
            prelude_deck: PreludeSet::default(),
            card_resources: CardResources::default(),
            adding: None,
            claimed_milestones: [None; Milestone::ALL.len()],
            funded_awards: [None; Award::ALL.len()],
            log: Vec::new(),
        }
    }

    pub fn is_over(&self) -> bool {
        self.phase == Phase::Over
    }

    /// The Decision the Game is waiting on, or `None` once it is over.
    pub fn decision(&self) -> Option<Decision> {
        if self.phase == Phase::Over {
            return None;
        }
        let options = match (self.waiting, self.phase) {
            (Some(Waiting::Corporation), _) => self.corporation_options(),
            (Some(Waiting::PreludeCards), _) => self.prelude_keeping_options(),
            (Some(Waiting::Area(placement)), _) => self.area_options(placement),
            (Some(Waiting::ClaimArea), _) => {
                self.board.claimable_areas().map(DecisionOption::ClaimArea).collect()
            }
            (Some(Waiting::Payment(card)), _) => self.payment_options(card),
            (Some(Waiting::Production(card)), _) => self.production_options(self.current_player, card),
            (Some(Waiting::KeepCards(keeping)), _) => {
                keeping.options(self.spendable_megacredits(self.current_player))
            }
            (Some(Waiting::Expense(expense)), _) => self.expense_options(expense),
            (Some(Waiting::ActionPayment(card)), _) => self.action_payment_options(card),
            (Some(Waiting::Resources(card)), _) => self.resource_change_options(self.current_player, card),
            (Some(Waiting::Effects(card)), _) => self.alternative_options(card),
            (Some(Waiting::AddToCard { card, add }), _) => self.add_to_card_options(card, add),
            (Some(Waiting::SellPatents(sold)), _) => self.selling_options(sold),
            (Some(Waiting::DiscardToDraw), _) => self.discard_to_draw_options(),
            (Some(Waiting::OlympusConference), _) => self.olympus_conference_options(),
            (Some(Waiting::ViralEnhancers), _) => self.viral_enhancers_options(),
            (Some(Waiting::Target(targeting)), _) => self.target_options(targeting),
            (Some(Waiting::CardFromHand), _) => self.cards_to_play_options(),
            (Some(Waiting::FreeAward), _) => self.free_award_options(),
            (Some(Waiting::DrawnPreludeCards), _) => self.prelude_playing_options(),
            (None, Phase::Draft) => self.drafting_options(),
            (None, Phase::Setup | Phase::Research) => self.buying_options(),
            (None, Phase::PreludeCards) => self.prelude_playing_options(),
            (None, Phase::FinalGreenery) => {
                vec![DecisionOption::ConvertPlants, DecisionOption::Done]
            }
            (None, _) => self.action_options(),
        };
        Some(Decision {
            player: self.current_player,
            kind: self.decision_kind()?,
            sequence: self.replay.picks.len() as u64,
            options,
        })
    }

    /// What kind of Decision the Game is waiting on, or `None` once it is over. Everyone at the table
    /// sees it, though not always its Options: another Player buying cards, say, or selling patents.
    pub fn decision_kind(&self) -> Option<DecisionKind> {
        if self.phase == Phase::Over {
            return None;
        }
        Some(match (self.waiting, self.phase) {
            (Some(Waiting::Corporation), _) => DecisionKind::Corporation,
            (Some(Waiting::PreludeCards), _) => DecisionKind::PreludeCards,
            (Some(Waiting::Area(_) | Waiting::ClaimArea), _) => DecisionKind::Area,
            (Some(Waiting::Payment(_) | Waiting::Expense(_) | Waiting::ActionPayment(_)), _) => {
                DecisionKind::Payment
            }
            (Some(Waiting::Production(_)), _) => DecisionKind::Production,
            (Some(Waiting::KeepCards(_)), _) => DecisionKind::KeepCards,
            (Some(Waiting::Resources(_)), _) => DecisionKind::Resources,
            (Some(Waiting::Effects(_)), _) => DecisionKind::Effects,
            (Some(Waiting::AddToCard { .. }), _) => DecisionKind::AddToCard,
            (Some(Waiting::SellPatents(_)), _) => DecisionKind::SellPatents,
            (Some(Waiting::DiscardToDraw), _) => DecisionKind::DiscardToDraw,
            (Some(Waiting::OlympusConference), _) => DecisionKind::OlympusConference,
            (Some(Waiting::ViralEnhancers), _) => DecisionKind::ViralEnhancers,
            (Some(Waiting::Target(_)), _) => DecisionKind::Target,
            (Some(Waiting::CardFromHand), _) => DecisionKind::PlayCard,
            (Some(Waiting::FreeAward), _) => DecisionKind::FreeAward,
            (Some(Waiting::DrawnPreludeCards), _) | (None, Phase::PreludeCards) => {
                DecisionKind::PlayPreludeCard
            }
            (None, Phase::Draft) => DecisionKind::Draft,
            (None, Phase::Setup | Phase::Research) => DecisionKind::BuyCards,
            (None, Phase::FinalGreenery) => DecisionKind::FinalGreenery,
            (None, _) => DecisionKind::Action,
        })
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
        if index >= count {
            return Err(PickError::NoSuchOption { index, count });
        }
        self.apply_pick(&decision, index);
        Ok(())
    }

    /// Records the pick of `decision`'s Option at `index` and carries it out. `decision` must
    /// be the current Decision and `index` one of its Options; `pick` checks both.
    pub fn apply_pick(&mut self, decision: &Decision, index: usize) {
        self.replay.picks.push(index);
        self.resolve(decision.options[index]);
    }

    /// Each Player's final score, once the Game is over.
    pub fn scores(&self) -> Option<Vec<Score>> {
        self.is_over().then(|| final_scores(self))
    }

    /// The current Player may play any card in their hand they can.
    fn cards_to_play_options(&self) -> Vec<DecisionOption> {
        self.cards_to_play().collect()
    }

    /// Playing each card in the current Player's hand that they can, as Options.
    fn cards_to_play(&self) -> impl Iterator<Item = DecisionOption> + '_ {
        let hand = self.players[self.current_player].hand.iter();
        hand.filter(|&card| self.can_play(self.current_player, card)).map(DecisionOption::PlayCard)
    }

    fn action_options(&self) -> Vec<DecisionOption> {
        if let Some(card) = self.first_action_to_take() {
            return vec![DecisionOption::TakeFirstAction(card), DecisionOption::Pass];
        }
        let player = &self.players[self.current_player];
        let spendable = self.spendable_megacredits(self.current_player);
        let mut options: Vec<DecisionOption> =
            self.cards_to_play().chain(self.usable_actions().map(DecisionOption::UseAction)).collect();
        for project in StandardProject::ALL {
            let can_use = match project {
                StandardProject::SellPatents => !player.hand.is_empty(),
                _ => {
                    spendable >= self.standard_project_cost(self.current_player, project)
                        && self.can_take_action_placing(
                            self.current_player,
                            project.tile().map(Placement::usual),
                        )
                }
            };
            if can_use {
                options.push(DecisionOption::UseStandardProject(project));
            }
        }
        if self.can_convert_plants(self.current_player) {
            options.push(DecisionOption::ConvertPlants);
        }
        // Offered at maximum Temperature too, like Asteroid (see docs/rules-notes.md).
        if player.resources.heat >= HEAT_PER_TEMPERATURE_STEP {
            options.push(DecisionOption::ConvertHeat);
        }
        for milestone in Milestone::ALL {
            if self.can_claim(milestone) {
                options.push(DecisionOption::ClaimMilestone(milestone));
            }
        }
        if let Some(cost) = self.award_cost()
            && spendable >= cost
        {
            for award in Award::ALL {
                if self.funded_awards[award.index()].is_none() {
                    options.push(DecisionOption::FundAward { award, cost });
                }
            }
        }
        // Once everyone else has passed, ending the Turn would only start another one.
        if self.actions_this_turn > 0 && self.another_player_still_in() {
            options.push(DecisionOption::EndTurn);
        }
        options.push(DecisionOption::Pass);
        options
    }

    /// Whether `player` may take an Action that makes `placement` (or places no Tile, for None):
    /// only if the Tile has an Area to go on. Actions that raise a Global Parameter stay open once it
    /// is at its maximum, though: Aquifer once 9 Oceans are placed (see docs/rules-notes.md).
    pub(crate) fn can_take_action_placing(&self, player: usize, placement: Option<Placement>) -> bool {
        match placement {
            None => true,
            Some(placement) if placement.tile == TileKind::Ocean && self.board.oceans() >= MAX_OCEANS => true,
            Some(placement) => self.board.has_area_for(placement, player),
        }
    }

    /// Whether the current Player may claim `milestone`: they meet it and can pay, nobody has
    /// claimed it, and fewer than three Milestones are claimed.
    fn can_claim(&self, milestone: Milestone) -> bool {
        let player = self.current_player;
        self.milestone_cost().is_some_and(|cost| self.spendable_megacredits(player) >= cost)
            && self.claimed_milestones[milestone.index()].is_none()
            && milestone.count(self, player) >= milestone.target()
    }

    /// What `player` pays for `project`: its printed cost, less Thorgate's discount on Power Plant.
    pub fn standard_project_cost(&self, player: usize, project: StandardProject) -> i32 {
        let discount = match project {
            StandardProject::PowerPlant if self.players[player].played.contains(THORGATE) => CARD_CATALOG
                [THORGATE]
                .implemented_effects()
                .discount
                .map_or(0, |discount| discount.megacredits),
            _ => 0,
        };
        project.cost() - discount
    }

    /// What claiming a Milestone costs, or None once three are claimed.
    pub fn milestone_cost(&self) -> Option<i32> {
        let claimed = self.claimed_milestones.iter().flatten().count();
        (claimed < MAX_MILESTONES_CLAIMED).then_some(MILESTONE_COST)
    }

    /// What funding the next Award costs, or None once three are funded.
    pub fn award_cost(&self) -> Option<i32> {
        AWARD_COSTS.get(self.funded_awards.iter().flatten().count()).copied()
    }

    /// How many plants `player` converts into a Greenery: `PLANTS_PER_GREENERY`, less what their
    /// cards take off (EcoLine).
    pub fn plants_per_greenery(&self, player: usize) -> i32 {
        let discounting = self.players[player].played.intersection(CARDS_WITH.greenery_discount);
        if discounting.is_empty() {
            return PLANTS_PER_GREENERY;
        }
        let discounts = discounting.iter();
        PLANTS_PER_GREENERY
            - discounts.map(|card| CARD_CATALOG[card].implemented_effects().greenery_discount).sum::<i32>()
    }

    fn can_convert_plants(&self, player: usize) -> bool {
        self.players[player].resources.plants >= self.plants_per_greenery(player)
            && self.board.has_area_for(Placement::usual(TileKind::Greenery), player)
    }

    /// Every way the current Player may pay for `card`.
    fn payment_options(&self, card: usize) -> Vec<DecisionOption> {
        let payments = self.payments(self.current_player, card);
        payments.into_iter().map(|payment| DecisionOption::Pay { card, payment }).collect()
    }

    /// Every Area where the current Player may make `placement`.
    fn area_options(&self, placement: Placement) -> Vec<DecisionOption> {
        let mut areas = self.board.areas_for(placement, self.current_player);
        if placement.tile == TileKind::Ocean {
            areas.retain(|&area| self.ocean_pays_for_prelude_card(area));
        }
        areas.into_iter().map(|area| DecisionOption::PlaceTile { placement, area }).collect()
    }

    fn resolve(&mut self, option: DecisionOption) {
        let player = self.current_player;
        match option {
            DecisionOption::PlayCard(card) => {
                if let Some(Waiting::CardFromHand) = self.waiting {
                    self.waiting = None;
                }
                match self.payments(player, card)[..] {
                    [only_way] => self.play_card(player, card, only_way),
                    _ => self.wait_on(Waiting::Payment(card)),
                }
            }
            DecisionOption::Pay { card, payment } => {
                self.waiting = None;
                self.play_card(player, card, payment);
            }
            DecisionOption::ChangeProduction { card, change } => {
                self.change_production_as_chosen(player, card, change)
            }
            DecisionOption::UseAction(card) => self.use_action(player, card),
            DecisionOption::TakeFirstAction(card) => self.take_first_action(card),
            DecisionOption::PayForAction { card, payment } => self.carry_out_action(player, card, payment),
            DecisionOption::ChangeResources { card, change } => {
                self.change_resources_as_chosen(player, card, change)
            }
            DecisionOption::ChooseEffects { card, alternative } => {
                self.carry_out_alternative(player, card, alternative)
            }
            DecisionOption::AddToCard { to, amount, .. } => self.add_to_card(to, amount),
            DecisionOption::ChooseCorporation(card) => self.choose_corporation(card),
            DecisionOption::KeepPreludeCard(card) => self.keep_prelude_card(card),
            DecisionOption::PlayPreludeCard(card) => self.play_prelude_card(card),
            DecisionOption::DraftCard(card) => self.draft(card),
            DecisionOption::BuyCard(card) if matches!(self.waiting, Some(Waiting::KeepCards(_))) => {
                self.keep_card(card)
            }
            DecisionOption::BuyCard(card) => self.buy(card),
            DecisionOption::SellCard(card) => self.sell(card),
            DecisionOption::DiscardCard(card) => self.discard_to_draw(Some(card)),
            DecisionOption::Target { card, player: target, alternative } => {
                self.take_as_picked(card, target, alternative)
            }
            DecisionOption::MoveCardResource { card, owner, from } => {
                self.move_card_resource_as_picked(card, owner, from)
            }
            DecisionOption::RemoveFromCard { owner, from, amount, .. } => {
                self.remove_from_card(owner, from, amount)
            }
            DecisionOption::RemoveNothing(card) => self.remove_nothing(card),
            DecisionOption::OlympusConference { draw } => self.olympus_conference(draw),
            DecisionOption::ViralEnhancers { card, add } => self.viral_enhancers(card, add),
            DecisionOption::KeepCard(card) => self.keep_card(card),
            // It has no price: the Player picks the cards to sell next.
            DecisionOption::UseStandardProject(StandardProject::SellPatents) => {
                self.wait_on(Waiting::SellPatents(0))
            }
            DecisionOption::UseStandardProject(project) => self.spend_on(Expense::StandardProject(project)),
            DecisionOption::ClaimMilestone(milestone) => self.spend_on(Expense::Milestone(milestone)),
            DecisionOption::FundAward { award, cost } => {
                if let Some(Waiting::FreeAward) = self.waiting {
                    self.waiting = None;
                }
                self.spend_on(Expense::Award { award, cost })
            }
            DecisionOption::PayExpense(payment) => self.pay_expense(payment),
            DecisionOption::ConvertPlants => {
                let plants = self.plants_per_greenery(player);
                self.players[player].resources.plants -= plants;
                self.log.push(LogEvent::ConvertedPlants { player, plants });
                self.place(Placement::usual(TileKind::Greenery));
                self.finish_unless_placing();
            }
            DecisionOption::ConvertHeat => {
                self.players[player].resources.heat -= HEAT_PER_TEMPERATURE_STEP;
                self.log.push(LogEvent::ConvertedHeat { player });
                self.raise_temperature(player);
                self.finish_unless_placing();
            }
            DecisionOption::PlaceTile { placement, area } => {
                self.waiting = None;
                self.place_tile(player, placement, area);
                self.finish_unless_placing();
            }
            DecisionOption::ClaimArea(area) => {
                self.waiting = None;
                self.board.claim_area(area, player);
                self.log.push(LogEvent::ClaimedArea { player, area });
                self.finish_unless_placing();
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
            DecisionOption::Done if matches!(self.waiting, Some(Waiting::SellPatents(_))) => {
                self.finish_selling()
            }
            DecisionOption::Done if matches!(self.waiting, Some(Waiting::KeepCards(_))) => {
                self.done_keeping()
            }
            DecisionOption::Done
                if matches!(self.waiting, Some(Waiting::DiscardToDraw | Waiting::OlympusConference)) =>
            {
                self.discard_to_draw(None)
            }
            DecisionOption::Done if self.phase == Phase::FinalGreenery => {
                self.log.push(LogEvent::DoneConvertingPlants { player });
                self.offer_final_greenery_from(self.index_in_player_order() + 1);
            }
            DecisionOption::Done => self.done_buying(),
        }
    }

    /// Unless a Tile is still to be placed, a card's included, the card played lets its Player choose
    /// its effects, Card Resources are added to another card of the Player's picking, the card played
    /// takes from a Player of its Player's picking, or the Tags played call on Olympus Conference, Mars
    /// University or Viral Enhancers: the current Action ends, or in the final Greenery conversion,
    /// the current Player may convert again.
    pub(crate) fn finish_unless_placing(&mut self) {
        if !self.is_placing() {
            self.place_next_card_tile();
        }
        if self.is_placing()
            || self.offer_alternatives()
            || self.offer_card_to_add_to()
            || self.offer_target()
            || self.offer_science_tag_effects()
            || self.offer_viral_enhancers()
        {
            return;
        }
        match self.phase {
            Phase::FinalGreenery => self.offer_final_greenery_from(self.index_in_player_order()),
            Phase::PreludeCards => self.finish_prelude_card(),
            // A Prelude Card played as a first action (Valley Trust).
            _ if self.playing_prelude_card.is_some() => self.finish_prelude_card(),
            _ => self.finish_action(),
        }
    }

    /// The Game now waits on the current Player's Decision about `waiting`. It waits on one
    /// thing at a time: nothing sets up a second Decision while one is waiting.
    pub(crate) fn wait_on(&mut self, waiting: Waiting) {
        assert!(self.waiting.is_none(), "{waiting:?} while {:?} is waiting", self.waiting);
        self.waiting = Some(waiting);
    }

    /// The current Player must make `placement` next.
    pub(crate) fn place(&mut self, placement: Placement) {
        self.wait_on(Waiting::Area(placement));
    }

    /// Whether the Game waits on an Area for a Tile, or for Land Claim to claim.
    pub(crate) fn is_placing(&self) -> bool {
        matches!(self.waiting, Some(Waiting::Area(_) | Waiting::ClaimArea))
    }

    pub(crate) fn finish_action(&mut self) {
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

    /// Each Player's energy turns into heat, then every Resource gains its Production,
    /// and MegaCredits also gain Terraform Rating. It ends the Generation, so every card action
    /// is unused again, and an effect on the next card played this Generation is lost.
    fn production_phase(&mut self) {
        self.log.push(LogEvent::ProductionPhase);
        for (index, player) in self.players.iter_mut().enumerate() {
            player.used_actions = CardSet::default();
            player.next_card = None;
            player.terraform_rating_raised = false;
            let energy = player.resources.energy;
            if energy > 0 {
                player.resources.heat += energy;
                player.resources.energy = 0;
                self.log.push(LogEvent::EnergyTurnsIntoHeat { player: index, energy });
            }
            for resource in Resource::ALL {
                player.resources[resource] += player.production[resource];
            }
            player.resources.megacredits += player.terraform_rating;
            self.log.push(LogEvent::Produced {
                player: index,
                terraform_rating: player.terraform_rating,
                production: player.production,
            });
        }
        if self.mars_is_terraformed() {
            self.log.push(LogEvent::MarsIsTerraformed);
            self.begin_final_greenery_conversion();
        } else {
            // The first-player marker passes clockwise, to the next Player.
            self.first_player = (self.first_player + 1) % self.players.len();
            self.generation += 1;
            self.log_generation_begins();
            self.begin_research_phase();
        }
    }

    /// Hands the first-player marker to `first_player` and begins `generation` with its Action
    /// phase: after setup, or where a Scenario starts.
    pub fn begin(&mut self, generation: u32, first_player: usize) {
        self.first_player = first_player;
        self.generation = generation;
        self.log_generation_begins();
        self.begin_action_phase();
    }

    fn log_generation_begins(&mut self) {
        self.log.push(LogEvent::GenerationBegins {
            generation: self.generation,
            first_player: self.first_player,
        });
    }

    /// The first Player takes the first Turn, and everyone is back in the Action phase.
    pub(crate) fn begin_action_phase(&mut self) {
        self.phase = Phase::Action;
        for player in &mut self.players {
            player.passed = false;
        }
        self.current_player = self.first_player;
        self.actions_this_turn = 0;
    }

    /// After the final Production phase, Players may convert plants into Greeneries in player
    /// order, starting with the first player, each finishing before the next.
    fn begin_final_greenery_conversion(&mut self) {
        self.phase = Phase::FinalGreenery;
        self.log.push(LogEvent::FinalGreeneryConversion { first_player: self.first_player });
        self.offer_final_greenery_from(0);
    }

    /// Hands the final Greenery conversion to the first Player who can convert plants,
    /// looking from index `start` in player order (0 is the first player). Once nobody
    /// can, the Game is over.
    fn offer_final_greenery_from(&mut self, start: usize) {
        match self.first_in_player_order_who(start, Game::can_convert_plants) {
            Some(player) => self.current_player = player,
            None => self.end_game(),
        }
    }

    /// Every Player, in player order from the first player.
    pub(crate) fn player_order(&self) -> impl Iterator<Item = usize> + use<> {
        let (first, count) = (self.first_player, self.players.len());
        (0..count).map(move |offset| (first + offset) % count)
    }

    /// The first Player for whom `can` holds, looking from index `start` in player order (0 is
    /// the first player).
    pub(crate) fn first_in_player_order_who(
        &self,
        start: usize,
        can: fn(&Game, usize) -> bool,
    ) -> Option<usize> {
        self.player_order().skip(start).find(|&player| can(self, player))
    }

    /// The first Player for whom `can` holds, looking from index `start` in player order, and then from
    /// the first player again. In a real Game nobody before `start` still has a pick to make; in a
    /// Sampled Position, the Players whose secret picks it took back do.
    pub(crate) fn next_in_player_order_who(
        &self,
        start: usize,
        can: fn(&Game, usize) -> bool,
    ) -> Option<usize> {
        self.first_in_player_order_who(start, can).or_else(|| self.first_in_player_order_who(0, can))
    }

    /// The current Player's index in player order, counting the first player as 0.
    pub(crate) fn index_in_player_order(&self) -> usize {
        let count = self.players.len();
        (self.current_player + count - self.first_player) % count
    }

    /// Whether all three Global Parameters are at their maximum.
    fn mars_is_terraformed(&self) -> bool {
        self.temperature >= MAX_TEMPERATURE && self.oxygen >= MAX_OXYGEN && self.board.oceans() >= MAX_OCEANS
    }

    /// The Game is over: the log says who took each Award, each Player's Victory Points, and
    /// who wins.
    fn end_game(&mut self) {
        self.phase = Phase::Over;
        self.log.push(LogEvent::GameOver);
        for place in funded_award_places(self) {
            self.log.push(LogEvent::AwardPlace(place));
        }
        let scores = final_scores(self);
        for score in &scores {
            self.log.push(LogEvent::FinalScore { player: score.player, victory_points: score.total });
        }
        for (player, win) in winners(&scores) {
            self.log.push(LogEvent::Won { player, win });
        }
    }

    /// The current Player has an Ocean to place `on` those Areas, unless all 9 are already
    /// placed: then the Aquifer they paid for, or the 0 °C bonus they reached, places nothing
    /// (see docs/rules-notes.md). Fewer than 9 placed always leaves an Area for one: of the 12
    /// reserved for Oceans, other Tiles take at most 3 (Mangrove, Protected Valley and Mohole
    /// Area).
    pub(crate) fn place_ocean(&mut self, on: Areas) {
        if self.board.oceans() < MAX_OCEANS {
            self.place(Placement { tile: TileKind::Ocean, on, special: None });
        } else {
            self.log.push(LogEvent::OceansAlreadyAtMaximum);
        }
    }

    /// Makes `placement` for `player` on `area`. An Ocean raises their Terraform Rating, and a
    /// Greenery Oxygen. Then `player` collects the placement bonus, unless that raise gave
    /// them another Tile to place: the bonus then waits until that Tile is down.
    fn place_tile(&mut self, player: usize, placement: Placement, area: usize) {
        let Placement { tile, special, .. } = placement;
        let owner = if tile == TileKind::Ocean { None } else { Some(player) };
        self.board.place(area, Tile { kind: tile, owner, special });
        self.log.push(LogEvent::PlacedTile { player, placement, area });
        if tile == TileKind::Ocean && self.placing_for.is_some_and(|tiles| tiles.card == FLOODING) {
            self.take_next_to_floodings_ocean(area);
        }
        match tile {
            TileKind::Ocean => {
                self.raise_terraform_rating(player, 1);
                self.log.push(LogEvent::OceansRaised { player, oceans: self.board.oceans() });
            }
            TileKind::Greenery => self.raise_oxygen(player),
            TileKind::City | TileKind::Special => {}
        }
        if matches!(special, Some(SpecialTile::MiningArea | SpecialTile::MiningRights)) {
            self.raise_mining_production(player, area);
        }
        self.set_off(Happened::TilePlaced { player, tile, on_mars: row_and_position(area).is_some() });
        if self.is_placing() {
            self.waiting_bonus = Some(area);
            return;
        }
        self.grant_placement_bonus(player, area);
        if let Some(waiting) = self.waiting_bonus.take()
            && self.has_placement_bonus(waiting)
        {
            self.log.push(LogEvent::CollectsWaitingBonus { player, area: waiting });
            self.grant_placement_bonus(player, waiting);
        }
    }

    /// Whether placing a Tile on `area` now gives anything: a printed bonus or an adjacent Ocean.
    fn has_placement_bonus(&self, area: usize) -> bool {
        !printed(area).bonus.is_empty() || self.board.adjacent(area, TileKind::Ocean) > 0
    }

    /// What `player` gains for placing a Tile on `area`: the bonus printed on it, and
    /// MegaCredits for each Ocean next to it.
    fn grant_placement_bonus(&mut self, player: usize, area: usize) {
        let bonus = printed(area).bonus;
        for item in BonusItem::ALL {
            let amount = bonus.iter().filter(|&&each| each == item).count() as i32;
            if amount == 0 {
                continue;
            }
            self.log.push(LogEvent::PlacementBonus { player, item, amount });
            match item.resource() {
                Some(resource) => self.players[player].resources[resource] += amount,
                None => self.draw(player, amount),
            }
        }
        if !bonus.is_empty() {
            self.set_off(Happened::PlacementBonus { player, area });
        }
        let oceans = self.board.adjacent(area, TileKind::Ocean);
        if oceans > 0 {
            self.players[player].resources.megacredits += self.megacredits_from_oceans_next_to(area);
            self.log.push(LogEvent::AdjacentOceans { player, oceans });
        }
    }

    /// What a Tile placed on `area` gains its Player for the Oceans next to it.
    pub(crate) fn megacredits_from_oceans_next_to(&self, area: usize) -> i32 {
        OCEAN_ADJACENCY_BONUS * self.board.adjacent(area, TileKind::Ocean) as i32
    }

    /// Raises `player`'s Terraform Rating `by` so many steps, which United Nations Mars Initiative's
    /// action looks for.
    pub(crate) fn raise_terraform_rating(&mut self, player: usize, by: i32) {
        self.players[player].terraform_rating += by;
        self.players[player].terraform_rating_raised = true;
    }

    /// Raises `player`'s Production of `resource` by `by` steps, or lowers it below zero.
    pub(crate) fn change_production(&mut self, player: usize, resource: Resource, by: i32) {
        self.players[player].production[resource] += by;
        self.log.push(LogEvent::ProductionChanged { player, resource, by });
    }

    /// Raises Oxygen one step, which gives `player` one Terraform Rating, and at 8 % a
    /// Temperature step too. At its maximum, Oxygen stays put and nobody gains anything.
    pub(crate) fn raise_oxygen(&mut self, player: usize) {
        if self.oxygen >= MAX_OXYGEN {
            self.log.push(LogEvent::OxygenAlreadyAtMaximum);
            return;
        }
        self.oxygen += 1;
        self.raise_terraform_rating(player, 1);
        self.log.push(LogEvent::OxygenRaised { player, oxygen: self.oxygen });
        if self.oxygen == TEMPERATURE_BONUS_OXYGEN {
            self.log.push(LogEvent::TemperatureBonus { player });
            self.raise_temperature(player);
        }
    }

    /// Raises Temperature one step, which gives `player` one Terraform Rating, plus the
    /// track bonus on that step if there is one. At its maximum, Temperature stays put and
    /// nobody gains anything.
    pub(crate) fn raise_temperature(&mut self, player: usize) {
        if self.temperature >= MAX_TEMPERATURE {
            self.log.push(LogEvent::TemperatureAlreadyAtMaximum);
            return;
        }
        self.temperature += TEMPERATURE_STEP;
        self.raise_terraform_rating(player, 1);
        self.log.push(LogEvent::TemperatureRaised { player, temperature: self.temperature });
        if HEAT_PRODUCTION_BONUS_TEMPERATURES.contains(&self.temperature) {
            self.players[player].production.heat += 1;
            self.log.push(LogEvent::HeatProductionBonus { player, temperature: self.temperature });
        }
        if self.temperature == OCEAN_BONUS_TEMPERATURE {
            self.log.push(LogEvent::OceanBonus { player });
            self.place_ocean(Areas::Usual);
        }
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
