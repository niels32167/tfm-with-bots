//! The game log. The Game records small events as it goes, and they are turned into
//! plain-language lines only when someone reads the log. Events are plain values,
//! so the log adds little to the cost of copying a Game.

use crate::board::{BonusItem, Placement, area_label};
use crate::card_flow::{CARD_PRICE, PATENT_VALUE, RESEARCH_CARDS, SETUP_CARDS};
use crate::cards::{AddToAnother, CARD_CATALOG, Tag};
use crate::corporations::CORPORATIONS_DEALT;
use crate::game::{
    HEAT_PER_TEMPERATURE_STEP, MAX_OCEANS, OCEAN_ADJACENCY_BONUS, OCEAN_BONUS_TEMPERATURE, StandardProject,
    TEMPERATURE_BONUS_OXYGEN,
};
use crate::milestones_and_awards::{Award, MILESTONE_COST, Milestone};
use crate::playing_cards::Payment;
use crate::prelude_cards::{
    MEGACREDITS_FOR_AN_UNPLAYABLE_PRELUDE_CARD, PRELUDE_CARDS_DEALT, PRELUDE_CARDS_KEPT,
};
use crate::resources::{Resource, Resources};
use crate::scoring::{AwardPlace, Win};

#[derive(Clone, Copy, Debug)]
pub enum LogEvent {
    Setup,
    CorporationsDealt,
    PreludeCardsDealt,
    /// `player` draws `count` Prelude Cards from the Prelude deck, hidden from the others (Valley Trust).
    DrewPreludeCards {
        player: usize,
        count: usize,
    },
    /// After setup, Players play their Prelude Cards.
    PreludeCardsPlayed,
    PlayedPreludeCard {
        player: usize,
        card: usize,
    },
    /// The Player reveals this card from the top of the deck, and takes it into their hand for having
    /// `taken_for`, the Tag they are revealing cards until they find, or else discards it.
    RevealedLookingForTag {
        player: usize,
        card: usize,
        taken_for: Option<Tag>,
    },
    /// The Player pays the price of this Prelude Card of theirs ("Pay 6 M€").
    PaidForPreludeCard {
        player: usize,
        card: usize,
        payment: Payment,
    },
    /// The Player can't play this Prelude Card of theirs, so they discard it and gain 15 MegaCredits.
    DiscardedUnplayablePreludeCard {
        player: usize,
        card: usize,
    },
    /// The Player takes the first action of their Corporation.
    TookFirstAction {
        player: usize,
        card: usize,
    },
    /// The Player reveals the Corporation they chose at setup.
    RevealedCorporation {
        player: usize,
        card: usize,
    },
    GenerationBegins {
        generation: u32,
        first_player: usize,
    },
    ResearchPhase,
    /// The Research phase begins with the Draft, among `players` Players, passing clockwise or not.
    ResearchPhaseWithDraft {
        players: usize,
        clockwise: bool,
    },
    DraftIsOver,
    /// A Player bought `bought` of the `dealt` cards dealt to them.
    BoughtCards {
        player: usize,
        bought: usize,
        dealt: usize,
    },
    PlayedCard {
        player: usize,
        card: usize,
        payment: Payment,
    },
    UsedStandardProject {
        player: usize,
        project: StandardProject,
        cost: i32,
    },
    /// The Player paid `heat` of what they just paid for with heat (Helion).
    PaidWithHeat {
        player: usize,
        heat: i32,
    },
    /// The Player uses the action of `card`.
    UsedAction {
        player: usize,
        card: usize,
    },
    /// The Player pays for the action they are using.
    PaidForAction {
        player: usize,
        payment: Payment,
    },
    ClaimedMilestone {
        player: usize,
        milestone: Milestone,
    },
    FundedAward {
        player: usize,
        award: Award,
        cost: i32,
    },
    TemperatureRaised {
        player: usize,
        temperature: i32,
    },
    ConvertedPlants {
        player: usize,
        plants: i32,
    },
    ConvertedHeat {
        player: usize,
    },
    ProductionChanged {
        player: usize,
        resource: Resource,
        by: i32,
    },
    ResourceChanged {
        player: usize,
        resource: Resource,
        by: i32,
    },
    TerraformRatingRaised {
        player: usize,
        by: i32,
    },
    DrewCards {
        player: usize,
        count: i32,
    },
    /// The Player looks at the top `cards` cards of the deck to keep some of them.
    LookedAtCards {
        player: usize,
        cards: usize,
    },
    /// The Player keeps `kept` of the cards they looked at, or buys them at `price` each, and
    /// discards the rest.
    KeptCards {
        player: usize,
        kept: usize,
        discarded: usize,
        price: i32,
    },
    /// The effect of `card`, one of `player`'s played cards, is set off.
    TriggerTakesEffect {
        player: usize,
        card: usize,
    },
    /// The Player discards a card face down to draw one (Mars University).
    DiscardedToDraw {
        player: usize,
    },
    /// Robotic Workforce copies the production box of `card`.
    CopiedProductionBox {
        player: usize,
        card: usize,
    },
    /// `player` reveals `card` from the top of the deck and discards it (Search for Life).
    RevealedCard {
        player: usize,
        card: usize,
    },
    /// `player` adds Card Resources to `card`, or removes them below zero.
    CardResourcesChanged {
        player: usize,
        card: usize,
        by: i32,
    },
    /// `player` has no card for the Card Resources `add` adds, so they are lost.
    NoCardToAddTo {
        player: usize,
        add: AddToAnother,
    },
    /// `player` moves 1 Card Resource from `from`, a card of `owner`'s, to `card`.
    MovedCardResource {
        player: usize,
        owner: usize,
        from: usize,
        card: usize,
    },
    /// `player` removes `amount` Card Resources from `from`, a card of `owner`'s.
    RemovedFromCard {
        player: usize,
        owner: usize,
        from: usize,
        amount: i32,
    },
    /// `player` lowers `target`'s Production of `resource` `by` steps with a card that lowers any
    /// Player's; `target` may be `player` themselves.
    LoweredProductionOf {
        player: usize,
        target: usize,
        resource: Resource,
        by: i32,
    },
    /// `player` removes `amount` of `resource` from `target`, and gains it if `stolen`.
    RemovedResources {
        player: usize,
        target: usize,
        resource: Resource,
        amount: i32,
        stolen: bool,
    },
    /// `player` removes, or steals, nothing with `card`.
    RemovedNothing {
        player: usize,
        card: usize,
        stolen: bool,
    },
    SoldPatents {
        player: usize,
        cards: usize,
    },
    DiscardPileReshuffled {
        cards: usize,
    },
    DeckAndDiscardPileEmpty {
        player: usize,
    },
    TemperatureAlreadyAtMaximum,
    HeatProductionBonus {
        player: usize,
        temperature: i32,
    },
    OceanBonus {
        player: usize,
    },
    TemperatureBonus {
        player: usize,
    },
    OxygenRaised {
        player: usize,
        oxygen: i32,
    },
    OxygenAlreadyAtMaximum,
    PlacedTile {
        player: usize,
        placement: Placement,
        area: usize,
    },
    ClaimedArea {
        player: usize,
        area: usize,
    },
    OceansRaised {
        player: usize,
        oceans: usize,
    },
    OceansAlreadyAtMaximum,
    PlacementBonus {
        player: usize,
        item: BonusItem,
        amount: i32,
    },
    CollectsWaitingBonus {
        player: usize,
        area: usize,
    },
    AdjacentOceans {
        player: usize,
        oceans: usize,
    },
    EndedTurn {
        player: usize,
    },
    Passed {
        player: usize,
    },
    ProductionPhase,
    EnergyTurnsIntoHeat {
        player: usize,
        energy: i32,
    },
    Produced {
        player: usize,
        terraform_rating: i32,
        production: Resources,
    },
    MarsIsTerraformed,
    FinalGreeneryConversion {
        first_player: usize,
    },
    DoneConvertingPlants {
        player: usize,
    },
    GameOver,
    AwardPlace(AwardPlace),
    FinalScore {
        player: usize,
        victory_points: i32,
    },
    Won {
        player: usize,
        win: Win,
    },
}

