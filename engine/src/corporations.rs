//! Corporations at setup: each Player is dealt 2 and chooses one. The choice is simultaneous at the
//! table. The engine asks one Player at a time, in player order from the first player (ADR 0002), and
//! keeps it hidden until every Player is done buying: then each reveals their Corporation, which joins
//! their played cards, so that its Tags and ongoing effects count as a Project Card's do.

use crate::card_set::CardSet;
use crate::cards::{BASE_BOX_CARDS, CARD_CATALOG, PROJECT_CARDS};
use crate::game::{DecisionOption, Game};
use crate::log::LogEvent;
use crate::triggers::Happened;

/// How many Corporations each Player is dealt at setup.
pub const CORPORATIONS_DEALT: usize = 2;

/// At setup, the Corporations dealt to a Player and the one of them they chose, if they have.
#[derive(Clone, Copy, Debug, Default)]
pub struct ChoosingCorporation {
    pub dealt: CardSet,
    pub picked: Option<usize>,
}

impl ChoosingCorporation {
    /// Whether the Player still has to choose: they were dealt Corporations, as a Player of a Game
    /// with them is, and chose none yet.
    pub fn is_due(self) -> bool {
        !self.dealt.is_empty() && self.picked.is_none()
    }
}

impl Game {
    /// Each Player, in player order from the first player, is dealt their Corporations from the
    /// shuffled Corporations. Those left over, and later those not chosen, go back in the box.
    pub(crate) fn deal_corporations(&mut self) {
        let mut corporations: Vec<usize> = (PROJECT_CARDS..BASE_BOX_CARDS).collect();
        self.random_numbers.shuffle(&mut corporations);
        let mut dealing = corporations.chunks(CORPORATIONS_DEALT);
        for player in self.player_order() {
            let dealt = dealing.next().expect("there are enough Corporations for 5 Players");
            self.players[player].choosing_corporation.dealt = dealt.iter().copied().collect();
        }
        self.log.push(LogEvent::CorporationsDealt);
    }

    /// The current Player may choose any Corporation dealt to them.
    pub(crate) fn corporation_options(&self) -> Vec<DecisionOption> {
        let dealt = self.players[self.current_player].choosing_corporation.dealt;
        dealt.iter().map(DecisionOption::ChooseCorporation).collect()
    }

    /// The current Player chooses `card`, and goes on to buy cards with its starting MegaCredits.
    pub(crate) fn choose_corporation(&mut self, card: usize) {
        self.waiting = None;
        self.players[self.current_player].choosing_corporation.picked = Some(card);
        self.buy_more_or_be_done();
    }

    /// `player` reveals the Corporation they chose, if they chose one, and gets its starting Resources
    /// and Production. Its Tags are put into play, "including this" for Saturn Systems.
    pub(crate) fn reveal_corporation(&mut self, player: usize) {
        let Some(card) = std::mem::take(&mut self.players[player].choosing_corporation).picked else {
            return;
        };
        let own = &mut self.players[player];
        own.played.insert(card);
        own.first_action_due = CARD_CATALOG[card].first_action().is_some();
        self.log.push(LogEvent::RevealedCorporation { player, card });
        self.carry_out(player, card, CARD_CATALOG[card].implemented_effects());
        self.set_off(Happened::CardPlayed { player, card });
    }

    /// The Corporation whose first action the current Player must take before anything else but
    /// passing, if it is due and they can carry it out. If they can't, they go without it, as the
    /// open-source game has them do.
    pub(crate) fn first_action_to_take(&self) -> Option<usize> {
        let own = &self.players[self.current_player];
        if !own.first_action_due {
            return None;
        }
        own.corporation().filter(|&card| {
            CARD_CATALOG[card]
                .first_action()
                .is_some_and(|first| self.can_carry_out(self.current_player, first))
        })
    }

    /// The current Player takes the first action of `card`, their Corporation, as an Action.
    pub(crate) fn take_first_action(&mut self, card: usize) {
        let player = self.current_player;
        let first_action = CARD_CATALOG[card].first_action().expect("only a first action due is taken");
        self.players[player].first_action_due = false;
        self.log.push(LogEvent::TookFirstAction { player, card });
        self.carry_out(player, card, first_action);
        if let Some(&placement) = first_action.tiles.first() {
            self.place_card_tile(card, placement);
        }
        self.finish_unless_placing();
    }

    /// What `player` may spend on the cards dealt to them, so far as they know: at setup the starting
    /// MegaCredits of the Corporation they chose, which they get only once it is revealed, and
    /// otherwise what they could spend, heat included (Helion).
    pub fn megacredits_to_buy_with(&self, player: usize) -> i32 {
        match self.players[player].choosing_corporation.picked {
            Some(card) => CARD_CATALOG[card].implemented_effects().resources.megacredits,
            None => self.spendable_megacredits(player),
        }
    }
}
