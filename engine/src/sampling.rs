//! Sampled Positions (ADR 0013): a Game made from what one Player knows, with the cards they can't see
//! dealt at random, so that a Controller can look ahead without seeing hidden cards.
//!
//! A `Sampler` is made once for a Player at a position. It keeps the position with every
//! place a hidden card can be emptied out, and the cards that Player can't see in a pool for each kind
//! of card. Each sample deals the pool afresh into those places, the same number of cards to each as
//! the real Game has there. So the Sampler holds no hidden card, and a sample depends only on what the
//! Player View holds and on the sample's seed: two Games the Player can't tell apart give the same
//! samples (tests/engine/test_sampled_positions.py).
//!
//! Nothing of the real Game's past comes along: a sample has its own seed and random numbers, an empty
//! log, a Replay that starts at the sample ("sampled"), and only the Player's own Draft passes.

use crate::card_set::CardSet;
use crate::cards::{CATALOG_CARDS, FIRST_PRELUDE_CARD, corporations_with, project_cards_with};
use crate::deck::Deck;
use crate::expenses::Expense;
use crate::game::{Game, Phase, Waiting};
use crate::prelude_cards::PreludeSet;
use crate::random::RandomNumbers;
use crate::replay::{Replay, Start};

/// Makes Sampled Positions for one Player at one position.
#[derive(Clone, Debug)]
pub struct Sampler {
    /// The Player the samples are for.
    player: usize,
    /// The position with every hidden place empty, and nothing of the real Game's past.
    base: Game,
    /// The places the Player can't see into, and how many cards each holds.
    places: Vec<(Place, usize)>,
    /// The cards the Player can't see and knows nothing more of, of each kind, in card-number order.
    pools: [Vec<usize>; KINDS],
    /// The cards the Player passed in the Draft and can't see now, which they know to be with the
    /// Player they passed them to last, in groups dealt one after the other (see `Pin`).
    pins: Vec<Vec<Pin>>,
    /// The card the current Player, another one, is paying for, which every Player sees: it stays in
    /// their hand until it is played.
    paying_for: Option<usize>,
    /// Whether the current Player, another one, was buying with choices of theirs taken back: they
    /// start again once the cards are dealt.
    restart_buying: bool,
}

/// A place in a Game where cards may be hidden from the Player the sample is for.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Place {
    Hand(usize),
    PickingFrom(usize),
    DraftKept(usize),
    Dealt(usize),
    /// The cards the current Player, another one, is looking at to keep or buy some of them.
    LookingAt,
    /// Those of them they have kept or bought so far.
    KeptOfThoseLookedAt,
    Deck,
    Discard,
    CorporationsDealt(usize),
    PreludeCardsDealt(usize),
    PreludeCardsKept(usize),
    PreludeDeck,
}

/// A card the Player passed in the Draft and can't see now. It goes to the first of `places` (indices
/// into the Sampler's places, all of the Player it went to) with room left, or if none has, with the
/// cards nothing more is known of.
#[derive(Clone, Debug)]
struct Pin {
    card: usize,
    places: Vec<usize>,
}

/// How many times a sample is dealt at most, to leave a Decision in progress with an Option.
const DEALS: usize = 1_000;

const KINDS: usize = 3;
const PROJECT_CARDS: usize = 0;
const CORPORATIONS: usize = 1;
const PRELUDE_CARDS: usize = 2;

impl Place {
    /// Which kind of card goes there.
    fn kind(self) -> usize {
        match self {
            Place::CorporationsDealt(_) => CORPORATIONS,
            Place::PreludeCardsDealt(_) | Place::PreludeCardsKept(_) | Place::PreludeDeck => PRELUDE_CARDS,
            _ => PROJECT_CARDS,
        }
    }
}

