//! The rules: the state of a Game, the Decision it is waiting on, and what each Option does.
//!
//! The Game is always either over or waiting on exactly one Decision for one Player
//! (ADR 0002). Picking one of that Decision's Options is the only way it moves forward.
//! The state is a plain value with no shared references, so copying a Game is cheap
//! (ADR 0004), and nothing in it depends on the clock or on hash-map order (ADR 0010).

use std::fmt;

use serde::{Deserialize, Serialize};

use crate::board::{Board, BonusItem, Tile, TileKind, printed};
use crate::card_flow::Buying;
use crate::card_set::CardSet;
use crate::cards::{CARD_CATALOG, PROJECT_CARDS};
use crate::deck::Deck;
use crate::draft::{DraftPass, Drafting};
use crate::log::LogEvent;
use crate::milestones_and_awards::{AWARD_COSTS, Award, MAX_MILESTONES_CLAIMED, MILESTONE_COST, Milestone};
use crate::playing_cards::{CardTiles, Payment};
use crate::random::RandomNumbers;
use crate::replay::{Replay, Start};
use crate::resources::{Resource, Resources};
use crate::scoring::{Score, final_scores, funded_award_places, winners};

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

/// Temporary until Corporations exist (ticket 21): every Player starts with this many
/// MegaCredits, as Helion and Saturn Systems do, and buys their setup cards with them.
pub const STARTING_MEGACREDITS: i32 = 42;

pub const ACTIONS_PER_TURN: u32 = 2;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Settings {
    pub players: usize,
    pub seed: u64,
    /// While most cards are not implemented yet: the implemented ones are shuffled and put on
    /// top of the deck, so they are dealt first. Off, the deck is shuffled as the rules say.
    #[serde(default)]
    pub implemented_cards_first: bool,
    /// The Draft variant in the Research phase. On by default (ADR 0003), but a Replay saved
    /// before the Draft existed has no such setting, and reads as off, as it was played.
    #[serde(default)]
    pub draft: bool,
}

#[derive(Clone, Debug)]
pub struct Player {
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
    /// Passed for the rest of this Generation's Action phase.
    pub passed: bool,
    pub hand: CardSet,
    /// The cards they have played, Events included.
    pub played: CardSet,
    /// In the setup or a Research phase, what they are buying from.
    pub buying: Buying,
    /// In the Draft, what they are drafting.
    pub drafting: Drafting,
}

impl Player {
    pub fn new() -> Player {
        Player {
            resources: starting_resources(),
            production: Resources::default(),
            terraform_rating: STARTING_TERRAFORM_RATING,
            passed: false,
            hand: CardSet::default(),
            played: CardSet::default(),
            buying: Buying::default(),
            drafting: Drafting::default(),
        }
    }
}

/// What every Player starts with, until Corporations exist: MegaCredits and nothing else.
pub fn starting_resources() -> Resources {
    Resources { megacredits: STARTING_MEGACREDITS, ..Resources::default() }
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
    /// Choose the Area for a Tile.
    Area,
    /// Choose how to pay for the card being played.
    Payment,
    /// Keep one of the cards being drafted, and pass the rest on.
    Draft,
    /// Buy one more of the cards dealt, or be done, in the setup or a Research phase.
    BuyCards,
    /// Sell one more card from the hand, or be done, with the Sell Patents Standard Project.
    SellPatents,
    /// Convert plants into a Greenery once more, or be done, in the final Greenery conversion.
    FinalGreenery,
}

