//! What crosses into Python: the current Decision and the Player View, as plain
//! JSON-shaped values. Every Option gets a readable label for people and structured
//! details for programs (the GUI, and later the AI).

use std::collections::BTreeMap;

use serde::Serialize;

use crate::board::{AREA_COUNT, Areas, Board, TileKind, area_id, area_label, printed, row_and_position};
use crate::card_flow::{CARD_PRICE, PATENT_VALUE};
use crate::card_set::CardSet;
use crate::cards::{CARD_CATALOG, Tag};
use crate::draft::DraftPass;
use crate::game::{
    Decision, DecisionKind, DecisionOption, Game, HEAT_PER_TEMPERATURE_STEP, PLANTS_PER_GREENERY, Phase,
    StandardProject,
};
use crate::log::{listed, player_name};
use crate::milestones_and_awards::{Award, MILESTONE_COST, Milestone};
use crate::playing_cards::{Payment, ProductionChange};
use crate::resources::{Resource, Resources};
use crate::scoring::Score;

#[derive(Serialize)]
pub struct DecisionView {
    pub player: usize,
    pub kind: &'static str,
    pub sequence: u64,
    pub options: Vec<OptionView>,
}

#[derive(Serialize)]
pub struct OptionView {
    pub index: usize,
    pub label: String,
    pub details: OptionDetails,
}

#[derive(Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum OptionDetails {
    /// Play a card from the hand, named by its catalog id.
    PlayCard {
        card: &'static str,
        cost: i32,
    },
    /// Keep one of the cards being drafted, named by its catalog id, and pass the rest on.
    DraftCard {
        card: &'static str,
    },
    /// Buy one of the cards dealt, named by its catalog id.
    BuyCard {
        card: &'static str,
        cost: i32,
    },
    /// Sell a card from the hand with Sell Patents, named by its catalog id, for `megacredits`.
    SellCard {
        card: &'static str,
        megacredits: i32,
    },
    /// One way to pay for the card being played: its MegaCredits, steel and titanium.
    Payment {
        card: &'static str,
        #[serde(flatten)]
        payment: Payment,
    },
    /// One of the Production changes the card being played lets its Player choose.
    ChooseProduction {
        card: &'static str,
        production: Resources,
    },
    /// One of the Player's building cards whose production box Robotic Workforce may copy.
    CopyProductionBox {
        card: &'static str,
    },
    StandardProject {
        project: String,
        cost: i32,
    },
    ClaimMilestone {
        milestone: String,
        cost: i32,
    },
    FundAward {
        award: String,
        cost: i32,
    },
    ConvertPlants {
        plants: i32,
    },
    ConvertHeat {
        heat: i32,
    },
    EndTurn,
    Pass,
    Done,
    /// An Area for the Tile being placed. `on` is left out for the usual Areas of its kind.
    Area {
        area: String,
        tile: TileKind,
        #[serde(skip_serializing_if = "Areas::is_usual")]
        on: Areas,
    },
}

/// What one Player is allowed to know (their Player View), or everything (the full
/// view, which has no viewer).
#[derive(Serialize)]
pub struct View {
    /// The Player whose view this is, or None for the full view.
    pub viewer: Option<usize>,
    pub generation: u32,
    pub phase: &'static str,
    pub temperature: i32,
    /// In percent.
    pub oxygen: i32,
    /// How many Ocean Tiles have been placed.
    pub oceans: usize,
    /// Every Area, on Mars row by row from the top and each row from the left, then off Mars.
    pub board: Vec<AreaView>,
    /// How many cards are in the deck.
    pub deck_size: usize,
    /// The deck by catalog id, from the top down: only in the full view, otherwise None.
    pub deck: Option<Vec<&'static str>>,
    /// How many cards are in the discard pile.
    pub discard_size: usize,
    /// The discard pile by catalog id, in card-number order: it lies face down, so only in the
    /// full view, otherwise None.
    pub discard: Option<Vec<&'static str>>,
    /// Who holds the first-player marker.
    pub first_player: usize,
    /// Whose Turn it is, or None once the Game is over.
    pub current_player: Option<usize>,
    /// How many Actions the current Player has taken in this Turn.
    pub actions_this_turn: u32,
    pub players: Vec<PlayerBoard>,
    /// The five Milestones, in the order printed on the board.
    pub milestones: Vec<MilestoneView>,
    /// What claiming a Milestone costs, or None once three are claimed.
    pub milestone_cost: Option<i32>,
    /// The five Awards, in the order printed on the board.
    pub awards: Vec<AwardView>,
    /// What funding the next Award costs (8, 14 or 20), or None once three are funded.
    pub award_cost: Option<i32>,
    /// Each Player's final score once the Game is over, otherwise None.
    pub scores: Option<Vec<Score>>,
}