impl Sampler {
    pub fn new(game: &Game, player: usize) -> Sampler {
        let mut base = scrubbed(game, player);
        let restart_buying = take_back_hidden_choices(&mut base, player);
        let mut places = Vec::new();
        let mut seen = CardSet::default();
        for (index, own) in base.players.iter().enumerate() {
            seen = seen.union(own.played);
            if index == player {
                seen = seen
                    .union(own.hand)
                    .union(own.drafting.picking_from)
                    .union(own.drafting.kept)
                    .union(own.buying.dealt)
                    .union(own.choosing_corporation.dealt)
                    .union(prelude_cards(own.prelude_cards.dealt))
                    .union(prelude_cards(own.prelude_cards.kept));
                continue;
            }
            places.extend([
                (Place::Hand(index), own.hand.len()),
                (Place::PickingFrom(index), own.drafting.picking_from.len()),
                (Place::DraftKept(index), own.drafting.kept.len()),
                (Place::Dealt(index), own.buying.dealt.len()),
                (Place::CorporationsDealt(index), own.choosing_corporation.dealt.len()),
                (Place::PreludeCardsDealt(index), own.prelude_cards.dealt.len()),
                (Place::PreludeCardsKept(index), own.prelude_cards.kept.len()),
            ]);
        }
        let current_player = base.current_player;
        let paying_for = match base.waiting {
            Some(Waiting::Payment(card)) if current_player != player => Some(card),
            _ => None,
        };
        if let Some(card) = paying_for {
            seen.insert(card);
            places
                .iter_mut()
                .filter(|(place, _)| *place == Place::Hand(current_player))
                .for_each(|(_, count)| *count -= 1);
        }
        if let Some(keeping) = keeping(&mut base) {
            if current_player == player {
                seen = seen.union(keeping.looking_at).union(keeping.kept);
            } else {
                places.extend([
                    (Place::LookingAt, keeping.looking_at.len()),
                    (Place::KeptOfThoseLookedAt, keeping.kept.len()),
                ]);
            }
        }
        places.extend([
            (Place::Deck, base.deck.len()),
            (Place::Discard, base.discard.len()),
            (Place::PreludeDeck, base.prelude_deck.len()),
        ]);
        places.retain(|&(_, count)| count > 0);
        for &(place, _) in &places {
            empty(&mut base, place);
        }
        let prelude = base.settings.prelude;
        let all_prelude_cards: CardSet =
            if prelude { (FIRST_PRELUDE_CARD..CATALOG_CARDS).collect() } else { CardSet::default() };
        let pins = pins(&base, player, seen, &places);
        let pinned: CardSet = pins.iter().flatten().map(|pin| pin.card).collect();
        let pools = [project_cards_with(prelude), corporations_with(prelude), all_prelude_cards]
            .map(|cards| cards.without(seen).without(pinned).iter().collect());
        Sampler { player, base, places, pools, pins, paying_for, restart_buying }
    }

    /// A Sampled Position: the position with the cards the Player can't see dealt at random from
    /// `seed`, which is also the sample's own seed.
    ///
    /// A Decision another Player is in the middle of may need cards they hold: Excentric Sponsor plays
    /// a card from the hand, and is played only with one it can play. Everyone knows that much, so if
    /// the cards dealt leave that Decision with no Option, they are dealt again.
    pub fn sample(&self, seed: u64) -> Game {
        let mut random_numbers = RandomNumbers::new(seed);
        for _ in 0..DEALS {
            let game = self.deal(seed, &mut random_numbers);
            if game.current_player == self.player
                || game.decision().is_none_or(|decision| !decision.options.is_empty())
            {
                return game;
            }
        }
        panic!("no deal of {DEALS} left the Decision in progress with an Option")
    }