/// One of the answers a Decision offers. (Named `DecisionOption` because Rust already has `Option`.)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecisionOption {
    /// Play this Project Card from the hand, by its index in the card catalog.
    PlayCard(usize),
    /// Keep this card, one of those being drafted, and pass the rest on.
    DraftCard(usize),
    /// Buy this card, one of those dealt, in the setup or a Research phase.
    BuyCard(usize),
    /// Sell this card from the hand, with the Sell Patents Standard Project.
    SellCard(usize),
    /// Pay for `card`, which is being played, this way.
    Pay {
        card: usize,
        payment: Payment,
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
    /// Finished buying cards, selling them, or converting plants in the final Greenery conversion.
    Done,
    /// Place the Tile being placed on this Area.
    PlaceTile {
        tile: TileKind,
        area: usize,
    },
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
    /// The Tile the current Player must place next, if the Game is waiting on an Area for it.
    pub placing: Option<TileKind>,
    /// The card the current Player is playing, while the Game waits on how they pay for it.
    pub paying_for: Option<usize>,
    /// The card whose Tiles the current Player is placing, while it has any left to place.
    pub placing_for: Option<CardTiles>,
    /// How many cards the current Player has sold so far, while they are selling patents.
    pub selling: Option<usize>,
    /// The Area of a Tile whose placement bonus waits until the Tile being placed is down:
    /// a Greenery's waits for the Ocean its 0 °C step gave (see docs/rules-notes.md).
    pub waiting_bonus: Option<usize>,
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
        let players = vec![Player::new(); settings.players];
        let mut game = Game::prepare(Start::Settings(settings), players);
        game.first_player = game.random_numbers.below(game.players.len());
        game.generation = 1;
        let mut on_top = Vec::new();
        if game.settings.implemented_cards_first {
            on_top = (0..PROJECT_CARDS).filter(|&card| CARD_CATALOG[card].effects.is_some()).collect();
            game.random_numbers.shuffle(&mut on_top);
        }
        game.deck = Deck::shuffled(CardSet::default(), &on_top, &mut game.random_numbers);
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
            placing: None,
            paying_for: None,
            placing_for: None,
            selling: None,
            waiting_bonus: None,
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
        let (kind, options) = match (self.placing, self.paying_for, self.selling, self.phase) {
            (Some(tile), ..) => (DecisionKind::Area, self.area_options(tile)),
            (None, Some(card), ..) => (DecisionKind::Payment, self.payment_options(card)),
            (None, None, Some(sold), _) => (DecisionKind::SellPatents, self.selling_options(sold)),
            (None, None, None, Phase::Draft) => (DecisionKind::Draft, self.drafting_options()),
            (None, None, None, Phase::Setup | Phase::Research) => {
                (DecisionKind::BuyCards, self.buying_options())
            }
            (None, None, None, Phase::FinalGreenery) => {
                (DecisionKind::FinalGreenery, vec![DecisionOption::ConvertPlants, DecisionOption::Done])
            }
            (None, None, None, _) => (DecisionKind::Action, self.action_options()),
        };
        Some(Decision {
            player: self.current_player,
            kind,
            sequence: self.replay.picks.len() as u64,
            options,
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

    fn action_options(&self) -> Vec<DecisionOption> {
        let player = &self.players[self.current_player];
        let mut options: Vec<DecisionOption> = player
            .hand
            .iter()
            .filter(|&card| self.can_play(self.current_player, card))
            .map(DecisionOption::PlayCard)
            .collect();
        for project in StandardProject::ALL {
            let can_use = match project {
                StandardProject::SellPatents => !player.hand.is_empty(),
                _ => {
                    player.resources.megacredits >= project.cost()
                        && self.can_take_action_placing(project.tile())
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
            && player.resources.megacredits >= cost
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

    /// Whether an Action that places `tile` (or no Tile, for None) may be taken: only if the
    /// Tile has an Area to go on. Actions that raise a Global Parameter stay open once it is
    /// at its maximum, though: Aquifer once 9 Oceans are placed (see docs/rules-notes.md).
    pub(crate) fn can_take_action_placing(&self, tile: Option<TileKind>) -> bool {
        match tile {
            None => true,
            Some(TileKind::Ocean) if self.board.oceans() >= MAX_OCEANS => true,
            Some(tile) => self.board.has_area_for(tile),
        }
    }

    /// Whether the current Player may claim `milestone`: they meet it and can pay, nobody has
    /// claimed it, and fewer than three Milestones are claimed.
    fn can_claim(&self, milestone: Milestone) -> bool {
        let player = self.current_player;
        self.milestone_cost().is_some_and(|cost| self.players[player].resources.megacredits >= cost)
            && self.claimed_milestones[milestone.index()].is_none()
            && milestone.count(self, player) >= milestone.target()
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

    fn can_convert_plants(&self, player: usize) -> bool {
        self.players[player].resources.plants >= PLANTS_PER_GREENERY
            && self.board.has_area_for(TileKind::Greenery)
    }

    /// Every way the current Player may pay for `card`.
    fn payment_options(&self, card: usize) -> Vec<DecisionOption> {
        let payments = self.payments(self.current_player, card);
        payments.into_iter().map(|payment| DecisionOption::Pay { card, payment }).collect()
    }

    /// Every Area where the current Player may place `tile`.
    fn area_options(&self, tile: TileKind) -> Vec<DecisionOption> {
        let areas = self.board.areas_for(tile, self.current_player);
        areas.into_iter().map(|area| DecisionOption::PlaceTile { tile, area }).collect()
    }

    fn resolve(&mut self, option: DecisionOption) {
        let player = self.current_player;
        match option {
            DecisionOption::PlayCard(card) => match self.payments(player, card)[..] {
                [only_way] => self.play_card(player, card, only_way),
                _ => self.paying_for = Some(card),
            },
            DecisionOption::Pay { card, payment } => {
                self.paying_for = None;
                self.play_card(player, card, payment);
            }
            DecisionOption::DraftCard(card) => self.draft(card),
            DecisionOption::BuyCard(card) => self.buy(card),
            DecisionOption::SellCard(card) => self.sell(card),
            // It has no price: the Player picks the cards to sell next.
            DecisionOption::UseStandardProject(StandardProject::SellPatents) => self.selling = Some(0),
            DecisionOption::UseStandardProject(project) => {
                self.players[player].resources.megacredits -= project.cost();
                self.log.push(LogEvent::UsedStandardProject { player, project });
                match project {
                    StandardProject::SellPatents => {
                        unreachable!("Sell Patents begins with the cards to sell")
                    }
                    StandardProject::PowerPlant => self.change_production(player, Resource::Energy, 1),
                    StandardProject::Asteroid => self.raise_temperature(player),
                    StandardProject::Aquifer => self.place_ocean(),
                    StandardProject::Greenery => self.placing = Some(TileKind::Greenery),
                    StandardProject::City => {
                        self.change_production(player, Resource::MegaCredits, 1);
                        self.placing = Some(TileKind::City);
                    }
                }
                self.finish_unless_placing();
            }
            DecisionOption::ClaimMilestone(milestone) => {
                self.players[player].resources.megacredits -= MILESTONE_COST;
                self.claimed_milestones[milestone.index()] = Some(player);
                self.log.push(LogEvent::ClaimedMilestone { player, milestone });
                self.finish_unless_placing();
            }
            DecisionOption::FundAward { award, cost } => {
                self.players[player].resources.megacredits -= cost;
                self.funded_awards[award.index()] = Some(player);
                self.log.push(LogEvent::FundedAward { player, award, cost });
                self.finish_unless_placing();
            }
            DecisionOption::ConvertPlants => {
                self.players[player].resources.plants -= PLANTS_PER_GREENERY;
                self.log.push(LogEvent::ConvertedPlants { player });
                self.placing = Some(TileKind::Greenery);
                self.finish_unless_placing();
            }
            DecisionOption::ConvertHeat => {
                self.players[player].resources.heat -= HEAT_PER_TEMPERATURE_STEP;
                self.log.push(LogEvent::ConvertedHeat { player });
                self.raise_temperature(player);
                self.finish_unless_placing();
            }
            DecisionOption::PlaceTile { tile, area } => {
                self.placing = None;
                self.place_tile(player, tile, area);
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
            DecisionOption::Done if self.selling.is_some() => self.finish_selling(),
            DecisionOption::Done if self.phase == Phase::FinalGreenery => {
                self.log.push(LogEvent::DoneConvertingPlants { player });
                self.offer_final_greenery_from(self.index_in_player_order() + 1);
            }
            DecisionOption::Done => self.done_buying(),
        }
    }

    /// Unless a Tile is still to be placed, a card's included: the current Action ends, or in
    /// the final Greenery conversion, the current Player may convert again.
    pub(crate) fn finish_unless_placing(&mut self) {
        if self.placing.is_none() {
            self.place_next_card_tile();
        }
        match (self.placing, self.phase) {
            (Some(_), _) => {}
            (None, Phase::FinalGreenery) => self.offer_final_greenery_from(self.index_in_player_order()),
            (None, _) => self.finish_action(),
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

    /// Each Player's energy turns into heat, then every Resource gains its Production,
    /// and MegaCredits also gain Terraform Rating.
    fn production_phase(&mut self) {
        self.log.push(LogEvent::ProductionPhase);
        for (index, player) in self.players.iter_mut().enumerate() {
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

    /// The current Player has an Ocean to place, unless all 9 are already placed: then the
    /// Aquifer they paid for, or the 0 °C bonus they reached, places nothing (see
    /// docs/rules-notes.md).
    pub(crate) fn place_ocean(&mut self) {
        if self.board.oceans() < MAX_OCEANS {
            self.placing = Some(TileKind::Ocean);
        } else {
            self.log.push(LogEvent::OceansAlreadyAtMaximum);
        }
    }

    /// Places `tile` for `player` on `area`. An Ocean raises their Terraform Rating, and a
    /// Greenery Oxygen. Then `player` collects the placement bonus, unless that raise gave
    /// them another Tile to place: the bonus then waits until that Tile is down.
    fn place_tile(&mut self, player: usize, tile: TileKind, area: usize) {
        let owner = if tile == TileKind::Ocean { None } else { Some(player) };
        self.board.place(area, Tile { kind: tile, owner });
        self.log.push(LogEvent::PlacedTile { player, tile, area });
        match tile {
            TileKind::Ocean => {
                self.players[player].terraform_rating += 1;
                self.log.push(LogEvent::OceansRaised { player, oceans: self.board.oceans() });
            }
            TileKind::Greenery => self.raise_oxygen(player),
            TileKind::City => {}
        }
        if self.placing.is_some() {
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
        let oceans = self.board.adjacent(area, TileKind::Ocean);
        if oceans > 0 {
            self.players[player].resources.megacredits += OCEAN_ADJACENCY_BONUS * oceans as i32;
            self.log.push(LogEvent::AdjacentOceans { player, oceans });
        }
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
        self.players[player].terraform_rating += 1;
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
        self.players[player].terraform_rating += 1;
        self.log.push(LogEvent::TemperatureRaised { player, temperature: self.temperature });
        if HEAT_PRODUCTION_BONUS_TEMPERATURES.contains(&self.temperature) {
            self.players[player].production.heat += 1;
            self.log.push(LogEvent::HeatProductionBonus { player, temperature: self.temperature });
        }
        if self.temperature == OCEAN_BONUS_TEMPERATURE {
            self.log.push(LogEvent::OceanBonus { player });
            self.place_ocean();
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
