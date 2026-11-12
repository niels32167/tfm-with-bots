//! How Project Cards move through a Game outside of being played: the deal at setup and in
//! each Research phase, buying the cards dealt, drawing from the deck, looking at cards to keep
//! or buy some of them, and the discard pile.
//!
//! Buying is simultaneous at the table. The engine asks one Player at a time, in player order
//! from the first player (ADR 0002), and keeps what each buys hidden until all are done: nobody
//! pays and no card moves until the last Player is done buying.

use crate::card_set::CardSet;
use crate::cards::LookAt;
use crate::deck::Deck;
use crate::expenses::Expense;
use crate::game::{DecisionOption, Game, Phase, Waiting};
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
    /// How much of the price they pay with heat, once every Player is done buying (Helion).
    pub heat: i32,
    /// Whether they are done buying. Players are asked in player order, but a Sampled Position takes
    /// back the hidden choices of those before its Player and asks them again after the last.
    pub done: bool,
}

impl Buying {
    /// The cards dealt that are not bought (yet).
    fn unbought(self) -> CardSet {
        self.dealt.without(self.bought)
    }
}

/// The cards the current Player looks at while playing `card` (Business Contacts) or using its
/// action (Inventors' Guild): those they may still keep or buy, those they have kept or bought,
/// and how many more they keep, or may still buy, before the rest are discarded.
#[derive(Clone, Copy, Debug)]
pub struct Keeping {
    pub card: usize,
    pub looking_at: CardSet,
    pub kept: CardSet,
    pub keep: usize,
    /// What each card kept costs: nothing for cards they keep, the card price for cards they buy.
    /// Buying is up to them, so they may be done and discard the rest.
    pub price: i32,
    /// Whether they look at the cards with the card's action, rather than while playing it.
    pub for_action: bool,
}

impl Keeping {
    /// The Player may keep any of the cards they are looking at. Buying them instead, they may buy
    /// any if `megacredits` pays for it on top of those bought so far, or be done.
    pub fn options(self, megacredits: i32) -> Vec<DecisionOption> {
        if self.price == 0 {
            return self.looking_at.iter().map(DecisionOption::KeepCard).collect();
        }
        let buys = self.looking_at.iter().filter(|_| self.can_buy_one_more(megacredits));
        buys.map(DecisionOption::BuyCard).chain([DecisionOption::Done]).collect()
    }

    /// Whether the Player has a Decision to make: more cards to keep from than they keep, or a
    /// card they can buy with `megacredits`.
    fn needs_a_decision(self, megacredits: i32) -> bool {
        match self.price {
            0 => self.looking_at.len() > self.keep,
            _ => !self.looking_at.is_empty() && self.can_buy_one_more(megacredits),
        }
    }

    /// Whether the Player, buying cards, may buy one more and pay for it with `megacredits` on top
    /// of those bought so far.
    fn can_buy_one_more(self, megacredits: i32) -> bool {
        self.keep > 0 && megacredits >= self.price * (self.kept.len() as i32 + 1)
    }
}