    /// The position with the cards the Player can't see dealt from `random_numbers`.
    fn deal(&self, seed: u64, random_numbers: &mut RandomNumbers) -> Game {
        let mut pools = self.pools.clone();
        let mut contents: Vec<Vec<usize>> =
            self.places.iter().map(|&(_, count)| Vec::with_capacity(count)).collect();
        for group in &self.pins {
            let mut group = group.clone();
            random_numbers.shuffle(&mut group);
            for pin in group {
                let room = pin.places.iter().find(|&&place| contents[place].len() < self.places[place].1);
                match room {
                    Some(&place) => contents[place].push(pin.card),
                    None => pools[PROJECT_CARDS].push(pin.card),
                }
            }
        }
        for pool in &mut pools {
            random_numbers.shuffle(pool);
        }
        let mut dealt = [0; KINDS];
        let mut game = self.base.clone();
        for (&(place, count), cards) in self.places.iter().zip(&mut contents) {
            let kind = place.kind();
            let more = count - cards.len();
            cards.extend_from_slice(&pools[kind][dealt[kind]..dealt[kind] + more]);
            dealt[kind] += more;
            put(&mut game, place, cards);
        }
        if let Some(card) = self.paying_for {
            game.players[game.current_player].hand.insert(card);
        }
        game.settings.seed = seed;
        game.settings.deal = None; // A deal would give the hidden cards' real order back.
        game.random_numbers = random_numbers.clone();
        if self.restart_buying {
            game.offer_buying_from(game.index_in_player_order());
        }
        game
    }
}

/// The position without anything of the real Game's past that could tell hidden cards apart: its
/// seed, random numbers, log, Replay and the Draft passes of other Players. Every field is named, so
/// that a field added to the Game must be thought about here.
fn scrubbed(game: &Game, player: usize) -> Game {
    Game {
        settings: game.settings.clone(),
        generation: game.generation,
        phase: game.phase,
        temperature: game.temperature,
        oxygen: game.oxygen,
        board: game.board.clone(),
        deck: game.deck,
        discard: game.discard,
        draft_passes: game.draft_passes.iter().filter(|pass| pass.player == player).copied().collect(),
        players: game.players.clone(),
        first_player: game.first_player,
        current_player: game.current_player,
        actions_this_turn: game.actions_this_turn,
        waiting: game.waiting,
        placing_for: game.placing_for,
        choosing_for: game.choosing_for,
        playing_prelude_card: game.playing_prelude_card,
        discards_to_draw: game.discards_to_draw,
        olympus_conference_due: game.olympus_conference_due,
        viral_enhancing: game.viral_enhancing,
        targeting: game.targeting,
        waiting_bonus: game.waiting_bonus,
        prelude_deck: game.prelude_deck,
        card_resources: game.card_resources,
        adding: game.adding,
        claimed_milestones: game.claimed_milestones,
        funded_awards: game.funded_awards,
        log: Vec::new(),
        random_numbers: RandomNumbers::new(0),
        replay: Replay { start: Start::Sampled, picks: Vec::new() },
    }
}

/// The cards `player` passed in the Draft that aren't among those they see (`seen`), each with the
/// Player they passed it to last, in groups. First the cards they passed last in this Draft, which are
/// exactly those that Player picks from now; then the others passed this Generation, kept in this
/// Draft or dealt to buy from; then those passed in earlier Generations, likeliest in the hand.
/// Wherever it goes first is full, a card goes to the hand, and then anywhere else that Player hides
/// Project Cards.
fn pins(game: &Game, player: usize, seen: CardSet, places: &[(Place, usize)]) -> Vec<Vec<Pin>> {
    let mut groups = vec![Vec::new(), Vec::new(), Vec::new()];
    let mut accounted_for = seen;
    let passes = game.draft_passes.iter().rev().filter(|pass| pass.player == player);
    for (index, pass) in passes.enumerate() {
        let this_generation = pass.generation == game.generation;
        let (group, first) = match game.phase {
            Phase::Draft if this_generation && index == 0 => (0, Place::PickingFrom(pass.to)),
            Phase::Draft if this_generation => (1, Place::DraftKept(pass.to)),
            Phase::Research if this_generation => (1, Place::Dealt(pass.to)),
            _ => (2, Place::Hand(pass.to)),
        };
        let order = [
            first,
            Place::Hand(pass.to),
            Place::Dealt(pass.to),
            Place::DraftKept(pass.to),
            Place::PickingFrom(pass.to),
        ];
        let mut indices = Vec::new();
        for place in order {
            if let Some(index) = places.iter().position(|&(other, _)| other == place)
                && !indices.contains(&index)
            {
                indices.push(index);
            }
        }
        for card in pass.cards.without(accounted_for).iter() {
            groups[group].push(Pin { card, places: indices.clone() });
        }
        accounted_for = accounted_for.union(pass.cards);
    }
    groups
}