/// One Area: what is printed on it, and its Tile if it has one.
#[derive(Serialize)]
pub struct AreaView {
    /// Its name: "E3" on Mars, or "phobos_space_haven" off Mars.
    pub area: String,
    /// The name printed on it, such as "Noctis City", if any.
    pub name: Option<&'static str>,
    /// Its row from the top and position from the left on Mars, both counted from 1,
    /// matching its name. None off Mars.
    pub row: Option<usize>,
    pub position: Option<usize>,
    /// What the Area is kept for: "ocean", or a card's Tile such as "noctis_city".
    pub reserved: Option<&'static str>,
    /// The placement bonus, one entry per item: "steel", "titanium", "plant" or "card".
    pub bonus: Vec<&'static str>,
    pub tile: Option<TileView>,
}

#[derive(Serialize)]
pub struct TileView {
    #[serde(rename = "type")]
    pub kind: TileKind,
    /// The owning Player, or None for an Ocean.
    pub owner: Option<usize>,
}

/// What everyone can see of a Player.
#[derive(Serialize)]
pub struct PlayerBoard {
    pub name: String,
    pub resources: Resources,
    pub production: Resources,
    pub terraform_rating: i32,
    pub passed: bool,
    pub hand_size: usize,
    /// The cards in their hand, by catalog id in card-number order: only in their own Player
    /// View and the full view, otherwise None.
    pub hand: Option<Vec<&'static str>>,
    /// In the setup or a Research phase, what they are buying from: only in their own Player View
    /// and the full view, otherwise None.
    pub buying: Option<BuyingView>,
    /// In the Draft, what they are drafting: only in their own Player View and the full view,
    /// otherwise None.
    pub drafting: Option<DraftingView>,
    /// The cards they have passed on in the Draft this Game, in the order passed: only in their
    /// own Player View and the full view, otherwise None.
    pub passed_in_draft: Option<Vec<DraftPassView>>,
    /// The cards they have played, by catalog id in card-number order.
    pub played_cards: Vec<&'static str>,
    /// How many of each Tag they have in play, for every Tag but the Event Tag, which never counts.
    pub tags: BTreeMap<Tag, i32>,
}

/// The cards dealt to a Player to buy from, and those of them they have bought so far, by
/// catalog id in card-number order. Nothing is paid until every Player is done buying.
#[derive(Serialize)]
pub struct BuyingView {
    pub dealt: Vec<&'static str>,
    pub bought: Vec<&'static str>,
}

/// What a Player is drafting, by catalog id in card-number order: the cards they pick one from
/// now, passing the rest to `passing_to`, and the cards they have kept so far.
#[derive(Serialize)]
pub struct DraftingView {
    pub picking_from: Vec<&'static str>,
    pub kept: Vec<&'static str>,
    pub passing_to: usize,
}

/// Cards a Player passed on in the Draft, by catalog id in card-number order: in `generation`,
/// to Player `to`.
#[derive(Serialize)]
pub struct DraftPassView {
    pub generation: u32,
    pub to: usize,
    pub cards: Vec<&'static str>,
}

