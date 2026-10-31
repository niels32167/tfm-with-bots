//! Triggers: what an Active card's Player gains each time something happens while the card is in
//! play, such as Arctic Algae's 2 plants when anyone places an Ocean. They are effect data
//! (`cards::Trigger`), plus Mars University's Rust code in `card_code`.

use crate::board::TileKind;
use crate::card_code::MARS_UNIVERSITY;
use crate::cards::{CARD_CATALOG, CARDS_WITH, Owner, TriggerCondition};
use crate::game::Game;
use crate::log::LogEvent;

/// Something that happened in the Game which a card's Trigger may be set off by.
#[derive(Clone, Copy, Debug)]
pub enum Happened {
    /// `player` placed a Tile of this kind.
    TilePlaced { player: usize, tile: TileKind },
    /// `player` played `card`.
    CardPlayed { player: usize, card: usize },
    /// `player` paid for a Standard Project other than Sell Patents.
    StandardProject { player: usize },
}

impl Happened {
    /// How many times this sets off `on` for a card of `owner`'s: once, or once for each Tag
    /// played, or not at all.
    fn times(self, on: TriggerCondition, owner: usize) -> i32 {
        match (self, on) {
            (Happened::TilePlaced { player, tile }, TriggerCondition::TilePlaced { tile: kind, by }) => {
                i32::from(tile == kind && (by == Owner::Anyone || player == owner))
            }
            (Happened::CardPlayed { player, card }, TriggerCondition::CardPlayed { card_type, tag }) => {
                let printed = &CARD_CATALOG[card];
                let matches = card_type.is_none_or(|kind| printed.card_type == kind)
                    && tag.is_none_or(|tag| printed.has_tag(tag));
                i32::from(player == owner && matches)
            }
            (Happened::CardPlayed { player, card }, TriggerCondition::TagPlayed(tag)) if player == owner => {
                CARD_CATALOG[card].tags.iter().filter(|&&each| each == tag).count() as i32
            }
            (Happened::StandardProject { player }, TriggerCondition::StandardProject) => {
                i32::from(player == owner)
            }
            _ => 0,
        }
    }
}

impl Game {
    /// Every Trigger that `happened` sets off is carried out, for whichever Player's card it is
    /// on: Players in player number order, and each Player's cards in card-number order. A card
    /// in play counts itself: Immigrant City's own City sets it off. The order never changes the
    /// outcome: each Trigger only gains its Player something, but Mars University's, which lets
    /// its Player discard once the card being played is done (see `card_code`).
    pub(crate) fn set_off(&mut self, happened: Happened) {
        for owner in 0..self.players.len() {
            for card in self.players[owner].played.intersection(CARDS_WITH.triggers).iter() {
                for trigger in &CARD_CATALOG[card].implemented_effects().when {
                    let times = happened.times(trigger.on, owner);
                    if times > 0 && card == MARS_UNIVERSITY {
                        self.discards_to_draw += times as u32;
                    } else if times > 0 {
                        self.log.push(LogEvent::TriggerTakesEffect { player: owner, card });
                        self.change_resources(owner, trigger.resources.times(times));
                        self.change_productions(owner, trigger.production.times(times));
                    }
                }
            }
        }
    }
}
