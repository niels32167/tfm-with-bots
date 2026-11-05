//! What crosses into Python: the current Decision and the Player View, as plain
//! JSON-shaped values. Every Option gets a readable label for people and structured
//! details for programs (the GUI, and later the AI).

use std::collections::BTreeMap;

use serde::Serialize;

use crate::board::{
    AREA_COUNT, Areas, Board, SpecialTile, TileKind, area_id, area_label, printed, row_and_position,
};
use crate::card_code::{OLYMPUS_CONFERENCE, insulation_change};
use crate::card_flow::{CARD_PRICE, PATENT_VALUE};
use crate::card_set::CardSet;
use crate::cards::{CARD_CATALOG, CardResource, Tag};
use crate::draft::DraftPass;
use crate::game::{
    Decision, DecisionKind, DecisionOption, Game, HEAT_PER_TEMPERATURE_STEP, PLANTS_PER_GREENERY, Phase,
    StandardProject, Waiting,
};
use crate::log::{listed, player_name};
use crate::milestones_and_awards::{Award, MILESTONE_COST, Milestone};
use crate::playing_cards::{Payment, ProductionChange};
use crate::resources::{Resource, Resources};
use crate::scoring::Score;
use crate::targets::{Taking, steals};

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
    /// Use the action of a played card, named by its catalog id.
    UseAction {
        card: &'static str,
    },
    /// Keep one of the cards being drafted, named by its catalog id, and pass the rest on.
    DraftCard {
        card: &'static str,
    },
    /// Keep one of the cards the card being played lets its Player look at, named by its catalog
    /// id.
    KeepCard {
        card: &'static str,
    },
    /// Buy one of the cards dealt, or one of those the action being used lets its Player look at,
    /// named by its catalog id.
    BuyCard {
        card: &'static str,
        cost: i32,
    },
    /// Discard a card from the hand, named by its catalog id, to draw one (Mars University).
    DiscardCard {
        card: &'static str,
    },
    /// Lower `player`'s Production, the deciding Player's own or an opponent's, `production` steps
    /// (below zero) with `card`, which lowers any Player's.
    LowerProduction {
        card: &'static str,
        player: usize,
        production: Resources,
    },
    /// Remove `resources` (below zero) from `player` with `card`, which may remove any Player's
    /// Resources, and gain them if `stolen`.
    RemoveResources {
        card: &'static str,
        player: usize,
        resources: Resources,
        #[serde(skip_serializing_if = "std::ops::Not::not")]
        stolen: bool,
    },
    /// Move 1 Card Resource from the card `from`, of `player`'s, to `card`, whose action moves it.
    MoveCardResource {
        card: &'static str,
        player: usize,
        from: &'static str,
        kind: CardResource,
    },
    /// Remove `amount` Card Resources from the card `from`, of `player`'s, with `card` (Virus).
    RemoveCardResources {
        card: &'static str,
        player: usize,
        from: &'static str,
        kind: CardResource,
        amount: i32,
    },
    /// Remove, or steal, nothing with `card`.
    RemoveNothing {
        card: &'static str,
    },
    /// Remove a science from Olympus Conference to draw a card (`draw`), or add one to it.
    OlympusConference {
        card: &'static str,
        draw: bool,
    },
    /// Add 1 Card Resource to `card`, which is being played (`add`), or gain 1 plant (Viral Enhancers).
    ViralEnhancers {
        card: &'static str,
        add: bool,
    },
    /// Sell a card from the hand with Sell Patents, named by its catalog id, for `megacredits`.
    SellCard {
        card: &'static str,
        megacredits: i32,
    },
    /// One way to pay for the card being played, or for the action of `card` being used if
    /// `action` is true: its MegaCredits, steel and titanium.
    Payment {
        card: &'static str,
        #[serde(skip_serializing_if = "std::ops::Not::not")]
        action: bool,
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
    /// One of the Resource changes the action of `card`, being used, lets its Player choose.
    ChooseResources {
        card: &'static str,
        resources: Resources,
    },
    /// One of the alternatives `card`, being played, or its action, being used, lets its Player
    /// choose: the one at `alternative` in its effect data's `"choice"`.
    ChooseEffects {
        card: &'static str,
        alternative: usize,
    },
    /// One of the Player's cards to get `amount` Card Resources of the kind it holds, with `card`.
    AddCardResources {
        card: &'static str,
        to: &'static str,
        kind: CardResource,
        amount: i32,
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
        /// For a special Tile, the card whose symbol it is printed with.
        #[serde(skip_serializing_if = "Option::is_none")]
        card: Option<SpecialTile>,
    },
    /// An Area to claim with Land Claim.
    ClaimArea {
        area: String,
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
    /// The Player who claimed it with Land Claim, if anyone has: only they may place a Tile there.
    pub claimed_by: Option<usize>,
}

#[derive(Serialize)]
pub struct TileView {
    #[serde(rename = "type")]
    pub kind: TileKind,
    /// The owning Player, or None for an Ocean.
    pub owner: Option<usize>,
    /// For a special Tile, the card whose symbol it is printed with, by catalog id.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub card: Option<SpecialTile>,
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
    /// What they would pay now for each card in their hand, by catalog id, once their discounts
    /// are taken off: only with their hand, otherwise None.
    pub card_costs: Option<BTreeMap<&'static str, i32>>,
    /// In the setup or a Research phase, what they are buying from: only in their own Player View
    /// and the full view, otherwise None.
    pub buying: Option<BuyingView>,
    /// In the Draft, what they are drafting: only in their own Player View and the full view,
    /// otherwise None.
    pub drafting: Option<DraftingView>,
    /// The cards they have passed on in the Draft this Game, in the order passed: only in their
    /// own Player View and the full view, otherwise None.
    pub passed_in_draft: Option<Vec<DraftPassView>>,
    /// While they play a card that lets them look at cards to keep some of them, those cards:
    /// only in their own Player View and the full view, otherwise None.
    pub keeping: Option<KeepingView>,
    /// The cards they have played, by catalog id in card-number order.
    pub played_cards: Vec<&'static str>,
    /// The played cards whose action they have used this Generation, by catalog id in card-number
    /// order.
    pub used_actions: Vec<&'static str>,
    /// How many Card Resources are on each of their played cards that can hold some, by catalog id.
    pub card_resources: BTreeMap<&'static str, i32>,
    /// The Event they played whose effect waits on the next card they play this Generation
    /// (Indentured Workers, Special Design), by catalog id, or None.
    pub next_card: Option<&'static str>,
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

/// The cards a Player looks at while playing `card` or using its action, by catalog id in
/// card-number order: those they may still keep, those they have kept, and how many more they
/// `keep`. The rest are discarded. With a `price`, the MegaCredits each costs, they buy up to
/// `keep` more instead.
#[derive(Serialize)]
pub struct KeepingView {
    pub card: &'static str,
    pub looking_at: Vec<&'static str>,
    pub kept: Vec<&'static str>,
    pub keep: usize,
    pub price: i32,
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
                card_costs: sees_hand(index).then(|| {
                    player
                        .hand
                        .iter()
                        .map(|card| (CARD_CATALOG[card].id.as_str(), game.card_cost(index, card)))
                        .collect()
                }),
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
                keeping: match game.waiting {
                    Some(Waiting::KeepCards(keeping)) if sees_hand(index) && index == game.current_player => {
                        Some(KeepingView {
                            card: &CARD_CATALOG[keeping.card].id,
                            looking_at: ids(keeping.looking_at),
                            kept: ids(keeping.kept),
                            keep: keeping.keep,
                            price: keeping.price,
                        })
                    }
                    _ => None,
                },
                played_cards: ids(player.played),
                used_actions: ids(player.used_actions),
                card_resources: player
                    .cards_holding_card_resources()
                    .iter()
                    .map(|card| (CARD_CATALOG[card].id.as_str(), game.card_resources.on(card)))
                    .collect(),
                next_card: player.next_card.map(|card| CARD_CATALOG[card].id.as_str()),
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
                tile: board.tile(area).map(|tile| TileView {
                    kind: tile.kind,
                    owner: tile.owner,
                    card: tile.special,
                }),
                claimed_by: board.claim().filter(|claim| claim.area == area).map(|claim| claim.player),
            }
        })
        .collect()
}