/// One Milestone: what it asks for, who claimed it, and how far each Player is towards it.
#[derive(Serialize)]
pub struct MilestoneView {
    /// Its id, such as "terraformer".
    pub milestone: String,
    pub name: &'static str,
    /// What a Player needs to claim it, as printed: "Owning at least 3 Cities".
    pub condition: &'static str,
    /// The count a Player needs to reach: 3 for Mayor.
    pub target: i32,
    pub claimed_by: Option<usize>,
    /// Each Player's count towards it, by Player.
    pub counts: Vec<i32>,
}

/// One Award: what it measures, who funded it, and what each Player has of it.
#[derive(Serialize)]
pub struct AwardView {
    /// Its id, such as "landlord".
    pub award: String,
    pub name: &'static str,
    /// What the leader has most of, as printed: "Owning the most Tiles in play".
    pub condition: &'static str,
    pub funded_by: Option<usize>,
    /// What each Player has of what it measures, by Player.
    pub counts: Vec<i32>,
}

pub fn player_view(game: &Game, viewer: usize) -> View {
    view(game, Some(viewer))
}

/// Everything about the Game, for Hotseat and the dev panel. Until there is hidden
/// information (hands, the deck), it shows the same as every Player View.
pub fn full_view(game: &Game) -> View {
    view(game, None)
}

fn view(game: &Game, viewer: Option<usize>) -> View {
    // Hands, and the cards being bought from, are shown only to their own Player, or to everyone in the full view.
    let sees_hand = |player: usize| viewer.is_none() || viewer == Some(player);
    View {
        viewer,
        generation: game.generation,
        phase: match game.phase {
            Phase::Setup => "setup",
            Phase::Draft => "draft",
            Phase::Research => "research",
            Phase::Action => "action",
            Phase::FinalGreenery => "final_greenery",
            Phase::Over => "over",
        },
        temperature: game.temperature,
        oxygen: game.oxygen,
        oceans: game.board.oceans(),
        board: board_view(&game.board),
        deck_size: game.deck.len(),
        deck: viewer.is_none().then(|| game.deck.iter().map(|card| CARD_CATALOG[card].id.as_str()).collect()),
        discard_size: game.discard.len(),
        discard: viewer.is_none().then(|| ids(game.discard)),
        first_player: game.first_player,
        current_player: if game.is_over() { None } else { Some(game.current_player) },
        actions_this_turn: game.actions_this_turn,
        players: game
            .players
            .iter()
            .enumerate()
            .map(|(index, player)| PlayerBoard {
                name: player_name(index),
                resources: player.resources,
                production: player.production,
                terraform_rating: player.terraform_rating,
                passed: player.passed,
                hand_size: player.hand.len(),
                hand: sees_hand(index).then(|| ids(player.hand)),
                buying: (sees_hand(index) && game.phase.is_buying()).then(|| BuyingView {
                    dealt: ids(player.buying.dealt),
                    bought: ids(player.buying.bought),
                }),
                drafting: (sees_hand(index) && game.phase == Phase::Draft).then(|| DraftingView {
                    picking_from: ids(player.drafting.picking_from),
                    kept: ids(player.drafting.kept),
                    passing_to: game.passing_to(index),
                }),
                passed_in_draft: sees_hand(index).then(|| passed_in_draft(&game.draft_passes, index)),
                played_cards: ids(player.played),
                tags: Tag::COUNTED.into_iter().map(|tag| (tag, game.tags(index, tag))).collect(),
            })
            .collect(),
        milestones: Milestone::ALL
            .into_iter()
            .map(|milestone| MilestoneView {
                milestone: milestone.id(),
                name: milestone.name(),
                condition: milestone.condition(),
                target: milestone.target(),
                claimed_by: game.claimed_milestones[milestone.index()],
                counts: (0..game.players.len()).map(|player| milestone.count(game, player)).collect(),
            })
            .collect(),
        milestone_cost: game.milestone_cost(),
        awards: Award::ALL
            .into_iter()
            .map(|award| AwardView {
                award: award.id(),
                name: award.name(),
                condition: award.condition(),
                funded_by: game.funded_awards[award.index()],
                counts: (0..game.players.len()).map(|player| award.count(game, player)).collect(),
            })
            .collect(),
        award_cost: game.award_cost(),
        scores: game.scores(),
    }
}

