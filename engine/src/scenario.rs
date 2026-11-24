//! A Scenario: a described position to start a Game from instead of normal setup.
//! Tests and the dev panel's state editor build Games this way. Anything a Scenario leaves
//! out takes the normal defaults; an unknown field is an error, so a typo in a test fails
//! loudly instead of being ignored. `Game::to_scenario` describes a Game's position as one.

use std::collections::BTreeMap;

use serde::{Deserialize, Deserializer, Serialize};

use crate::board::{
    AREA_COUNT, Areas, Board, Reservation, SpecialTile, Tile, TileKind, area_id, find_area, printed,
    row_and_position,
};
use crate::card_flow::Buying;
use crate::card_resources::CardResources;
use crate::card_set::CardSet;
use crate::cards::{
    CARD_CATALOG, CARDS_OF_TYPE, CardType, Expansion, find_card, find_corporation, find_prelude_card,
    find_project_card, project_cards_with,
};
use crate::corporations::ChoosingCorporation;
use crate::deck::Deck;
use crate::draft::Drafting;
use crate::game::{
    ACTIONS_PER_TURN, Game, MAX_OCEANS, MAX_OXYGEN, MAX_TEMPERATURE, MIN_TEMPERATURE, Phase, Player,
    STARTING_TERRAFORM_RATING, TEMPERATURE_STEP, check_player_count, check_seed,
    resources_without_a_corporation,
};
use crate::log::player_name;
use crate::milestones_and_awards::{AWARD_COSTS, Award, MAX_MILESTONES_CLAIMED, Milestone};
use crate::prelude_cards::{PRELUDE_CARDS_KEPT, PreludeCards, PreludeSet};
use crate::replay::Start;
use crate::resources::{MIN_MEGACREDIT_PRODUCTION, Resource, Resources};

/// The lowest Terraform Rating a Scenario may give a Player. MegaCredit Production stops at
/// -5, so from 5 up, a Production phase never leaves anyone with fewer than 0 MegaCredits.
/// (A Game from normal setup never gets near it: Terraform Rating starts at 20 and only rises.)
const MIN_TERRAFORM_RATING: i32 = -MIN_MEGACREDIT_PRODUCTION;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Scenario {
    pub seed: u64,
    pub generation: u32,
    /// Who holds the first-player marker. The Scenario starts with their Turn, unless it says
    /// whose it is.
    pub first_player: usize,
    /// Whose Turn it is, in the middle of a Generation. Left out, the first player's.
    pub current_player: Option<usize>,
    /// How many Actions they have taken in this Turn.
    pub actions_this_turn: u32,
    pub temperature: i32,
    pub oxygen: i32,
    /// The Tiles on the board. The number of Oceans is the number of Ocean Tiles.
    pub tiles: Vec<ScenarioTile>,
    /// The Area claimed with Land Claim, if any, and by whom.
    pub land_claim: Option<LandClaim>,
    /// The Milestones claimed so far, and by whom.
    pub milestones: Vec<ClaimedMilestone>,
    /// The Awards funded so far, and by whom.
    pub awards: Vec<FundedAward>,
    pub players: Vec<ScenarioPlayer>,
    /// Cards on top of the deck, by catalog id, the first drawn first. Every Project Card
    /// that is in no hand, among no played cards and not here is shuffled beneath them.
    pub deck: Vec<String>,
    /// The cards in the discard pile, by catalog id.
    pub discard: Vec<String>,
    /// Whether the Research phases have the Draft. On by default (ADR 0003).
    pub draft: bool,
    /// Whether the Game has Prelude: Prelude's Project Cards are in the deck, and Players may hold
    /// Prelude Cards. Off by default, and only a Scenario that has it on names it.
    #[serde(skip_serializing_if = "std::ops::Not::not")]
    pub prelude: bool,
    /// Whether the last Prelude Card a Player plays is a Decision of its own (see `Settings`). Off by
    /// default, and only a Scenario that has it on names it.
    #[serde(skip_serializing_if = "std::ops::Not::not")]
    pub ask_last_prelude_card: bool,
    /// Only with Prelude: the Prelude Cards in the Prelude deck, which Valley Trust's first action
    /// draws from at random, by catalog id. Left out, every Prelude Card the Scenario names nowhere
    /// else.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub prelude_deck: Option<Vec<String>>,
}

