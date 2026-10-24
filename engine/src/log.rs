//! The game log. The Game records small events as it goes, and they are turned into
//! plain-language lines only when someone reads the log. Events are plain values,
//! so the log adds little to the cost of copying a Game.

use crate::board::{BonusItem, TileKind, area_label};
use crate::card_flow::{CARD_PRICE, PATENT_VALUE, RESEARCH_CARDS, SETUP_CARDS};
use crate::cards::CARD_CATALOG;
use crate::game::{
    HEAT_PER_TEMPERATURE_STEP, MAX_OCEANS, OCEAN_ADJACENCY_BONUS, OCEAN_BONUS_TEMPERATURE,
    PLANTS_PER_GREENERY, StandardProject, TEMPERATURE_BONUS_OXYGEN,
};
use crate::milestones_and_awards::{Award, MILESTONE_COST, Milestone};
use crate::playing_cards::Payment;
use crate::resources::{Resource, Resources};
use crate::scoring::{AwardPlace, Win};

#[derive(Clone, Copy, Debug)]
pub enum LogEvent {
    Setup,
    GenerationBegins {
        generation: u32,
        first_player: usize,
    },
    ResearchPhase,
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
        tile: TileKind,
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
            LogEvent::GenerationBegins { generation, first_player } => {
                format!("Generation {generation} begins, with {} as first player.", player_name(first_player))
            }
            LogEvent::ResearchPhase => format!(
                "Research phase: each Player draws {RESEARCH_CARDS} cards and may buy any of them for \
                 {CARD_PRICE} MegaCredits each."
            ),
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
            LogEvent::UsedStandardProject { player, project } => format!(
                "{} uses the {} Standard Project for {} MegaCredits.",
                player_name(player),
                project.name(),
                project.cost()
            ),
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
            LogEvent::ConvertedPlants { player } => {
                format!("{} converts {PLANTS_PER_GREENERY} plants into a Greenery.", player_name(player))
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
            LogEvent::PlacedTile { player, tile, area } => {
                format!("{} places {} on {}.", player_name(player), tile.with_article(), area_label(area))
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