impl LogEvent {
    pub fn text(&self) -> String {
        match *self {
            LogEvent::Setup => format!(
                "Setup: each Player is dealt {SETUP_CARDS} Project Cards and may buy any of them for \
                 {CARD_PRICE} MegaCredits each."
            ),
            LogEvent::CorporationsDealt => format!(
                "Each Player is dealt {CORPORATIONS_DEALT} Corporations and chooses one, which stays hidden until \
                 every Player is done buying."
            ),
            LogEvent::DrewPreludeCards { player, count } => {
                let cards = counted(count as i32, "Prelude Card", "Prelude Cards");
                format!("{} draws {cards}.", player_name(player))
            }
            LogEvent::PreludeCardsDealt => format!(
                "Each Player is dealt {PRELUDE_CARDS_DEALT} Prelude Cards and keeps {PRELUDE_CARDS_KEPT}, which stay \
                 hidden until they are played."
            ),
            LogEvent::PreludeCardsPlayed => {
                "Each Player, in player order, plays the Prelude Cards they kept.".to_string()
            }
            LogEvent::PlayedPreludeCard { player, card } => {
                format!("{} plays {}.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::RevealedLookingForTag { player, card, taken_for: Some(tag) } => format!(
                "{} reveals {}, which has a{} {} Tag, and takes it into their hand.",
                player_name(player),
                CARD_CATALOG[card].name,
                if tag.name().starts_with(['a', 'e', 'i', 'o', 'u']) { "n" } else { "" },
                tag.name()
            ),
            LogEvent::RevealedLookingForTag { player, card, taken_for: None } => {
                format!("{} reveals {} and discards it.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::PaidForPreludeCard { player, card, payment } => {
                format!("{} pays {} for {}.", player_name(player), payment.text(), CARD_CATALOG[card].name)
            }
            LogEvent::DiscardedUnplayablePreludeCard { player, card } => format!(
                "{} can't play {}, so they discard it and gain {MEGACREDITS_FOR_AN_UNPLAYABLE_PRELUDE_CARD} MegaCredits.",
                player_name(player),
                CARD_CATALOG[card].name
            ),
            LogEvent::TookFirstAction { player, card } => {
                format!("{} takes the first action of {}.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::RevealedCorporation { player, card } => {
                format!("{} reveals {}.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::GenerationBegins { generation, first_player } => {
                format!("Generation {generation} begins, with {} as first player.", player_name(first_player))
            }
            LogEvent::ResearchPhase => format!(
                "Research phase: each Player draws {RESEARCH_CARDS} cards and may buy any of them for \
                 {CARD_PRICE} MegaCredits each."
            ),
            LogEvent::ResearchPhaseWithDraft { players, clockwise } => {
                let passing = match (players, clockwise) {
                    (2, _) => "to the other Player",
                    (_, true) => "clockwise, to the next Player",
                    (_, false) => "counter-clockwise, to the Player before them",
                };
                format!(
                    "Research phase, with the Draft: each Player is dealt {RESEARCH_CARDS} cards, keeps one and \
                     passes the rest {passing}, until every card is kept. Then they may buy any of the cards \
                     they kept for {CARD_PRICE} MegaCredits each."
                )
            }
            LogEvent::DraftIsOver => "The Draft is over.".to_string(),
            LogEvent::BoughtCards { player, bought, dealt } => {
                let price = Resource::MegaCredits.counted(CARD_PRICE * bought as i32);
                match bought {
                    0 => format!("{} buys none of their {dealt} cards.", player_name(player)),
                    _ if bought == dealt => {
                        format!("{} buys all {dealt} of their cards for {price}.", player_name(player))
                    }
                    _ => format!("{} buys {bought} of their {dealt} cards for {price}.", player_name(player)),
                }
            }
            LogEvent::PlayedCard { player, card, payment } => {
                format!(
                    "{} plays {}, paying {}.",
                    player_name(player),
                    CARD_CATALOG[card].name,
                    payment.text()
                )
            }
            LogEvent::UsedAction { player, card } => {
                format!("{} uses the action of {}.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::PaidForAction { player, payment } => {
                format!("{} pays {}.", player_name(player), payment.text())
            }
            LogEvent::UsedStandardProject { player, project, cost } => format!(
                "{} uses the {} Standard Project for {cost} MegaCredits.",
                player_name(player),
                project.name()
            ),
            LogEvent::PaidWithHeat { player, heat } => {
                format!("{} pays {heat} of it with heat.", player_name(player))
            }
            LogEvent::ClaimedMilestone { player, milestone } => format!(
                "{} claims the {} Milestone for {MILESTONE_COST} MegaCredits.",
                player_name(player),
                milestone.name()
            ),
            LogEvent::FundedAward { player, award, cost } => {
                format!("{} funds the {} Award for {cost} MegaCredits.", player_name(player), award.name())
            }
            LogEvent::TemperatureRaised { player, temperature } => format!(
                "{} raises Temperature to {temperature} °C and gains 1 Terraform Rating.",
                player_name(player)
            ),
            LogEvent::TemperatureAlreadyAtMaximum => {
                "Temperature is already at its maximum, so it does not rise.".to_string()
            }
            LogEvent::HeatProductionBonus { player, temperature } => {
                format!("Reaching {temperature} °C raises {}'s heat Production by 1.", player_name(player))
            }
            LogEvent::OceanBonus { player } => {
                format!(
                    "Reaching {OCEAN_BONUS_TEMPERATURE} °C gives {} an Ocean to place.",
                    player_name(player)
                )
            }
            LogEvent::TemperatureBonus { player } => format!(
                "Reaching {TEMPERATURE_BONUS_OXYGEN} % Oxygen gives {} a Temperature step.",
                player_name(player)
            ),
            LogEvent::ProductionChanged { player, resource, by } => format!(
                "{} {} their {} Production by {}.",
                player_name(player),
                if by < 0 { "lowers" } else { "raises" },
                resource.name(),
                by.abs()
            ),
            LogEvent::ResourceChanged { player, resource, by } => format!(
                "{} {} {}.",
                player_name(player),
                if by < 0 { "loses" } else { "gains" },
                resource.counted(by.abs())
            ),
            LogEvent::TerraformRatingRaised { player, by } => {
                format!("{} raises their Terraform Rating by {by}.", player_name(player))
            }
            LogEvent::DrewCards { player, count } => {
                format!("{} draws {}.", player_name(player), counted(count, "card", "cards"))
            }
            LogEvent::LookedAtCards { player, cards: 1 } => {
                format!("{} looks at the top card of the deck.", player_name(player))
            }
            LogEvent::LookedAtCards { player, cards } => format!(
                "{} looks at the top {} of the deck.",
                player_name(player),
                counted(cards as i32, "card", "cards")
            ),
            LogEvent::KeptCards { player, kept, discarded, price: 0 } => format!(
                "{} keeps {} and discards {discarded}.",
                player_name(player),
                counted(kept as i32, "card", "cards")
            ),
            LogEvent::KeptCards { player, kept: 0, discarded, .. } => {
                format!("{} buys none of them and discards {discarded}.", player_name(player))
            }
            LogEvent::KeptCards { player, kept, discarded, price } => format!(
                "{} buys {} for {} and discards {discarded}.",
                player_name(player),
                counted(kept as i32, "card", "cards"),
                Resource::MegaCredits.counted(price * kept as i32)
            ),
            LogEvent::TriggerTakesEffect { player, card } => {
                format!("{}'s {} takes effect.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::DiscardedToDraw { player } => {
                format!("{} discards a card to draw one.", player_name(player))
            }
            LogEvent::CopiedProductionBox { player, card } => {
                format!("{} copies the production box of {}.", player_name(player), CARD_CATALOG[card].name)
            }
            LogEvent::RevealedCard { player, card } => format!(
                "{} reveals {} from the top of the deck and discards it.",
                player_name(player),
                CARD_CATALOG[card].name
            ),
            LogEvent::CardResourcesChanged { player, card, by } => {
                let printed = &CARD_CATALOG[card];
                let (verb, preposition) = if by < 0 { ("removes", "from") } else { ("adds", "to") };
                let amount = printed.held().counted(by.abs());
                format!("{} {verb} {amount} {preposition} {}.", player_name(player), printed.name)
            }
            LogEvent::NoCardToAddTo { player, add } => {
                format!("{} has no card to add {} to.", player_name(player), add.amount_text())
            }
            LogEvent::MovedCardResource { player, owner, from, card } => {
                let whose = if owner == player {
                    "their own".to_string()
                } else {
                    format!("{}'s", player_name(owner))
                };
                format!(
                    "{} moves {} from {whose} {} to {}.",
                    player_name(player),
                    CARD_CATALOG[card].held().counted(1),
                    CARD_CATALOG[from].name,
                    CARD_CATALOG[card].name
                )
            }
            LogEvent::RemovedFromCard { player, owner, from, amount } => format!(
                "{} removes {} from {}'s {}.",
                player_name(player),
                CARD_CATALOG[from].held().counted(amount),
                player_name(owner),
                CARD_CATALOG[from].name
            ),
            LogEvent::LoweredProductionOf { player, target, resource, by } => {
                let whose = if target == player {
                    "their own".to_string()
                } else {
                    format!("{}'s", player_name(target))
                };
                format!("{} lowers {whose} {} Production by {by}.", player_name(player), resource.name())
            }
            LogEvent::RemovedResources { player, target, resource, amount, stolen } => format!(
                "{} {} {} from {}.",
                player_name(player),
                if stolen { "steals" } else { "removes" },
                resource.counted(amount),
                player_name(target)
            ),
            LogEvent::RemovedNothing { player, card, stolen } => format!(
                "{} {} nothing with {}.",
                player_name(player),
                if stolen { "steals" } else { "removes" },
                CARD_CATALOG[card].name
            ),
            LogEvent::SoldPatents { player, cards } => format!(
                "{} sells {} for {}.",
                player_name(player),
                counted(cards as i32, "patent", "patents"),
                Resource::MegaCredits.counted(PATENT_VALUE * cards as i32)
            ),
            LogEvent::DiscardPileReshuffled { cards } => format!(
                "The deck has run out, so the discard pile is shuffled into a new deck of {}.",
                counted(cards as i32, "card", "cards")
            ),
            LogEvent::DeckAndDiscardPileEmpty { player } => format!(
                "The deck and the discard pile are empty, so {} draws no more cards.",
                player_name(player)
            ),
            LogEvent::ConvertedPlants { player, plants } => {
                format!("{} converts {plants} plants into a Greenery.", player_name(player))
            }
            LogEvent::ConvertedHeat { player } => format!(
                "{} converts {HEAT_PER_TEMPERATURE_STEP} heat into a Temperature step.",
                player_name(player)
            ),
            LogEvent::OxygenRaised { player, oxygen } => {
                format!("{} raises Oxygen to {oxygen} % and gains 1 Terraform Rating.", player_name(player))
            }
            LogEvent::OxygenAlreadyAtMaximum => {
                "Oxygen is already at its maximum, so it does not rise.".to_string()
            }
            LogEvent::PlacedTile { player, placement, area } => {
                let tile = match placement.special {
                    Some(special) => special.name(),
                    None => placement.tile.with_article(),
                };
                format!("{} places {tile} on {}.", player_name(player), area_label(area))
            }
            LogEvent::ClaimedArea { player, area } => {
                format!("{} claims {} with Land Claim.", player_name(player), area_label(area))
            }
            LogEvent::OceansRaised { player, oceans } => {
                format!(
                    "{} raises Oceans to {oceans} of {MAX_OCEANS} and gains 1 Terraform Rating.",
                    player_name(player)
                )
            }
            LogEvent::OceansAlreadyAtMaximum => {
                format!("All {MAX_OCEANS} Oceans are already placed, so no Ocean is placed.")
            }
            LogEvent::PlacementBonus { player, item, amount } => match item.resource() {
                Some(resource) => {
                    format!(
                        "{} gains {} from the placement bonus.",
                        player_name(player),
                        resource.counted(amount)
                    )
                }
                None => format!(
                    "{} draws {} from the placement bonus.",
                    player_name(player),
                    counted(amount, "card", "cards")
                ),
            },
            LogEvent::CollectsWaitingBonus { player, area } => {
                format!(
                    "{} collects the placement bonus of the Greenery on {}.",
                    player_name(player),
                    area_label(area)
                )
            }
            LogEvent::AdjacentOceans { player, oceans } => format!(
                "{} gains {} MegaCredits for {}.",
                player_name(player),
                OCEAN_ADJACENCY_BONUS * oceans as i32,
                counted(oceans as i32, "adjacent Ocean", "adjacent Oceans")
            ),
            LogEvent::EndedTurn { player } => format!("{} ends their Turn.", player_name(player)),
            LogEvent::Passed { player } => format!("{} passes.", player_name(player)),
            LogEvent::ProductionPhase => "Production phase.".to_string(),
            LogEvent::EnergyTurnsIntoHeat { player, energy } => {
                format!("{}'s {energy} energy turns into heat.", player_name(player))
            }
            LogEvent::Produced { player, terraform_rating, production } => {
                let megacredits = format!(
                    "{} (Terraform Rating {terraform_rating} + MegaCredit Production {})",
                    Resource::MegaCredits.counted(terraform_rating + production.megacredits),
                    production.megacredits
                );
                let others = Resource::ALL
                    .into_iter()
                    .filter(|&resource| resource != Resource::MegaCredits && production[resource] > 0)
                    .map(|resource| resource.counted(production[resource]));
                format!(
                    "{} gains {}.",
                    player_name(player),
                    listed(std::iter::once(megacredits).chain(others))
                )
            }
            LogEvent::MarsIsTerraformed => {
                "Mars is terraformed: Temperature, Oxygen and Oceans are all at their maximum.".to_string()
            }
            LogEvent::FinalGreeneryConversion { first_player } => {
                format!("Final Greenery conversion, in player order from {}.", player_name(first_player))
            }
            LogEvent::DoneConvertingPlants { player } => {
                format!("{} is done converting plants.", player_name(player))
            }
            LogEvent::GameOver => "The Game is over.".to_string(),
            LogEvent::AwardPlace(AwardPlace { award, player, place, count, shared }) => format!(
                "{} {} {} place in the {} Award ({}) and gains {} Victory Points.",
                player_name(player),
                if shared { "shares" } else { "takes" },
                place.name(),
                award.name(),
                award.counted(count),
                place.victory_points()
            ),
            LogEvent::FinalScore { player, victory_points } => {
                format!("{} finishes with {victory_points} Victory Points.", player_name(player))
            }
            LogEvent::Won { player, win } => match win {
                Win::Outright => format!("{} wins.", player_name(player)),
                Win::OnMegaCredits => format!(
                    "{} wins: tied on Victory Points, but with the most MegaCredits.",
                    player_name(player)
                ),
                Win::Shared => format!(
                    "{} shares the win, tied on both Victory Points and MegaCredits.",
                    player_name(player)
                ),
            },
        }
    }
}

/// "a", "a and b", "a, b and c".
pub fn listed(items: impl Iterator<Item = String>) -> String {
    let items: Vec<String> = items.collect();
    match items.split_last() {
        Some((last, [])) => last.clone(),
        Some((last, rest)) => format!("{} and {last}", rest.join(", ")),
        None => String::new(),
    }
}

/// "1 plant", "2 plants".
fn counted(amount: i32, one: &str, many: &str) -> String {
    format!("{amount} {}", if amount == 1 { one } else { many })
}

/// Players are numbered from 1 for people, but indexed from 0 everywhere else.
pub fn player_name(index: usize) -> String {
    format!("Player {}", index + 1)
}