impl Default for Scenario {
    fn default() -> Scenario {
        Scenario {
            seed: 0,
            generation: 1,
            first_player: 0,
            current_player: None,
            actions_this_turn: 0,
            temperature: MIN_TEMPERATURE,
            oxygen: 0,
            tiles: Vec::new(),
            land_claim: None,
            milestones: Vec::new(),
            awards: Vec::new(),
            players: vec![ScenarioPlayer::default(); 2],
            deck: Vec::new(),
            discard: Vec::new(),
            draft: true,
            prelude: false,
            ask_last_prelude_card: false,
            prelude_deck: None,
        }
    }
}

/// A Tile on an Area, such as `{"area": "C3", "tile": "city", "owner": 0}`, or a special Tile,
/// such as `{"area": "C4", "tile": "special", "card": "nuclear_zone", "owner": 0}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScenarioTile {
    pub area: String,
    pub tile: TileKind,
    /// The owning Player; Oceans have none.
    #[serde(default)]
    pub owner: Option<usize>,
    /// For a special Tile, the card whose symbol it is printed with: Capital's for its City.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub card: Option<SpecialTile>,
}

/// The Area claimed with Land Claim and the Player who claimed it, such as
/// `{"area": "C3", "player": 1}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LandClaim {
    /// The Area claimed, by its name: "C3".
    pub area: String,
    /// The Player who claimed it, indexed from 0.
    pub player: usize,
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
    /// The Resources given, such as `{"plants": 8}`; the rest are what a Player holds without a
    /// Corporation.
    #[serde(deserialize_with = "over_starting_resources")]
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
    /// The cards in their hand, by catalog id: `["mine", "trees"]`.
    pub hand: Vec<String>,
    /// The cards they have played, by catalog id.
    pub played_cards: Vec<String>,
    /// The Card Resources on their played cards, by catalog id: `{"tardigrades": 3}`.
    pub card_resources: BTreeMap<String, i32>,
    /// Their Corporation, by catalog id, revealed. It gives no starting values: the Scenario's
    /// Resources and Production are what they hold now.
    pub corporation: Option<String>,
    /// Whether they must still take their Corporation's first action.
    pub first_action_due: bool,
    /// Whether they have passed for the rest of this Generation's Action phase.
    pub passed: bool,
    /// The played cards, their Corporation included, whose action they have used this Generation.
    pub used_actions: Vec<String>,
    /// Whether their Terraform Rating was raised this Generation.
    pub terraform_rating_raised: bool,
    /// The Event they played whose effect waits on the next card they play this Generation.
    pub next_card: Option<String>,
    /// With Prelude, the Prelude Cards they kept and have still to play, by catalog id. The Scenario
    /// then starts where Players play them, before the Action phase.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub prelude_cards: Vec<String>,
    /// With Prelude, the Prelude Cards they have played, by catalog id.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub played_prelude_cards: Vec<String>,
}

impl Default for ScenarioPlayer {
    fn default() -> ScenarioPlayer {
        ScenarioPlayer {
            resources: resources_without_a_corporation(),
            production: Resources::default(),
            terraform_rating: STARTING_TERRAFORM_RATING,
            hand: Vec::new(),
            played_cards: Vec::new(),
            card_resources: BTreeMap::new(),
            corporation: None,
            first_action_due: false,
            passed: false,
            used_actions: Vec::new(),
            terraform_rating_raised: false,
            next_card: None,
            prelude_cards: Vec::new(),
            played_prelude_cards: Vec::new(),
        }
    }
}

