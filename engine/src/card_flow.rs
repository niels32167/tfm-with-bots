//! How Project Cards move through a Game outside of being played: the deal at setup and in
//! each Research phase, buying the cards dealt, drawing from the deck, and the discard pile.
//!
//! Buying is simultaneous at the table. The engine asks one Player at a time, in player order
//! from the first player (ADR 0002), and keeps what each buys hidden until all are done: nobody
//! pays and no card moves until the last Player is done buying.

use crate::card_set::CardSet;
use crate::deck::Deck;
use crate::game::{DecisionOption, Game, Phase};
use crate::log::LogEvent;

/// How many Project Cards each Player is dealt at setup.
pub const SETUP_CARDS: i32 = 10;
/// How many cards each Player draws in each Research phase.
pub const RESEARCH_CARDS: i32 = 4;

/// What buying a dealt card costs, in MegaCredits.
pub const CARD_PRICE: i32 = 3;

/// What each card sold with the Sell Patents Standard Project gains, in MegaCredits.
pub const PATENT_VALUE: i32 = 1;

/// The cards dealt to a Player to buy from in the setup or a Research phase, and those of them
/// they have bought so far. Nothing is paid until every Player is done buying.
#[derive(Clone, Copy, Debug, Default)]
pub struct Buying {
    pub dealt: CardSet,
    pub bought: CardSet,
}

impl Buying {
    /// The cards dealt that are not bought (yet).
    fn unbought(self) -> CardSet {
        self.dealt.without(self.bought)
    }
}

impl Game {
    /// The setup buy: each Player is dealt their cards to buy from, before Generation 1.
    pub(crate) fn begin_setup(&mut self) {
        self.phase = Phase::Setup;
        self.log.push(LogEvent::Setup);
        self.deal(SETUP_CARDS);
    }

    /// The Research phase, from Generation 2: each Player draws their cards to buy from, or
    /// with the Draft on, drafts them.
    pub(crate) fn begin_research_phase(&mut self) {
        if self.settings.draft {
            return self.begin_draft();
        }
        self.phase = Phase::Research;
        self.log.push(LogEvent::ResearchPhase);
        self.deal(RESEARCH_CARDS);
    }

    /// Each Player, in player order from the first player, is dealt `count` cards from the
    /// deck to buy from; then the first of them who can buy one decides.
    fn deal(&mut self, count: i32) {
        for player in self.player_order() {
            self.players[player].buying.dealt = self.draw_cards(player, count);
        }
        self.offer_buying_from(0);
    }

    /// Whether `player` may buy one more of the cards dealt to them: one is left, and they can
    /// pay for it on top of those they have bought so far.
    fn can_buy(&self, player: usize) -> bool {
        let own = &self.players[player];
        let price = CARD_PRICE * (own.buying.bought.len() as i32 + 1);
        !own.buying.unbought().is_empty() && own.resources.megacredits >= price
    }

    /// The current Player may buy any card dealt to them that they haven't bought, or be done.
    pub(crate) fn buying_options(&self) -> Vec<DecisionOption> {
        let unbought = self.players[self.current_player].buying.unbought();
        unbought.iter().map(DecisionOption::BuyCard).chain([DecisionOption::Done]).collect()
    }

    /// The current Player buys `card`. Once they can buy no more, they are done.
    pub(crate) fn buy(&mut self, card: usize) {
        self.players[self.current_player].buying.bought.insert(card);
        if !self.can_buy(self.current_player) {
            self.done_buying();
        }
    }

    /// The current Player is done buying, and the next one decides.
    pub(crate) fn done_buying(&mut self) {
        self.offer_buying_from(self.index_in_player_order() + 1);
    }

    /// Hands buying to the first Player who can buy a card, looking from index `start` in player
    /// order (0 is the first player). Once nobody can, every Player's buys are carried out.
    pub(crate) fn offer_buying_from(&mut self, start: usize) {
        match self.first_in_player_order_who(start, Game::can_buy) {
            Some(player) => self.current_player = player,
            None => self.finish_buying(),
        }
    }

    /// Every Player pays for the cards they bought and takes them into their hand, and the rest
    /// of the cards dealt go face down to the discard pile. Then the Action phase begins, after
    /// setup with Generation 1.
    fn finish_buying(&mut self) {
        for player in self.player_order() {
            let own = &mut self.players[player];
            let buying = std::mem::take(&mut own.buying);
            own.resources.megacredits -= CARD_PRICE * buying.bought.len() as i32;
            own.hand = own.hand.union(buying.bought);
            self.discard = self.discard.union(buying.unbought());
            if !buying.dealt.is_empty() {
                let (bought, dealt) = (buying.bought.len(), buying.dealt.len());
                self.log.push(LogEvent::BoughtCards { player, bought, dealt });
            }
        }
        match self.phase {
            Phase::Setup => self.begin(1, self.first_player),
            _ => self.begin_action_phase(),
        }
    }

    /// The current Player, selling patents, may sell any card in their hand; once they have sold
    /// one, they may be done instead. (Selling none would only waste the Action.)
    pub(crate) fn selling_options(&self, sold: usize) -> Vec<DecisionOption> {
        let hand = self.players[self.current_player].hand.iter().map(DecisionOption::SellCard);
        let done = (sold > 0).then_some(DecisionOption::Done);
        hand.chain(done).collect()
    }

    /// The current Player sells `card` from their hand: it goes face down to the discard pile, and
    /// they gain its value. With their hand empty, they are done.
    pub(crate) fn sell(&mut self, card: usize) {
        let own = &mut self.players[self.current_player];
        own.hand.remove(card);
        own.resources.megacredits += PATENT_VALUE;
        self.discard.insert(card);
        self.selling = self.selling.map(|sold| sold + 1);
        if own.hand.is_empty() {
            self.finish_selling();
        }
    }

    /// The current Player is done selling patents, which ends the Action.
    pub(crate) fn finish_selling(&mut self) {
        let sold = self.selling.take().expect("only a Player selling patents finishes selling");
        self.log.push(LogEvent::SoldPatents { player: self.current_player, cards: sold });
        self.finish_unless_placing();
    }

    /// `player` draws `count` cards into their hand.
    pub(crate) fn draw(&mut self, player: usize, count: i32) {
        let drawn = self.draw_cards(player, count);
        let hand = &mut self.players[player].hand;
        *hand = hand.union(drawn);
    }

    /// The `count` cards `player` draws from the top of the deck. When the deck runs out, the
    /// discard pile is shuffled into a new deck; once both are empty, they draw no more.
    pub(crate) fn draw_cards(&mut self, player: usize, count: i32) -> CardSet {
        let mut drawn = CardSet::default();
        for _ in 0..count {
            if self.deck.is_empty() && !self.discard.is_empty() {
                self.deck = Deck::shuffled_from(self.discard, &mut self.random_numbers);
                self.discard = CardSet::default();
                self.log.push(LogEvent::DiscardPileReshuffled { cards: self.deck.len() });
            }
            let Some(card) = self.deck.draw() else {
                self.log.push(LogEvent::DeckAndDiscardPileEmpty { player });
                break;
            };
            drawn.insert(card);
        }
        drawn
    }
}