impl Game {
    /// The setup buy: each Player is dealt their cards to buy from, before Generation 1.
    pub(crate) fn begin_setup(&mut self) {
        self.phase = Phase::Setup;
        self.log.push(LogEvent::Setup);
        if self.settings.corporations {
            self.deal_corporations();
        }
        if self.settings.prelude {
            self.deal_prelude_cards();
        }
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

    /// Whether `player` has something to decide: a Corporation to choose or a Prelude Card to keep at
    /// setup, or one more of the cards dealt to them to buy: one is left, and they can pay for it on
    /// top of those they have bought so far.
    fn can_buy(&self, player: usize) -> bool {
        let own = &self.players[player];
        let price = CARD_PRICE * (own.buying.bought.len() as i32 + 1);
        own.choosing_corporation.is_due()
            || own.prelude_cards.keeping_due()
            || !own.buying.unbought().is_empty() && self.megacredits_to_buy_with(player) >= price
    }

    /// The current Player may buy any card dealt to them that they haven't bought, or be done.
    pub(crate) fn buying_options(&self) -> Vec<DecisionOption> {
        let unbought = self.players[self.current_player].buying.unbought();
        unbought.iter().map(DecisionOption::BuyCard).chain([DecisionOption::Done]).collect()
    }

    /// The current Player buys `card`.
    pub(crate) fn buy(&mut self, card: usize) {
        self.players[self.current_player].buying.bought.insert(card);
        self.buy_more_or_be_done();
    }

    /// Once the current Player can buy no more, they are done. At setup, they keep their Prelude
    /// Cards before they buy.
    pub(crate) fn buy_more_or_be_done(&mut self) {
        if !self.can_buy(self.current_player) {
            self.done_buying();
        } else {
            self.offer_keeping_prelude_card();
        }
    }

    /// The current Player is done buying. Unless they say how they will pay with heat first, the
    /// next one decides.
    pub(crate) fn done_buying(&mut self) {
        let own = &self.players[self.current_player];
        if !own.buying.bought.is_empty() && self.usable_heat(self.current_player, 0) > 0 {
            return self.spend_on(Expense::BoughtCards);
        }
        self.next_player_buys();
    }

    /// The current Player is done, and the next Player who can buy a card decides.
    pub(crate) fn next_player_buys(&mut self) {
        self.players[self.current_player].buying.done = true;
        self.offer_buying_from(self.index_in_player_order() + 1);
    }

    /// Whether `player` is still to be asked about buying: they aren't done, and have something to decide.
    fn still_buying(&self, player: usize) -> bool {
        !self.players[player].buying.done && self.can_buy(player)
    }

    /// Hands buying to the next Player still buying, looking from index `start` in player order (0 is
    /// the first player); at setup, they first choose their Corporation and keep their Prelude Cards.
    /// Once nobody is, every Player's buys are carried out.
    pub(crate) fn offer_buying_from(&mut self, start: usize) {
        match self.next_in_player_order_who(start, Game::still_buying) {
            Some(player) => {
                self.current_player = player;
                if self.players[player].choosing_corporation.is_due() {
                    self.wait_on(Waiting::Corporation);
                } else {
                    self.offer_keeping_prelude_card();
                }
            }
            None => self.finish_buying(),
        }
    }

    /// Every Player, in player order, reveals their Corporation if they are choosing one, puts back
    /// the Prelude Cards they didn't keep, pays for the cards they bought and takes them into their
    /// hand, and the rest of the cards dealt go face down to the discard pile. Then the Action phase
    /// begins, after setup with Generation 1, once Players have played their Prelude Cards.
    fn finish_buying(&mut self) {
        for player in self.player_order() {
            self.reveal_corporation(player);
            self.put_back_prelude_cards_not_kept(player);
            let own = &mut self.players[player];
            let buying = std::mem::take(&mut own.buying);
            own.resources.megacredits -= CARD_PRICE * buying.bought.len() as i32 - buying.heat;
            own.resources.heat -= buying.heat;
            own.hand = own.hand.union(buying.bought);
            self.discard = self.discard.union(buying.unbought());
            if !buying.dealt.is_empty() {
                let (bought, dealt) = (buying.bought.len(), buying.dealt.len());
                self.log.push(LogEvent::BoughtCards { player, bought, dealt });
                self.log_heat_paid(player, buying.heat);
            }
        }
        match self.phase {
            Phase::Setup if self.settings.prelude => self.begin_playing_prelude_cards(),
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
        if let Some(Waiting::SellPatents(sold)) = &mut self.waiting {
            *sold += 1;
        }
        if own.hand.is_empty() {
            self.finish_selling();
        }
    }

    /// The current Player is done selling patents, which ends the Action.
    pub(crate) fn finish_selling(&mut self) {
        let Some(Waiting::SellPatents(sold)) = self.waiting.take() else {
            panic!("only a Player selling patents finishes selling")
        };
        self.log.push(LogEvent::SoldPatents { player: self.current_player, cards: sold });
        self.finish_unless_placing();
    }

    /// `player`, playing `card` or using its action (`for_action`), looks at the top cards of the
    /// deck that `look_at` names, if any, to keep or buy some of them. Returns whether the Game
    /// now waits on which; with no choice to make, they keep them all, or with none they can buy,
    /// discard them all, without a Decision.
    pub(crate) fn look_at_cards(
        &mut self,
        player: usize,
        card: usize,
        look_at: Option<LookAt>,
        for_action: bool,
    ) -> bool {
        let Some(LookAt { cards, keep, buy }) = look_at else { return false };
        let looking_at = self.draw_cards(player, cards);
        self.log.push(LogEvent::LookedAtCards { player, cards: looking_at.len() });
        let (keep, price) = if buy > 0 { (buy as usize, CARD_PRICE) } else { (keep as usize, 0) };
        let keeping = Keeping { card, looking_at, kept: CardSet::default(), keep, price, for_action };
        if keeping.needs_a_decision(self.spendable_megacredits(player)) {
            self.wait_on(Waiting::KeepCards(keeping));
            return true;
        }
        let (kept, discarded) =
            if price == 0 { (looking_at, CardSet::default()) } else { (CardSet::default(), looking_at) };
        self.keep_and_discard(player, kept, discarded, price);
        false
    }

    /// The current Player keeps or buys `card`, one of those they are looking at. Once they have
    /// no more choice to make, they are done keeping.
    pub(crate) fn keep_card(&mut self, card: usize) {
        let Some(Waiting::KeepCards(mut keeping)) = self.waiting.take() else {
            panic!("only a Player looking at cards keeps one")
        };
        keeping.looking_at.remove(card);
        keeping.kept.insert(card);
        keeping.keep -= 1;
        if keeping.keep > 0 && keeping.needs_a_decision(self.spendable_megacredits(self.current_player)) {
            self.waiting = Some(Waiting::KeepCards(keeping));
            return;
        }
        self.spend_on(Expense::KeptCards(keeping));
    }

    /// The current Player, buying cards they look at, buys no more of them.
    pub(crate) fn done_keeping(&mut self) {
        let Some(Waiting::KeepCards(keeping)) = self.waiting.take() else {
            panic!("only a Player buying cards they look at is done with them")
        };
        self.spend_on(Expense::KeptCards(keeping));
    }

    /// The cards kept, which `heat` helped pay for, go into the current Player's hand, and the rest
    /// are discarded. Then the card they play carries on with its Production change, or the action
    /// they use ends.
    pub(crate) fn keep_cards_paid_for(&mut self, keeping: Keeping, heat: i32) {
        let player = self.current_player;
        self.keep_and_discard(player, keeping.kept, keeping.looking_at, keeping.price);
        self.log_heat_paid(player, heat);
        if keeping.for_action {
            self.finish_card_action(keeping.card);
        } else {
            self.choose_production_change(player, keeping.card);
        }
    }

    /// `player`, who has paid `price` for each card `kept`, takes them into their hand, and
    /// `discarded` go face down to the discard pile.
    fn keep_and_discard(&mut self, player: usize, kept: CardSet, discarded: CardSet, price: i32) {
        let own = &mut self.players[player];
        own.hand = own.hand.union(kept);
        self.discard = self.discard.union(discarded);
        self.log.push(LogEvent::KeptCards { player, kept: kept.len(), discarded: discarded.len(), price });
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