impl ScenarioPlayer {
    /// Whether the rules allow these Resources, this Production and this Terraform Rating
    /// for Player `index`.
    fn check(&self, index: usize) -> Result<(), String> {
        let name = player_name(index);
        if self.terraform_rating < MIN_TERRAFORM_RATING {
            return Err(format!(
                "{name}'s Terraform Rating must be {MIN_TERRAFORM_RATING} or more, not {}",
                self.terraform_rating
            ));
        }
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

    /// The cards among `played` whose action this Player has used, or why they can't have.
    fn used_actions_among(&self, index: usize, played: CardSet, prelude: bool) -> Result<CardSet, String> {
        let mut used = CardSet::default();
        for id in &self.used_actions {
            let card = find_project_card(id, prelude)
                .or_else(|| find_corporation(id, prelude))
                .ok_or_else(|| format!("there is no card '{id}'"))?;
            check_played(index, card, id, played)?;
            if CARD_CATALOG[card].action().is_none() {
                return Err(format!("'{id}' has no action"));
            }
            used.insert(card);
        }
        Ok(used)
    }

    /// The Event among `played` that waits on this Player's next card, or why it can't.
    fn event_waiting(&self, index: usize, played: CardSet, prelude: bool) -> Result<Option<usize>, String> {
        let Some(id) = &self.next_card else { return Ok(None) };
        let card = project_card_named(id, prelude)?;
        check_played(index, card, id, played)?;
        if CARD_CATALOG[card].effects.as_ref().is_none_or(|effects| effects.next_card.is_none()) {
            return Err(format!("'{id}' does nothing to the next card played"));
        }
        Ok(Some(card))
    }

    /// Puts this Player's Card Resources on their played cards, or says why the rules never
    /// allow them there.
    fn put_card_resources(&self, index: usize, on: &mut CardResources, prelude: bool) -> Result<(), String> {
        let name = player_name(index);
        for (id, &amount) in &self.card_resources {
            if !self.played_cards.contains(id) {
                return Err(format!("{name} has Card Resources on '{id}', which they have not played"));
            }
            let card = project_card_named(id, prelude)?;
            if CARD_CATALOG[card].holds().is_none() {
                return Err(format!("'{id}' holds no Card Resources"));
            }
            if !(0..=i32::from(u16::MAX)).contains(&amount) {
                return Err(format!("'{id}' cannot hold {amount} Card Resources"));
            }
            on.set(card, amount);
        }
        Ok(())
    }
}

/// Whether Player `index` has played `card`, named by `id`, among the cards `played`.
fn check_played(index: usize, card: usize, id: &str, played: CardSet) -> Result<(), String> {
    if played.contains(card) {
        Ok(())
    } else {
        Err(format!("{} names '{id}', which they have not played", player_name(index)))
    }
}

/// Reads a Scenario Player's Resources given in part, such as `{"plants": 8}`: the
/// Resources left out keep what a Player holds without a Corporation.
fn over_starting_resources<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Resources, D::Error> {
    let given = BTreeMap::<Resource, i32>::deserialize(deserializer)?;
    let mut resources = resources_without_a_corporation();
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
        let mut named_cards = CardSet::default();
        let mut players = Vec::new();
        for (index, player) in self.players.iter().enumerate() {
            player.check(index)?;
            let mut played: CardSet =
                cards_named(&player.played_cards, self.prelude, &mut named_cards)?.into_iter().collect();
            let played_prelude_cards =
                prelude_cards_named(index, &player.played_prelude_cards, self.prelude, &mut named_cards)?;
            played = played.union(played_prelude_cards.into_iter().collect());
            let kept = prelude_cards_named(index, &player.prelude_cards, self.prelude, &mut named_cards)?;
            check_prelude_cards_to_play(index, &kept)?;
            let corporation = match &player.corporation {
                Some(id) => Some(corporation_named(id, self.prelude, &mut named_cards)?),
                None => None,
            };
            if let Some(card) = corporation {
                played.insert(card);
            }
            if player.first_action_due
                && corporation.and_then(|card| CARD_CATALOG[card].first_action()).is_none()
            {
                return Err(format!("{} has no first action to take", player_name(index)));
            }
            let used_actions = player.used_actions_among(index, played, self.prelude)?;
            let next_card = player.event_waiting(index, played, self.prelude)?;
            players.push(Player {
                resources: player.resources,
                production: player.production,
                terraform_rating: player.terraform_rating,
                passed: false,
                hand: cards_named(&player.hand, self.prelude, &mut named_cards)?.into_iter().collect(),
                played,
                used_actions,
                next_card,
                buying: Buying::default(),
                drafting: Drafting::default(),
                choosing_corporation: ChoosingCorporation::default(),
                prelude_cards: PreludeCards {
                    dealt: PreludeSet::default(),
                    kept: kept.into_iter().collect(),
                },
                first_action_due: player.first_action_due,
                terraform_rating_raised: player.terraform_rating_raised,
            });
        }
        let mut card_resources = CardResources::default();
        for (index, player) in self.players.iter().enumerate() {
            player.put_card_resources(index, &mut card_resources, self.prelude)?;
        }
        let prelude_deck = self.prelude_deck_named(&mut named_cards)?;
        let top_of_deck = cards_named(&self.deck, self.prelude, &mut named_cards)?;
        let discard = cards_named(&self.discard, self.prelude, &mut named_cards)?.into_iter().collect();
        let mut game = Game::prepare(Start::Scenario(Box::new(self.clone())), players);
        let project_cards = project_cards_with(self.prelude);
        game.deck = Deck::shuffled(project_cards, named_cards, &top_of_deck, &mut game.random_numbers);
        game.discard = discard;
        game.prelude_deck = prelude_deck;
        game.card_resources = card_resources;
        game.temperature = self.temperature;
        game.oxygen = self.oxygen;
        let mut allowed = AllowedByCards::played_by(&game.players);
        for tile in &self.tiles {
            let area = tile.check(self.players.len(), &mut allowed)?;
            if game.board.tile(area).is_some() {
                return Err(format!("a Scenario cannot put two Tiles on {}", tile.area));
            }
            game.board.place(area, Tile { kind: tile.tile, owner: tile.owner, special: tile.card });
        }
        if let Some(claim) = &self.land_claim {
            let area = claim.check(&game.board, self.players.len())?;
            game.board.claim_area(area, claim.player);
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
        if game.players.iter().any(|player| !player.prelude_cards.kept.is_empty()) {
            self.check_before_the_action_phase()?;
            game.generation = self.generation;
            game.first_player = self.first_player;
            game.begin_playing_prelude_cards();
        } else {
            game.begin(self.generation, self.first_player);
            self.resume_the_turn(&mut game)?;
        }
        Ok(game)
    }

    /// The Prelude deck: the Prelude Cards named for it, or with none named every one named nowhere
    /// else, so far as `named_so_far` says. Empty without Prelude.
    fn prelude_deck_named(&self, named_so_far: &mut CardSet) -> Result<PreludeSet, String> {
        match &self.prelude_deck {
            Some(ids) if !self.prelude && !ids.is_empty() => {
                Err("the Scenario has a Prelude deck, and no Prelude".to_string())
            }
            Some(ids) => ids
                .iter()
                .map(|id| {
                    let card =
                        find_prelude_card(id).ok_or_else(|| format!("there is no Prelude Card '{id}'"))?;
                    named_once(card, id, named_so_far)
                })
                .collect(),
            None if self.prelude => Ok(CARDS_OF_TYPE.prelude_cards.without(*named_so_far).iter().collect()),
            None => Ok(PreludeSet::default()),
        }
    }

    /// Whether this Scenario, in which Players have Prelude Cards still to play, starts before the
    /// Action phase, as it must.
    fn check_before_the_action_phase(&self) -> Result<(), String> {
        let under_way = self.current_player.is_some()
            || self.actions_this_turn > 0
            || self.players.iter().any(|player| player.passed);
        if under_way {
            return Err(
                "a Scenario in which Players have Prelude Cards still to play starts before the Action \
                        phase, so nobody has a Turn under way or has passed"
                    .to_string(),
            );
        }
        Ok(())
    }

    /// Who has passed and whose Turn it is, for a position in the middle of a Generation.
    fn resume_the_turn(&self, game: &mut Game) -> Result<(), String> {
        let current = self.current_player.unwrap_or(self.first_player);
        check_player(current, self.players.len(), "whose Turn it is")?;
        if self.actions_this_turn >= ACTIONS_PER_TURN {
            return Err(format!(
                "a Player has taken at most {} Action when it is still their Turn, not {}",
                ACTIONS_PER_TURN - 1,
                self.actions_this_turn
            ));
        }
        if self.players[current].passed {
            return Err(format!("{} has passed, so it cannot be their Turn", player_name(current)));
        }
        for (player, given) in game.players.iter_mut().zip(&self.players) {
            player.passed = given.passed;
        }
        game.current_player = current;
        game.actions_this_turn = self.actions_this_turn;
        Ok(())
    }
}

impl Game {
    /// This Game's position as a Scenario. At the start of a Turn or Action it starts the same
    /// position, but for the cards passed in the Draft and what is yet to be shuffled. Otherwise
    /// it starts the Action phase of this Generation, and what is under way is dropped: any card
    /// being played, bought, drafted or looked at is shuffled into the deck, beneath its cards.
    pub fn to_scenario(&self) -> Scenario {
        let in_action_phase = self.phase == Phase::Action;
        Scenario {
            seed: self.settings.seed,
            generation: self.generation,
            first_player: self.first_player,
            current_player: in_action_phase.then_some(self.current_player),
            actions_this_turn: if in_action_phase { self.actions_this_turn } else { 0 },
            temperature: self.temperature,
            oxygen: self.oxygen,
            tiles: (0..AREA_COUNT)
                .filter_map(|area| {
                    self.board.tile(area).map(|tile| ScenarioTile {
                        area: area_id(area),
                        tile: tile.kind,
                        owner: tile.owner,
                        card: tile.special,
                    })
                })
                .collect(),
            land_claim: self
                .board
                .claim()
                .map(|claim| LandClaim { area: area_id(claim.area), player: claim.player }),
            milestones: Milestone::ALL
                .into_iter()
                .filter_map(|milestone| {
                    let claimed_by = self.claimed_milestones[milestone.index()]?;
                    Some(ClaimedMilestone { milestone, claimed_by })
                })
                .collect(),
            awards: Award::ALL
                .into_iter()
                .filter_map(|award| {
                    let funded_by = self.funded_awards[award.index()]?;
                    Some(FundedAward { award, funded_by })
                })
                .collect(),
            players: self.players.iter().map(|player| self.describe(player, in_action_phase)).collect(),
            deck: ids(self.deck.iter()),
            discard: ids(self.discard.iter()),
            draft: self.settings.draft,
            prelude: self.settings.prelude,
            ask_last_prelude_card: self.settings.ask_last_prelude_card,
            // Prelude Cards drawn for a first action under way go back into it.
            prelude_deck: self.settings.prelude.then(|| {
                let mut deck = self.prelude_deck;
                if in_action_phase {
                    let drawn = self.players.iter().map(|player| player.prelude_cards.kept);
                    deck = drawn.fold(deck, PreludeSet::union);
                }
                ids(deck.iter())
            }),
        }
    }