pub fn decision(game: &Game) -> Option<DecisionView> {
    game.decision().map(|decision| decision_view(game, &decision))
}

fn decision_view(game: &Game, decision: &Decision) -> DecisionView {
    DecisionView {
        player: decision.player,
        kind: match decision.kind {
            DecisionKind::Action => "action",
            DecisionKind::Area => "area",
            DecisionKind::Payment => "payment",
            DecisionKind::Production => "production",
            DecisionKind::KeepCards => "keep_cards",
            DecisionKind::Resources => "resources",
            DecisionKind::Effects => "effects",
            DecisionKind::AddToCard => "add_to_card",
            DecisionKind::Draft => "draft",
            DecisionKind::BuyCards => "buy_cards",
            DecisionKind::SellPatents => "sell_patents",
            DecisionKind::DiscardToDraw => "discard_to_draw",
            DecisionKind::OlympusConference => "olympus_conference",
            DecisionKind::ViralEnhancers => "viral_enhancers",
            DecisionKind::Target => "target",
            DecisionKind::FinalGreenery => "final_greenery",
        },
        sequence: decision.sequence,
        options: decision
            .options
            .iter()
            .enumerate()
            .map(|(index, option)| OptionView {
                index,
                label: label(game, decision.player, option),
                details: details(game, decision.player, option),
            })
            .collect(),
    }
}