/// The cards `player` has passed on in the Draft, in the order passed.
fn passed_in_draft(passes: &[DraftPass], player: usize) -> Vec<DraftPassView> {
    passes
        .iter()
        .filter(|pass| pass.player == player)
        .map(|pass| DraftPassView { generation: pass.generation, to: pass.to, cards: ids(pass.cards) })
        .collect()
}

/// The catalog ids of `cards`.
fn ids(cards: CardSet) -> Vec<&'static str> {
    cards.iter().map(|card| CARD_CATALOG[card].id.as_str()).collect()
}

fn board_view(board: &Board) -> Vec<AreaView> {
    (0..AREA_COUNT)
        .map(|area| {
            let printed = printed(area);
            let row_and_position = row_and_position(area);
            AreaView {
                area: area_id(area),
                name: printed.name,
                row: row_and_position.map(|(row, _)| row + 1),
                position: row_and_position.map(|(_, position)| position + 1),
                reserved: printed.reserved.map(|reservation| reservation.name()),
                bonus: printed.bonus.iter().map(|item| item.name()).collect(),
                tile: board.tile(area).map(|tile| TileView { kind: tile.kind, owner: tile.owner }),
            }
        })
        .collect()
}

pub fn decision(game: &Game) -> Option<DecisionView> {
    game.decision().map(|decision| decision_view(&decision))
}

fn decision_view(decision: &Decision) -> DecisionView {
    DecisionView {
        player: decision.player,
        kind: match decision.kind {
            DecisionKind::Action => "action",
            DecisionKind::Area => "area",
            DecisionKind::Payment => "payment",
            DecisionKind::Production => "production",
            DecisionKind::Draft => "draft",
            DecisionKind::BuyCards => "buy_cards",
            DecisionKind::SellPatents => "sell_patents",
            DecisionKind::FinalGreenery => "final_greenery",
        },
        sequence: decision.sequence,
        options: decision
            .options
            .iter()
            .enumerate()
            .map(|(index, option)| OptionView { index, label: label(option), details: details(option) })
            .collect(),
    }
}

fn label(option: &DecisionOption) -> String {
    match option {
        DecisionOption::PlayCard(card) => {
            let printed_card = &CARD_CATALOG[*card];
            format!(
                "Play {} ({})",
                printed_card.name,
                Resource::MegaCredits.counted(printed_card.project_cost())
            )
        }
        DecisionOption::DraftCard(card) => format!("Keep {}", CARD_CATALOG[*card].name),
        DecisionOption::BuyCard(card) => {
            format!("Buy {} ({})", CARD_CATALOG[*card].name, Resource::MegaCredits.counted(CARD_PRICE))
        }
        DecisionOption::SellCard(card) => {
            format!("Sell {} ({})", CARD_CATALOG[*card].name, Resource::MegaCredits.counted(PATENT_VALUE))
        }
        DecisionOption::Pay { payment, .. } => format!("Pay {}", payment.text()),
        DecisionOption::ChangeProduction { card, change: ProductionChange::Alternative(index) } => {
            production_change(CARD_CATALOG[*card].production_alternative(*index))
        }
        DecisionOption::ChangeProduction { change: ProductionChange::CopyBox(copied), .. } => {
            format!("Copy the production box of {}", CARD_CATALOG[*copied].name)
        }
        DecisionOption::UseStandardProject(StandardProject::SellPatents) => {
            format!("Sell Patents ({} per card)", Resource::MegaCredits.counted(PATENT_VALUE))
        }
        DecisionOption::UseStandardProject(project) => {
            format!("{} ({} MegaCredits)", project.name(), project.cost())
        }
        DecisionOption::ClaimMilestone(milestone) => {
            format!("Claim the {} Milestone ({MILESTONE_COST} MegaCredits)", milestone.name())
        }
        DecisionOption::FundAward { award, cost } => {
            format!("Fund the {} Award ({cost} MegaCredits)", award.name())
        }
        DecisionOption::ConvertPlants => format!("Convert {PLANTS_PER_GREENERY} plants into a Greenery"),
        DecisionOption::ConvertHeat => {
            format!("Convert {HEAT_PER_TEMPERATURE_STEP} heat into a Temperature step")
        }
        DecisionOption::EndTurn => "End Turn".to_string(),
        DecisionOption::Pass => "Pass".to_string(),
        DecisionOption::Done => "Done".to_string(),
        DecisionOption::PlaceTile { placement, area } => {
            format!("Place the {} on {}", placement.tile.name(), area_label(*area))
        }
    }
}