    fn describe(&self, player: &Player, in_action_phase: bool) -> ScenarioPlayer {
        ScenarioPlayer {
            resources: player.resources,
            production: player.production,
            terraform_rating: player.terraform_rating,
            hand: ids(player.hand.iter()),
            played_cards: ids(player.played_project_cards().iter()),
            card_resources: player
                .cards_holding_card_resources()
                .iter()
                .map(|card| (card, self.card_resources.on(card)))
                .filter(|&(_, amount)| amount != 0)
                .map(|(card, amount)| (id_of(card), amount))
                .collect(),
            corporation: player.corporation().map(id_of),
            // Prelude Cards drawn for a first action under way (Valley Trust) mean it is due again.
            first_action_due: player.first_action_due
                || in_action_phase && !player.prelude_cards.kept.is_empty(),
            // Everyone who passed is back in when the next Action phase begins.
            passed: in_action_phase && player.passed,
            used_actions: ids(player.used_actions.iter()),
            terraform_rating_raised: player.terraform_rating_raised,
            // A Prelude Card's effect on the card it plays is under way, and dropped.
            next_card: player
                .next_card
                .filter(|&card| CARD_CATALOG[card].card_type == CardType::Event)
                .map(id_of),
            // Only once setup is over: a Prelude Card kept at setup is dropped with the rest of it.
            prelude_cards: if self.phase == Phase::PreludeCards {
                player.prelude_cards.kept.iter().map(id_of).collect()
            } else {
                Vec::new()
            },
            played_prelude_cards: ids(player.played_prelude_cards().iter()),
        }
    }
}

fn id_of(card: usize) -> String {
    CARD_CATALOG[card].id.clone()
}

/// The catalog ids of `cards`.
fn ids(cards: impl Iterator<Item = usize>) -> Vec<String> {
    cards.map(id_of).collect()
}

/// The Project Cards of a Game with Prelude or without named by `ids`, in order. Each must be named
/// in no other place: `named_so_far` collects every card the Scenario has named.
fn cards_named(ids: &[String], prelude: bool, named_so_far: &mut CardSet) -> Result<Vec<usize>, String> {
    ids.iter().map(|id| named_once(project_card_named(id, prelude)?, id, named_so_far)).collect()
}

/// The Project Card named `id` in a Game with Prelude or without, or why there is none.
fn project_card_named(id: &str, prelude: bool) -> Result<usize, String> {
    find_project_card(id, prelude).ok_or_else(|| match find_card(id) {
        Some(card) if CARD_CATALOG[card].expansion == Expansion::Prelude && !prelude => {
            format!("'{id}' is a card of the Prelude box, and the Scenario has no Prelude")
        }
        _ => format!("there is no Project Card '{id}'"),
    })
}

/// The Prelude Cards named by `ids` for Player `index`, in order, each named in no other place. Only
/// a Scenario with Prelude names any.
fn prelude_cards_named(
    index: usize,
    ids: &[String],
    prelude: bool,
    named_so_far: &mut CardSet,
) -> Result<Vec<usize>, String> {
    if !prelude && !ids.is_empty() {
        return Err(format!("{} has Prelude Cards, and the Scenario has no Prelude", player_name(index)));
    }
    ids.iter()
        .map(|id| {
            let card = find_prelude_card(id).ok_or_else(|| format!("there is no Prelude Card '{id}'"))?;
            named_once(card, id, named_so_far)
        })
        .collect()
}

/// Whether Player `index` may have `kept` still to play: at most as many as they keep.
fn check_prelude_cards_to_play(index: usize, kept: &[usize]) -> Result<(), String> {
    if kept.len() > PRELUDE_CARDS_KEPT {
        return Err(format!(
            "{} keeps at most {PRELUDE_CARDS_KEPT} Prelude Cards, not {}",
            player_name(index),
            kept.len()
        ));
    }
    Ok(())
}

/// The Corporation named by `id` in a Game with Prelude or without, which no other Player may have.
fn corporation_named(id: &str, prelude: bool, named_so_far: &mut CardSet) -> Result<usize, String> {
    let card = find_corporation(id, prelude).ok_or_else(|| match find_card(id) {
        Some(card) if CARD_CATALOG[card].expansion == Expansion::Prelude && !prelude => {
            format!("'{id}' is a card of the Prelude box, and the Scenario has no Prelude")
        }
        _ => format!("there is no Corporation '{id}'"),
    })?;
    named_once(card, id, named_so_far)
}

/// `card`, named by `id`, unless the Scenario has named it already.
fn named_once(card: usize, id: &str, named_so_far: &mut CardSet) -> Result<usize, String> {
    if named_so_far.contains(card) {
        return Err(format!("a Scenario can have the '{id}' card in only one place"));
    }
    named_so_far.insert(card);
    Ok(card)
}

/// Whether `player` is one of the `players` Players; `who` names them in the error.
fn check_player(player: usize, players: usize, who: &str) -> Result<(), String> {
    if player < players {
        Ok(())
    } else {
        Err(format!("{who} must be one of the Players, indexed 0 to {}, not {player}", players - 1))
    }
}

impl LandClaim {
    /// The Area claimed, or why Land Claim never claims it: it must be on Mars and reserved for
    /// nothing, with no Tile on it but its Player's.
    fn check(&self, board: &Board, players: usize) -> Result<usize, String> {
        let area = find_area(&self.area).ok_or_else(|| format!("there is no Area '{}'", self.area))?;
        check_player(self.player, players, "the Player who claimed an Area")?;
        if row_and_position(area).is_none() || printed(area).reserved.is_some() {
            return Err(format!("Land Claim cannot claim {}, which is reserved", self.area));
        }
        match board.tile(area).and_then(|tile| tile.owner) {
            Some(owner) if owner != self.player => Err(format!(
                "a Tile of {} is on {}, which is claimed by {}",
                player_name(owner),
                self.area,
                player_name(self.player)
            )),
            _ => Ok(area),
        }
    }
}

/// The Tiles still allowed where only a card puts them: one for each card played that does.
struct AllowedByCards {
    /// By Player, as a Player's card puts their own Greenery on an Area reserved for Oceans.
    greeneries_on_ocean_areas: Vec<usize>,
    /// For all Players together, as an Ocean belongs to nobody.
    oceans_on_land: usize,
}

impl AllowedByCards {
    fn played_by(players: &[Player]) -> AllowedByCards {
        let placements_by = |player: &Player, tile, on| {
            let effects = player.played.iter().filter_map(|card| CARD_CATALOG[card].effects.as_ref());
            effects
                .flat_map(|effects| &effects.tiles)
                .filter(|each| each.tile == tile && each.on == on)
                .count()
        };
        AllowedByCards {
            greeneries_on_ocean_areas: players
                .iter()
                .map(|player| placements_by(player, TileKind::Greenery, Areas::ReservedForOceans))
                .collect(),
            oceans_on_land: players
                .iter()
                .map(|player| placements_by(player, TileKind::Ocean, Areas::Land))
                .sum(),
        }
    }