/// An Option's label, for `player`, who is deciding.
fn label(game: &Game, player: usize, option: &DecisionOption) -> String {
    let cost = |card: usize| game.card_cost(player, card);
    match option {
        DecisionOption::PlayCard(card) => {
            format!("Play {} ({})", CARD_CATALOG[*card].name, Resource::MegaCredits.counted(cost(*card)))
        }
        DecisionOption::UseAction(card) => format!("Use the action of {}", CARD_CATALOG[*card].name),
        DecisionOption::DraftCard(card) | DecisionOption::KeepCard(card) => {
            format!("Keep {}", CARD_CATALOG[*card].name)
        }
        DecisionOption::BuyCard(card) => {
            format!("Buy {} ({})", CARD_CATALOG[*card].name, Resource::MegaCredits.counted(CARD_PRICE))
        }
        DecisionOption::SellCard(card) => {
            format!("Sell {} ({})", CARD_CATALOG[*card].name, Resource::MegaCredits.counted(PATENT_VALUE))
        }
        DecisionOption::DiscardCard(card) => format!("Discard {} to draw a card", CARD_CATALOG[*card].name),
        DecisionOption::OlympusConference { draw: false } => {
            format!("Add 1 science to {}", CARD_CATALOG[OLYMPUS_CONFERENCE].name)
        }
        DecisionOption::OlympusConference { draw: true } => {
            format!("Remove 1 science from {} to draw a card", CARD_CATALOG[OLYMPUS_CONFERENCE].name)
        }
        DecisionOption::ViralEnhancers { card, add: true } => {
            let printed = &CARD_CATALOG[*card];
            format!("Add {} to {}", printed.held().counted(1), printed.name)
        }
        DecisionOption::ViralEnhancers { add: false, .. } => {
            format!("Gain {}", Resource::Plants.counted(1))
        }
        DecisionOption::Target { card, player: target, alternative } => {
            taking_label(game.taking(*card, *target, *alternative), *target == player, *target)
        }
        DecisionOption::MoveCardResource { owner, from, .. } => {
            let whose =
                if *owner == player { "your own".to_string() } else { format!("{}'s", player_name(*owner)) };
            format!(
                "Remove {} from {whose} {}",
                CARD_CATALOG[*from].held().counted(1),
                CARD_CATALOG[*from].name
            )
        }
        DecisionOption::RemoveFromCard { owner, from, amount, .. } => {
            let printed = &CARD_CATALOG[*from];
            format!(
                "Remove {} from {}'s {}",
                printed.held().counted(*amount),
                player_name(*owner),
                printed.name
            )
        }
        DecisionOption::RemoveNothing(card) => {
            if steals(*card) {
                "Steal nothing".to_string()
            } else {
                "Remove nothing".to_string()
            }
        }
        DecisionOption::Pay { payment, .. } | DecisionOption::PayForAction { payment, .. } => {
            format!("Pay {}", payment.text())
        }
        DecisionOption::ChangeResources { card, change } => resource_change(change.resources(*card)),
        DecisionOption::ChooseEffects { card, alternative } => alternative_label(*card, *alternative),
        DecisionOption::AddToCard { to, amount, .. } => {
            let printed = &CARD_CATALOG[*to];
            format!("Add {} to {}", printed.held().counted(*amount), printed.name)
        }
        DecisionOption::ChangeProduction { card, change: ProductionChange::Alternative(index) } => {
            production_change(CARD_CATALOG[*card].production_alternative(*index))
        }
        DecisionOption::ChangeProduction { change: ProductionChange::CopyBox(copied), .. } => {
            format!("Copy the production box of {}", CARD_CATALOG[*copied].name)
        }
        DecisionOption::ChangeProduction { change: ProductionChange::HeatForMegaCredits(steps), .. } => {
            production_change(insulation_change(*steps))
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
        // Next to Olympus Conference's Options, being done is about Mars University's discard.
        DecisionOption::Done if matches!(game.waiting, Some(Waiting::OlympusConference)) => {
            "Keep the hand".to_string()
        }
        DecisionOption::Done => "Done".to_string(),
        DecisionOption::PlaceTile { placement, area } => {
            format!("Place {} on {}", placement.tile_name(), area_label(*area))
        }
        DecisionOption::ClaimArea(area) => format!("Claim {}", area_label(*area)),
    }
}

/// A Production change as a label writes it: "Raise energy Production by 2", or "Lower
/// MegaCredit Production by 1 and raise energy Production by 1".
fn production_change(by: Resources) -> String {
    let changes = Resource::ALL.into_iter().filter(|&resource| by[resource] != 0).map(|resource| {
        let verb = if by[resource] < 0 { "lower" } else { "raise" };
        format!("{verb} {} Production by {}", resource.name(), by[resource].abs())
    });
    capitalized(listed(changes))
}

fn capitalized(text: String) -> String {
    let mut letters = text.chars();
    letters.next().map(|first| first.to_uppercase().chain(letters).collect()).unwrap_or_default()
}

/// A card's or an action's alternative as a label writes it: "Add 1 microbe to Regolith Eaters",
/// "Remove 2 microbes from Regolith Eaters to raise Oxygen 1 step", "Gain 1 plant" or "Add 2 microbes to
/// another card".
fn alternative_label(card: usize, alternative: usize) -> String {
    let printed = &CARD_CATALOG[card];
    let effects = &printed.alternatives()[alternative];
    let amount = |by: i32| printed.holds().map_or(String::new(), |held| held.counted(by.abs()));
    let mut gains: Vec<String> = Resource::ALL
        .into_iter()
        .filter(|&resource| effects.resources[resource] > 0)
        .map(|resource| format!("gain {}", resource.counted(effects.resources[resource])))
        .collect();
    for add in &effects.add_to_another {
        gains.push(format!("add {} to another card", add.amount_text()));
    }
    for (steps, what) in [
        (effects.oxygen, "Oxygen"),
        (effects.temperature, "Temperature"),
        (effects.terraform_rating, "your Terraform Rating"),
    ] {
        if steps > 0 {
            gains.push(format!("raise {what} {steps} step"));
        }
    }
    let gained = listed(gains.into_iter());
    capitalized(match effects.card_resources {
        by if by > 0 => format!("add {} to {}", amount(by), printed.name),
        by if by < 0 => format!("remove {} from {} to {gained}", amount(by), printed.name),
        _ => gained,
    })
}

/// A taking as a label writes it: "Lower Player 2's heat Production by 2", "Lower your own heat
/// Production by 2", "Remove 3 plants from Player 2" or "Steal 2 steel from Player 2".
fn taking_label(taking: Taking, own: bool, target: usize) -> String {
    match taking {
        Taking::Production(by) => {
            let whose = if own { "your own".to_string() } else { format!("{}'s", player_name(target)) };
            let changes = Resource::ALL.into_iter().filter(|&resource| by[resource] != 0);
            let steps = listed(
                changes.map(|resource| format!("{} Production by {}", resource.name(), -by[resource])),
            );
            format!("Lower {whose} {steps}")
        }
        Taking::Resources { resources, stolen } => {
            let taken = Resource::ALL.into_iter().filter(|&resource| resources[resource] != 0);
            let amounts = listed(taken.map(|resource| resource.counted(-resources[resource])));
            format!("{} {amounts} from {}", if stolen { "Steal" } else { "Remove" }, player_name(target))
        }
    }
}

/// A Resource change as a label writes it: "Spend 1 plant to gain 7 MegaCredits".
fn resource_change(by: Resources) -> String {
    let amounts = |spent: bool| {
        let changed =
            Resource::ALL.into_iter().filter(|&resource| by[resource] != 0 && (by[resource] < 0) == spent);
        listed(changed.map(|resource| resource.counted(by[resource].abs())))
    };
    format!("Spend {} to gain {}", amounts(true), amounts(false))
}

/// An Option's details, for `player`, who is deciding.
fn details(game: &Game, player: usize, option: &DecisionOption) -> OptionDetails {
    let cost = |card: usize| game.card_cost(player, card);
    match option {
        DecisionOption::PlayCard(card) => {
            OptionDetails::PlayCard { card: &CARD_CATALOG[*card].id, cost: cost(*card) }
        }
        DecisionOption::UseAction(card) => OptionDetails::UseAction { card: &CARD_CATALOG[*card].id },
        DecisionOption::DraftCard(card) => OptionDetails::DraftCard { card: &CARD_CATALOG[*card].id },
        DecisionOption::KeepCard(card) => OptionDetails::KeepCard { card: &CARD_CATALOG[*card].id },
        DecisionOption::BuyCard(card) => {
            OptionDetails::BuyCard { card: &CARD_CATALOG[*card].id, cost: CARD_PRICE }
        }
        DecisionOption::SellCard(card) => {
            OptionDetails::SellCard { card: &CARD_CATALOG[*card].id, megacredits: PATENT_VALUE }
        }
        DecisionOption::DiscardCard(card) => OptionDetails::DiscardCard { card: &CARD_CATALOG[*card].id },
        DecisionOption::OlympusConference { draw } => {
            OptionDetails::OlympusConference { card: &CARD_CATALOG[OLYMPUS_CONFERENCE].id, draw: *draw }
        }
        DecisionOption::ViralEnhancers { card, add } => {
            OptionDetails::ViralEnhancers { card: &CARD_CATALOG[*card].id, add: *add }
        }
        DecisionOption::Target { card, player: target, alternative } => {
            let id = &CARD_CATALOG[*card].id;
            match game.taking(*card, *target, *alternative) {
                Taking::Production(production) => {
                    OptionDetails::LowerProduction { card: id, player: *target, production }
                }
                Taking::Resources { resources, stolen } => {
                    OptionDetails::RemoveResources { card: id, player: *target, resources, stolen }
                }
            }
        }
        DecisionOption::MoveCardResource { card, owner, from } => OptionDetails::MoveCardResource {
            card: &CARD_CATALOG[*card].id,
            player: *owner,
            from: &CARD_CATALOG[*from].id,
            kind: CARD_CATALOG[*from].held(),
        },
        DecisionOption::RemoveFromCard { card, owner, from, amount } => OptionDetails::RemoveCardResources {
            card: &CARD_CATALOG[*card].id,
            player: *owner,
            from: &CARD_CATALOG[*from].id,
            kind: CARD_CATALOG[*from].held(),
            amount: *amount,
        },
        DecisionOption::RemoveNothing(card) => OptionDetails::RemoveNothing { card: &CARD_CATALOG[*card].id },
        DecisionOption::Pay { card, payment } => {
            OptionDetails::Payment { card: &CARD_CATALOG[*card].id, action: false, payment: *payment }
        }
        DecisionOption::PayForAction { card, payment } => {
            OptionDetails::Payment { card: &CARD_CATALOG[*card].id, action: true, payment: *payment }
        }
        DecisionOption::ChangeResources { card, change } => OptionDetails::ChooseResources {
            card: &CARD_CATALOG[*card].id,
            resources: change.resources(*card),
        },
        DecisionOption::ChangeProduction { card, change: ProductionChange::Alternative(index) } => {
            let printed_card = &CARD_CATALOG[*card];
            let production = printed_card.production_alternative(*index);
            OptionDetails::ChooseProduction { card: &printed_card.id, production }
        }
        DecisionOption::ChangeProduction { change: ProductionChange::CopyBox(copied), .. } => {
            OptionDetails::CopyProductionBox { card: &CARD_CATALOG[*copied].id }
        }
        DecisionOption::ChangeProduction { card, change: ProductionChange::HeatForMegaCredits(steps) } => {
            OptionDetails::ChooseProduction {
                card: &CARD_CATALOG[*card].id,
                production: insulation_change(*steps),
            }
        }
        DecisionOption::ChooseEffects { card, alternative } => {
            OptionDetails::ChooseEffects { card: &CARD_CATALOG[*card].id, alternative: *alternative }
        }
        DecisionOption::AddToCard { card, to, amount } => OptionDetails::AddCardResources {
            card: &CARD_CATALOG[*card].id,
            to: &CARD_CATALOG[*to].id,
            kind: CARD_CATALOG[*to].held(),
            amount: *amount,
        },
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
        DecisionOption::PlaceTile { placement, area } => OptionDetails::Area {
            area: area_id(*area),
            tile: placement.tile,
            on: placement.on,
            card: placement.special,
        },
        DecisionOption::ClaimArea(area) => OptionDetails::ClaimArea { area: area_id(*area) },
    }
}