/// A Production change as a label writes it: "Raise energy Production by 2", or "Lower
/// MegaCredit Production by 1 and raise energy Production by 1".
fn production_change(by: Resources) -> String {
    let changes = Resource::ALL.into_iter().filter(|&resource| by[resource] != 0).map(|resource| {
        let verb = if by[resource] < 0 { "lower" } else { "raise" };
        format!("{verb} {} Production by {}", resource.name(), by[resource].abs())
    });
    let text = listed(changes);
    let mut letters = text.chars();
    letters.next().map(|first| first.to_uppercase().chain(letters).collect()).unwrap_or_default()
}

fn details(option: &DecisionOption) -> OptionDetails {
    match option {
        DecisionOption::PlayCard(card) => {
            let printed_card = &CARD_CATALOG[*card];
            OptionDetails::PlayCard { card: &printed_card.id, cost: printed_card.project_cost() }
        }
        DecisionOption::DraftCard(card) => OptionDetails::DraftCard { card: &CARD_CATALOG[*card].id },
        DecisionOption::BuyCard(card) => {
            OptionDetails::BuyCard { card: &CARD_CATALOG[*card].id, cost: CARD_PRICE }
        }
        DecisionOption::SellCard(card) => {
            OptionDetails::SellCard { card: &CARD_CATALOG[*card].id, megacredits: PATENT_VALUE }
        }
        DecisionOption::Pay { card, payment } => {
            OptionDetails::Payment { card: &CARD_CATALOG[*card].id, payment: *payment }
        }
        DecisionOption::ChangeProduction { card, change: ProductionChange::Alternative(index) } => {
            let printed_card = &CARD_CATALOG[*card];
            let production = printed_card.production_alternative(*index);
            OptionDetails::ChooseProduction { card: &printed_card.id, production }
        }
        DecisionOption::ChangeProduction { change: ProductionChange::CopyBox(copied), .. } => {
            OptionDetails::CopyProductionBox { card: &CARD_CATALOG[*copied].id }
        }
        DecisionOption::UseStandardProject(project) => {
            OptionDetails::StandardProject { project: project.id(), cost: project.cost() }
        }
        DecisionOption::ClaimMilestone(milestone) => {
            OptionDetails::ClaimMilestone { milestone: milestone.id(), cost: MILESTONE_COST }
        }
        DecisionOption::FundAward { award, cost } => {
            OptionDetails::FundAward { award: award.id(), cost: *cost }
        }
        DecisionOption::ConvertPlants => OptionDetails::ConvertPlants { plants: PLANTS_PER_GREENERY },
        DecisionOption::ConvertHeat => OptionDetails::ConvertHeat { heat: HEAT_PER_TEMPERATURE_STEP },
        DecisionOption::EndTurn => OptionDetails::EndTurn,
        DecisionOption::Pass => OptionDetails::Pass,
        DecisionOption::Done => OptionDetails::Done,
        DecisionOption::PlaceTile { placement, area } => {
            OptionDetails::Area { area: area_id(*area), tile: placement.tile, on: placement.on }
        }
    }
}
