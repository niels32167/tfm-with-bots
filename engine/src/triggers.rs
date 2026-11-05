//! Triggers: what an Active card's or a Corporation's Player gains each time something happens while
//! the card is in play, such as Arctic Algae's 2 plants when anyone places an Ocean. They are effect data
//! (`cards::Trigger`), plus Mars University's, Olympus Conference's and Viral Enhancers' Rust code in
//! `card_code`.

use crate::board::{TileKind, printed};
use crate::card_code::{MARS_UNIVERSITY, OLYMPUS_CONFERENCE, VIRAL_ENHANCERS, ViralEnhancing};
use crate::cards::{CARD_CATALOG, CARDS_WITH, Owner, Tag, TriggerCondition};
use crate::game::{Game, StandardProject};
use crate::log::LogEvent;

/// Something that happened in the Game which a card's Trigger may be set off by.
#[derive(Clone, Copy, Debug)]
pub enum Happened {
    /// `player` placed a Tile of this kind, on Mars or off it.
    TilePlaced { player: usize, tile: TileKind, on_mars: bool },
    /// `player` played `card`.
    CardPlayed { player: usize, card: usize },
    /// `player` paid for a Standard Project other than Sell Patents.
    StandardProject { player: usize, project: StandardProject },
    /// `player` got the placement bonus printed on `area`.
    PlacementBonus { player: usize, area: usize },
}

impl Happened {
    /// How many times this sets off `on` for a card of `owner`'s: once, or once for each Tag
    /// played, or not at all.
    pub(crate) fn times(self, on: &TriggerCondition, owner: usize) -> i32 {
        match (self, on) {
            (
                Happened::TilePlaced { player, tile, on_mars },
                TriggerCondition::TilePlaced { tile: kind, by, on_mars: only_on_mars },
            ) => i32::from(
                tile == *kind && (*by == Owner::Anyone || player == owner) && (on_mars || !only_on_mars),
            ),
            (Happened::CardPlayed { player, card }, TriggerCondition::CardPlayed { card_type, tag }) => {
                let printed = &CARD_CATALOG[card];
                let matches = card_type.is_none_or(|kind| printed.card_type == kind)
                    && tag.is_none_or(|tag| printed.has_tag(tag));
                i32::from(player == owner && matches)
            }
            (Happened::CardPlayed { player, card }, TriggerCondition::TagPlayed(tags)) if player == owner => {
                tags_on(card, tags)
            }
            (Happened::CardPlayed { card, .. }, TriggerCondition::TagPlayedByAnyone(tags)) => {
                tags_on(card, tags)
            }
            (Happened::CardPlayed { player, card }, TriggerCondition::CostAtLeast(cost)) => {
                i32::from(player == owner && CARD_CATALOG[card].cost.is_some_and(|printed| printed >= *cost))
            }
            (Happened::StandardProject { player, .. }, TriggerCondition::StandardProject) => {
                i32::from(player == owner)
            }
            (Happened::StandardProject { player, project }, TriggerCondition::CostAtLeast(cost)) => {
                i32::from(player == owner && project.cost() >= *cost)
            }
            (Happened::PlacementBonus { player, area }, TriggerCondition::PlacementBonus(resources)) => {
                let gives_one = printed(area)
                    .bonus
                    .iter()
                    .any(|item| item.resource().is_some_and(|given| resources.contains(&given)));
                i32::from(player == owner && gives_one)
            }
            _ => 0,
        }
    }
}

/// How many of `tags` are printed on `card`.
fn tags_on(card: usize, tags: &[Tag]) -> i32 {
    CARD_CATALOG[card].tags.iter().filter(|each| tags.contains(each)).count() as i32
}

impl Game {
    /// Every Trigger that `happened` sets off is carried out, for whichever Player's card it is
    /// on: Players in player number order, and each Player's cards in card-number order. A card
    /// in play counts itself: Immigrant City's own City sets it off. The order never changes the
    /// outcome: each Trigger only gains its Player something, but Mars University's, Olympus
    /// Conference's and Viral Enhancers' on a card that holds Card Resources, which let their Player
    /// choose once the card being played is done (see `card_code`).
    pub(crate) fn set_off(&mut self, happened: Happened) {
        for owner in 0..self.players.len() {
            for card in self.players[owner].played.intersection(CARDS_WITH.triggers).iter() {
                for trigger in &CARD_CATALOG[card].implemented_effects().when {
                    let times = happened.times(&trigger.on, owner);
                    if times == 0 {
                        continue;
                    }
                    match (card, happened) {
                        (MARS_UNIVERSITY, _) => self.discards_to_draw += times as u32,
                        (OLYMPUS_CONFERENCE, _) => self.olympus_conference_due += times as u32,
                        (VIRAL_ENHANCERS, Happened::CardPlayed { card: played, .. })
                            if CARD_CATALOG[played].holds().is_some() =>
                        {
                            self.viral_enhancing = Some(ViralEnhancing { card: played, times: times as u32 });
                        }
                        _ => {
                            self.log.push(LogEvent::TriggerTakesEffect { player: owner, card });
                            self.change_resources(owner, trigger.resources.times(times));
                            self.change_productions(owner, trigger.production.times(times));
                            self.change_card_resources(owner, card, trigger.card_resources * times);
                        }
                    }
                }
            }
        }
    }
}
