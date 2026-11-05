//! A Scenario: a described position to start a Game from instead of normal setup.
//! Tests (and later the dev panel's state editor) build Games this way. Anything a
//! Scenario leaves out takes the normal defaults; an unknown field is an error, so a
//! typo in a test fails loudly instead of being ignored.

use std::collections::BTreeMap;

use serde::{Deserialize, Deserializer, Serialize};

use crate::board::{Board, Reservation, SpecialTile, Tile, TileKind, find_area, printed, row_and_position};
use crate::card_flow::Buying;
use crate::card_resources::CardResources;
use crate::card_set::CardSet;
use crate::cards::{CARD_CATALOG, find_corporation, find_project_card};
use crate::corporations::ChoosingCorporation;
use crate::deck::Deck;
use crate::draft::Drafting;
use crate::game::{
    Game, MAX_OCEANS, MAX_OXYGEN, MAX_TEMPERATURE, MIN_TEMPERATURE, Player, STARTING_TERRAFORM_RATING,
    TEMPERATURE_STEP, check_player_count, check_seed, resources_without_a_corporation,
};
use crate::log::player_name;
use crate::milestones_and_awards::{AWARD_COSTS, Award, MAX_MILESTONES_CLAIMED, Milestone};
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
    /// Who holds the first-player marker. The Scenario starts with their Turn.
    pub first_player: usize,
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
            land_claim: None,
            milestones: Vec::new(),
            awards: Vec::new(),
            players: vec![ScenarioPlayer::default(); 2],
            deck: Vec::new(),
            discard: Vec::new(),
            draft: true,
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

    /// Puts this Player's Card Resources on their played cards, or says why the rules never
    /// allow them there.
    fn put_card_resources(&self, index: usize, on: &mut CardResources) -> Result<(), String> {
        let name = player_name(index);
        for (id, &amount) in &self.card_resources {
            if !self.played_cards.contains(id) {
                return Err(format!("{name} has Card Resources on '{id}', which they have not played"));
            }
            let card = find_project_card(id).ok_or_else(|| format!("there is no Project Card '{id}'"))?;
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
                cards_named(&player.played_cards, &mut named_cards)?.into_iter().collect();
            let corporation = match &player.corporation {
                Some(id) => Some(corporation_named(id, &mut named_cards)?),
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
            players.push(Player {
                resources: player.resources,
                production: player.production,
                terraform_rating: player.terraform_rating,
                passed: false,
                hand: cards_named(&player.hand, &mut named_cards)?.into_iter().collect(),
                played,
                used_actions: CardSet::default(),
                next_card: None,
                buying: Buying::default(),
                drafting: Drafting::default(),
                choosing_corporation: ChoosingCorporation::default(),
                first_action_due: player.first_action_due,
                terraform_rating_raised: false,
            });
        }
        let mut card_resources = CardResources::default();
        for (index, player) in self.players.iter().enumerate() {
            player.put_card_resources(index, &mut card_resources)?;
        }
        let top_of_deck = cards_named(&self.deck, &mut named_cards)?;
        let discard = cards_named(&self.discard, &mut named_cards)?.into_iter().collect();
        let mut game = Game::prepare(Start::Scenario(self.clone()), players);
        game.deck = Deck::shuffled(named_cards, &top_of_deck, &mut game.random_numbers);
        game.discard = discard;
        game.card_resources = card_resources;
        game.temperature = self.temperature;
        game.oxygen = self.oxygen;
        for tile in &self.tiles {
            let area = tile.check(self.players.len())?;
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
        game.begin(self.generation, self.first_player);
        Ok(game)
    }
}

/// The Project Cards named by `ids`, in order. Each must be named in no other place:
/// `named_so_far` collects every card the Scenario has named.
fn cards_named(ids: &[String], named_so_far: &mut CardSet) -> Result<Vec<usize>, String> {
    ids.iter()
        .map(|id| {
            let card = find_project_card(id).ok_or_else(|| format!("there is no Project Card '{id}'"))?;
            named_once(card, id, named_so_far)
        })
        .collect()
}

/// The Corporation named by `id`, which no other Player may have.
fn corporation_named(id: &str, named_so_far: &mut CardSet) -> Result<usize, String> {
    let card = find_corporation(id).ok_or_else(|| format!("there is no Corporation '{id}'"))?;
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

impl ScenarioTile {
    /// The Area this Tile is on, or why the rules never allow it there.
    fn check(&self, players: usize) -> Result<usize, String> {
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
            // Mohole Area's Tile goes on an Area reserved for Oceans.
            Some(Reservation::Ocean) if self.card == Some(SpecialTile::MoholeArea) => {}
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