    /// Whether `owner`'s card allows one more Greenery on an Area reserved for Oceans, using it up.
    fn take_greenery_on_an_ocean_area(&mut self, owner: Option<usize>) -> bool {
        let allowed = owner.and_then(|owner| self.greeneries_on_ocean_areas.get_mut(owner));
        allowed.is_some_and(take_one)
    }
}

/// Whether `allowed` has one left, using it up.
fn take_one(allowed: &mut usize) -> bool {
    let any_left = *allowed > 0;
    *allowed = allowed.saturating_sub(1);
    any_left
}

impl ScenarioTile {
    /// The Area this Tile is on, or why the rules never allow it there.
    fn check(&self, players: usize, allowed: &mut AllowedByCards) -> Result<usize, String> {
        let area = find_area(&self.area).ok_or_else(|| format!("there is no Area '{}'", self.area))?;
        let tile = self.tile.name();
        match (self.tile, self.card) {
            (TileKind::Special, None) => {
                return Err(format!("the special Tile on {} needs the card it is printed with", self.area));
            }
            (TileKind::City, Some(SpecialTile::Capital)) | (TileKind::Special, Some(_)) => {}
            (_, Some(card)) => {
                return Err(format!(
                    "{} is no {tile}, so the {tile} on {} cannot be it",
                    card.name(),
                    self.area
                ));
            }
            (_, None) => {}
        }
        let reserved = printed(area).reserved;
        if self.tile == TileKind::Ocean {
            let on_land_by_a_card = reserved.is_none() && take_one(&mut allowed.oceans_on_land);
            if reserved != Some(Reservation::Ocean) && !on_land_by_a_card {
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
            // Mohole Area's Tile goes on an Area reserved for Oceans.
            Some(Reservation::Ocean) if self.card == Some(SpecialTile::MoholeArea) => {}
            // The Greenery of a card such as Mangrove.
            Some(Reservation::Ocean)
                if self.tile == TileKind::Greenery && allowed.take_greenery_on_an_ocean_area(self.owner) => {}
            Some(Reservation::Ocean) => {
                return Err(format!("cannot put a {tile} on {}, which is reserved for Oceans", self.area));
            }
            // The City of the card it is reserved for.
            Some(_) if self.tile == TileKind::City && self.card.is_none() => {}
            Some(_) => {
                return Err(format!(
                    "cannot put a {tile} on {}, which is reserved for the {} card's City",
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