/// Takes back what the other Players have chosen in secret so far in this Draft round or buying step:
/// the card they kept in this round, or the Corporation they chose, the Prelude Cards they kept and the
/// cards they bought; and what the current Player, another one, has kept so far of the cards they look
/// at (once they pay for those they buy, everyone sees how many). Those choices are simultaneous at the table, so they are as good made after
/// `player`'s own; whoever plays the sample makes them again. Returns whether the current Player is
/// one of them, buying, who must start again once their cards are dealt.
fn take_back_hidden_choices(game: &mut Game, player: usize) -> bool {
    let (phase, current_player) = (game.phase, game.current_player);
    for (index, own) in game.players.iter_mut().enumerate() {
        if index == player {
            continue;
        }
        if phase == Phase::Draft && own.drafting.picked {
            // One of the cards they kept goes back: which one doesn't matter, as all are dealt again.
            let card = own.drafting.kept.iter().last().expect("a Player who picked kept a card");
            own.drafting.kept.remove(card);
            own.drafting.picking_from.insert(card);
            own.drafting.picked = false;
        }
        if phase.is_buying() {
            own.buying.bought = CardSet::default();
            own.buying.heat = 0;
            own.buying.done = false;
            own.choosing_corporation.picked = None;
            if phase == Phase::Setup {
                own.prelude_cards.kept = PreludeSet::default();
            }
        }
    }
    if let Some(Waiting::KeepCards(keeping)) = &mut game.waiting
        && current_player != player
    {
        keeping.looking_at = keeping.looking_at.union(keeping.kept);
        keeping.keep += keeping.kept.len();
        keeping.kept = CardSet::default();
    }
    let restart_buying = phase.is_buying() && current_player != player;
    if restart_buying {
        game.waiting = None;
    }
    restart_buying
}

/// What the current Player is looking at to keep or buy some of, if they are.
fn keeping(game: &mut Game) -> Option<&mut crate::card_flow::Keeping> {
    match &mut game.waiting {
        Some(Waiting::KeepCards(keeping) | Waiting::Expense(Expense::KeptCards(keeping))) => Some(keeping),
        _ => None,
    }
}

fn prelude_cards(cards: PreludeSet) -> CardSet {
    cards.iter().collect()
}

fn empty(game: &mut Game, place: Place) {
    put(game, place, &[]);
}

/// Puts exactly `cards` in `place`.
fn put(game: &mut Game, place: Place, cards: &[usize]) {
    let set = || cards.iter().copied().collect::<CardSet>();
    let preludes = || cards.iter().copied().collect::<PreludeSet>();
    match place {
        Place::Hand(player) => game.players[player].hand = set(),
        Place::PickingFrom(player) => game.players[player].drafting.picking_from = set(),
        Place::DraftKept(player) => game.players[player].drafting.kept = set(),
        Place::Dealt(player) => game.players[player].buying.dealt = set(),
        Place::LookingAt => keeping(game).expect("someone is looking at cards").looking_at = set(),
        Place::KeptOfThoseLookedAt => keeping(game).expect("someone is looking at cards").kept = set(),
        Place::Deck => game.deck = Deck::from_bottom_up(cards),
        Place::Discard => game.discard = set(),
        Place::CorporationsDealt(player) => game.players[player].choosing_corporation.dealt = set(),
        Place::PreludeCardsDealt(player) => game.players[player].prelude_cards.dealt = preludes(),
        Place::PreludeCardsKept(player) => game.players[player].prelude_cards.kept = preludes(),
        Place::PreludeDeck => game.prelude_deck = preludes(),
    }
}
