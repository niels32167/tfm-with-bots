//! The Tharsis board: every Area, what it is reserved for, its placement bonus, and the
//! Tiles placed on it so far.
//!
//! Areas are indexed from 0: the 61 Areas on Mars row by row from the top and each row
//! from the left, then the two Areas off Mars. People know them by name instead. Rows are
//! lettered A to J, skipping I, as the open-source game labels them, so "E3" is the third
//! Area of the fifth row: Noctis City.

use std::sync::LazyLock;

use serde::{Deserialize, Serialize};

use crate::cards::CARD_CATALOG;
use crate::resources::Resource;

/// How many Areas each row of Mars has, from the top.
const ROW_LENGTHS: [usize; 9] = [5, 6, 7, 8, 9, 8, 7, 6, 5];
const ROW_LETTERS: [char; 9] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J'];
/// The length of the widest row. The other rows are centred under it.
const WIDEST_ROW: usize = 9;

pub const AREAS_ON_MARS: usize = 61;
/// The Areas on Mars plus the two off Mars (Phobos Space Haven and Ganymede Colony).
pub const AREA_COUNT: usize = AREAS_ON_MARS + 2;

/// One item of a placement bonus.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BonusItem {
    Steel,
    Titanium,
    Plant,
    Card,
}

impl BonusItem {
    pub const ALL: [BonusItem; 4] =
        [BonusItem::Steel, BonusItem::Titanium, BonusItem::Plant, BonusItem::Card];

    /// The Resource it gives, or None for a card.
    pub fn resource(self) -> Option<Resource> {
        match self {
            BonusItem::Steel => Some(Resource::Steel),
            BonusItem::Titanium => Some(Resource::Titanium),
            BonusItem::Plant => Some(Resource::Plants),
            BonusItem::Card => None,
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            BonusItem::Steel => "steel",
            BonusItem::Titanium => "titanium",
            BonusItem::Plant => "plant",
            BonusItem::Card => "card",
        }
    }
}

/// What an Area is kept for: Oceans, or one card's Tile.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reservation {
    Ocean,
    NoctisCity,
    PhobosSpaceHaven,
    GanymedeColony,
}

impl Reservation {
    pub fn name(self) -> &'static str {
        match self {
            Reservation::Ocean => "ocean",
            Reservation::NoctisCity => "noctis_city",
            Reservation::PhobosSpaceHaven => "phobos_space_haven",
            Reservation::GanymedeColony => "ganymede_colony",
        }
    }
}

/// What is printed on an Area.
pub struct PrintedArea {
    /// The name printed on it, if any: Noctis City, the four volcanoes, and the Areas off Mars.
    pub name: Option<&'static str>,
    pub reserved: Option<Reservation>,
    pub bonus: &'static [BonusItem],
}

const fn land(bonus: &'static [BonusItem]) -> PrintedArea {
    PrintedArea { name: None, reserved: None, bonus }
}

const fn ocean(bonus: &'static [BonusItem]) -> PrintedArea {
    PrintedArea { name: None, reserved: Some(Reservation::Ocean), bonus }
}

const fn volcano(name: &'static str, bonus: &'static [BonusItem]) -> PrintedArea {
    PrintedArea { name: Some(name), reserved: None, bonus }
}

const fn reserved(name: &'static str, reservation: Reservation, bonus: &'static [BonusItem]) -> PrintedArea {
    PrintedArea { name: Some(name), reserved: Some(reservation), bonus }
}

use BonusItem::{Card as C, Plant as P, Steel as S, Titanium as T};

/// The printed Tharsis board, checked against the official board and the open-source game's.
#[rustfmt::skip]
static AREAS: [PrintedArea; AREA_COUNT] = [
    // Row A
    land(&[S, S]), ocean(&[S, S]), land(&[]), ocean(&[C]), ocean(&[]),
    // Row B
    land(&[]), volcano("Tharsis Tholus", &[S]), land(&[]), land(&[]), land(&[]), ocean(&[C, C]),
    // Row C
    volcano("Ascraeus Mons", &[C]), land(&[]), land(&[]), land(&[]), land(&[]), land(&[]), land(&[S]),
    // Row D
    volcano("Pavonis Mons", &[P, T]), land(&[P]), land(&[P]), land(&[P]), land(&[P, P]), land(&[P]), land(&[P]),
    ocean(&[P, P]),
    // Row E
    volcano("Arsia Mons", &[P, P]), land(&[P, P]), reserved("Noctis City", Reservation::NoctisCity, &[P, P]),
    ocean(&[P, P]), ocean(&[P, P]), ocean(&[P, P]), land(&[P, P]), land(&[P, P]), land(&[P, P]),
    // Row F
    land(&[P]), land(&[P, P]), land(&[P]), land(&[P]), land(&[P]), ocean(&[P]), ocean(&[P]), ocean(&[P]),
    // Row G
    land(&[]), land(&[]), land(&[]), land(&[]), land(&[]), land(&[P]), land(&[]),
    // Row H
    land(&[S, S]), land(&[]), land(&[C]), land(&[C]), land(&[]), land(&[T]),
    // Row J
    land(&[S]), land(&[S, S]), land(&[]), land(&[]), ocean(&[T, T]),
    // Off Mars
    reserved("Phobos Space Haven", Reservation::PhobosSpaceHaven, &[]),
    reserved("Ganymede Colony", Reservation::GanymedeColony, &[]),
];

pub fn printed(area: usize) -> &'static PrintedArea {
    &AREAS[area]
}

/// The Resource whose Production a mining Tile on `area` raises (Mining Area, Mining Rights): the
/// steel or titanium of its placement bonus, if it has one. No Area of the Tharsis board has both.
pub fn mining_resource(area: usize) -> Option<Resource> {
    let bonus = printed(area).bonus;
    [BonusItem::Steel, BonusItem::Titanium]
        .into_iter()
        .find(|item| bonus.contains(item))
        .and_then(BonusItem::resource)
}

/// Where an Area is on Mars, as (row, position) counted from 0, or None off Mars.
pub fn row_and_position(area: usize) -> Option<(usize, usize)> {
    let mut first_in_row = 0;
    for (row, length) in ROW_LENGTHS.into_iter().enumerate() {
        if area < first_in_row + length {
            return Some((row, area - first_in_row));
        }
        first_in_row += length;
    }
    None
}

/// The Areas next to each Area, worked out once. Legal Areas and placement bonuses ask for
/// them all the time, and reading them from here made Random Bot playouts about 20 %
/// faster than working them out each time (measured in ticket 06).
static ADJACENT_AREAS: LazyLock<[[Option<usize>; 6]; AREA_COUNT]> =
    LazyLock::new(|| std::array::from_fn(work_out_adjacent_areas));

/// The Areas next to `area`. Areas off Mars have none.
pub fn adjacent_areas(area: usize) -> impl Iterator<Item = usize> {
    ADJACENT_AREAS[area].into_iter().flatten()
}

/// The (up to six) Areas next to `area`, for `ADJACENT_AREAS`.
fn work_out_adjacent_areas(area: usize) -> [Option<usize>; 6] {
    // Counted in half-Areas from the left edge of the widest row, an Area's neighbours in
    // the rows above and below are one half-Area to either side, and those in its own row two.
    const NEIGHBOURS: [(isize, isize); 6] = [(-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1)];
    match row_and_position(area) {
        Some((row, position)) => {
            let (row, column) = (row as isize, half_column(row, position));
            NEIGHBOURS.map(|(rows, columns)| area_at(row + rows, column + columns))
        }
        None => [None; 6],
    }
}

fn half_column(row: usize, position: usize) -> isize {
    (2 * position + WIDEST_ROW - ROW_LENGTHS[row]) as isize
}

/// The Area on Mars at `row` and `half_column` (see `adjacent_areas`), if there is one.
fn area_at(row: isize, half_column: isize) -> Option<usize> {
    if row < 0 || row >= ROW_LENGTHS.len() as isize {
        return None;
    }
    let row = row as usize;
    let from_left = half_column - (WIDEST_ROW - ROW_LENGTHS[row]) as isize;
    if from_left < 0 || from_left % 2 != 0 {
        return None;
    }
    let position = (from_left / 2) as usize;
    if position >= ROW_LENGTHS[row] {
        return None;
    }
    let first_in_row: usize = ROW_LENGTHS[..row].iter().sum();
    Some(first_in_row + position)
}

/// The Areas on Mars reserved for nothing, the Areas reserved for Oceans and the Areas reserved for
/// a card's City, each in board order, worked out once: a placement looks only at those its Tile
/// could go on. (Looking at all 63 Areas made Random Bot playouts about 9 % slower, measured in
/// ticket 18.)
static LAND: LazyLock<Vec<usize>> =
    LazyLock::new(|| (0..AREAS_ON_MARS).filter(|&area| printed(area).reserved.is_none()).collect());
static OCEAN_AREAS: LazyLock<Vec<usize>> =
    LazyLock::new(|| areas_reserved_for(|reserved| reserved == Some(Reservation::Ocean)));
static CARDS_AREAS: LazyLock<Vec<usize>> = LazyLock::new(|| {
    areas_reserved_for(|reserved| reserved.is_some_and(|reservation| reservation != Reservation::Ocean))
});

/// Every Area, on Mars or off it, whose reservation is `wanted`.
fn areas_reserved_for(wanted: fn(Option<Reservation>) -> bool) -> Vec<usize> {
    (0..AREA_COUNT).filter(|&area| wanted(printed(area).reserved)).collect()
}

/// The Areas `placement` could go on, whatever is on the board: the Areas reserved for Oceans, a
/// card's reserved Area among those reserved for a card's City, or else the land on Mars.
fn candidate_areas(placement: Placement) -> &'static [usize] {
    match (placement.on, placement.tile) {
        (Areas::ReservedForOceans, _) | (Areas::Usual, TileKind::Ocean) => &OCEAN_AREAS,
        (Areas::NoctisCity | Areas::PhobosSpaceHaven | Areas::GanymedeColony, _) => &CARDS_AREAS,
        _ => &LAND,
    }
}

/// The name people use for an Area: "E3" on Mars, or "phobos_space_haven" off Mars.
pub fn area_id(area: usize) -> String {
    match row_and_position(area) {
        Some((row, position)) => format!("{}{}", ROW_LETTERS[row], position + 1),
        None => printed(area).name.unwrap_or_default().to_lowercase().replace(' ', "_"),
    }
}

/// The Area people call `id` ("E3", "phobos_space_haven"), if there is one.
pub fn find_area(id: &str) -> Option<usize> {
    (0..AREA_COUNT).find(|&area| area_id(area) == id)
}

/// How an Area is written in labels and the game log: "E5", with its printed name if it
/// has one, "E3 (Noctis City)", and off Mars just its name.
pub fn area_label(area: usize) -> String {
    match (row_and_position(area), printed(area).name) {
        (Some(_), None) => area_id(area),
        (Some(_), Some(name)) => format!("{} ({name})", area_id(area)),
        (None, name) => name.unwrap_or_default().to_string(),
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TileKind {
    Ocean,
    Greenery,
    City,
    /// A Tile printed with its card's symbol, other than Capital's City (see `SpecialTile`).
    Special,
}

impl TileKind {
    pub fn name(self) -> &'static str {
        match self {
            TileKind::Ocean => "Ocean",
            TileKind::Greenery => "Greenery",
            TileKind::City => "City",
            TileKind::Special => "special Tile",
        }
    }

    /// As a sentence names it: "an Ocean", "a Greenery", "a City".
    pub fn with_article(self) -> String {
        let article = if self == TileKind::Ocean { "an" } else { "a" };
        format!("{article} {}", self.name())
    }
}

/// The card whose symbol a special Tile is printed with. Each is a Tile of its own kind, but
/// Capital's is a City as well, and counts as one wherever a City does.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SpecialTile {
    Capital,
    NaturalPreserve,
    MiningArea,
    MiningRights,
    CommercialDistrict,
    NuclearZone,
    IndustrialCenter,
    LavaFlows,
    MoholeArea,
    RestrictedArea,
    EcologicalZone,
}

impl SpecialTile {
    /// In card-number order.
    pub const ALL: [SpecialTile; 11] = [
        SpecialTile::Capital,
        SpecialTile::NaturalPreserve,
        SpecialTile::MiningArea,
        SpecialTile::MiningRights,
        SpecialTile::CommercialDistrict,
        SpecialTile::NuclearZone,
        SpecialTile::IndustrialCenter,
        SpecialTile::EcologicalZone,
        SpecialTile::LavaFlows,
        SpecialTile::MoholeArea,
        SpecialTile::RestrictedArea,
    ];

    /// Its card's index in the card catalog, which checks it against the card's id when read.
    pub const fn card(self) -> usize {
        match self {
            SpecialTile::Capital => 7,
            SpecialTile::NaturalPreserve => 43,
            SpecialTile::MiningArea => 63,
            SpecialTile::MiningRights => 66,
            SpecialTile::CommercialDistrict => 84,
            SpecialTile::NuclearZone => 96,
            SpecialTile::IndustrialCenter => 122,
            SpecialTile::EcologicalZone => 127,
            SpecialTile::LavaFlows => 139,
            SpecialTile::MoholeArea => 141,
            SpecialTile::RestrictedArea => 198,
        }
    }

    /// The special Tile `card` places, if it places one.
    pub fn of_card(card: usize) -> Option<SpecialTile> {
        SpecialTile::ALL.into_iter().find(|tile| tile.card() == card)
    }

    /// How labels and the game log name it: "the Nuclear Zone Tile".
    pub fn name(self) -> String {
        format!("the {} Tile", CARD_CATALOG[self.card()].name)
    }
}

/// Which Areas a Tile may go on.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Areas {
    /// Those the rules give its kind of Tile.
    #[default]
    Usual,
    /// Any free Area reserved for Oceans, whatever is next to it, as for Mangrove's Greenery.
    #[serde(rename = "ocean_areas")]
    ReservedForOceans,
    /// Any free Area on Mars reserved for nothing, whatever is next to it, as for Artificial
    /// Lake's Ocean.
    Land,
    /// Any free Area on Mars reserved for nothing and next to at least 2 Cities, as for
    /// Urbanized Area's City.
    NextToTwoCities,
    /// Any free Area on Mars reserved for nothing and next to no Tile at all, as for Research
    /// Outpost's City.
    NextToNoOtherTile,
    /// Any free Area on Mars reserved for nothing and next to a City, as for Industrial Center's
    /// Tile.
    NextToACity,
    /// Any free Area on Mars reserved for nothing and next to a Greenery, whoever owns it, as for
    /// Ecological Zone's Tile.
    NextToAGreenery,
    /// Any free volcano: Tharsis Tholus, Ascraeus Mons, Pavonis Mons or Arsia Mons, as for Lava
    /// Flows' Tile.
    Volcanoes,
    /// Any free Area on Mars reserved for nothing, with a steel or titanium placement bonus, as
    /// for Mining Rights' Tile.
    SteelOrTitaniumBonus,
    /// Like `SteelOrTitaniumBonus`, but next to one of its owner's Tiles, as for Mining Area's.
    SteelOrTitaniumBonusNextToOwnTile,
    /// The Area reserved for Noctis City's City, whatever is next to it.
    NoctisCity,
    /// The Area off Mars reserved for Phobos Space Haven's City.
    PhobosSpaceHaven,
    /// The Area off Mars reserved for Ganymede Colony's City.
    GanymedeColony,
}

impl Areas {
    pub fn is_usual(&self) -> bool {
        *self == Areas::Usual
    }

    /// The card's reserved Area these are, if they are one.
    fn reservation(self) -> Option<Reservation> {
        match self {
            Areas::NoctisCity => Some(Reservation::NoctisCity),
            Areas::PhobosSpaceHaven => Some(Reservation::PhobosSpaceHaven),
            Areas::GanymedeColony => Some(Reservation::GanymedeColony),
            _ => None,
        }
    }
}

/// A Tile to place, and the Areas it may go on. Effect data writes the usual Areas as the Tile
/// alone, `"city"`, and others as `{"tile": "greenery", "on": "ocean_areas"}`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(from = "WrittenPlacement", into = "WrittenPlacement")]
pub struct Placement {
    pub tile: TileKind,
    pub on: Areas,
    /// The card's symbol it is printed with, for a special Tile: effect data leaves it out, and
    /// the card being played fills it in.
    pub special: Option<SpecialTile>,
}

impl Placement {
    /// `tile` on the usual Areas for it.
    pub fn usual(tile: TileKind) -> Placement {
        Placement { tile, on: Areas::Usual, special: None }
    }

    /// How labels name the Tile: "the City", or "the Nuclear Zone Tile".
    pub fn tile_name(&self) -> String {
        match self.special {
            Some(special) => special.name(),
            None => format!("the {}", self.tile.name()),
        }
    }
}

/// How effect data writes a Placement.
#[derive(Clone, Copy, Serialize, Deserialize)]
#[serde(untagged, deny_unknown_fields)]
enum WrittenPlacement {
    Usual(TileKind),
    On { tile: TileKind, on: Areas },
}

impl From<WrittenPlacement> for Placement {
    fn from(written: WrittenPlacement) -> Placement {
        match written {
            WrittenPlacement::Usual(tile) => Placement::usual(tile),
            WrittenPlacement::On { tile, on } => Placement { tile, on, special: None },
        }
    }
}

impl From<Placement> for WrittenPlacement {
    fn from(placement: Placement) -> WrittenPlacement {
        match placement.on {
            Areas::Usual => WrittenPlacement::Usual(placement.tile),
            on => WrittenPlacement::On { tile: placement.tile, on },
        }
    }
}

/// A Tile on the board. Oceans belong to nobody.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Tile {
    pub kind: TileKind,
    pub owner: Option<usize>,
    /// The card's symbol it is printed with, for a special Tile.
    pub special: Option<SpecialTile>,
}

/// An Area that one Player has claimed with Land Claim: only they may place a Tile there.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Claim {
    pub area: usize,
    /// The Player who claimed it, and the only one who may place a Tile on it.
    pub player: usize,
}

/// The Tiles on the board, by Area, and the Area claimed with Land Claim.
#[derive(Clone, Debug)]
pub struct Board {
    tiles: [Option<Tile>; AREA_COUNT],
    /// There is one Land Claim card, so at most one Area is ever claimed.
    claim: Option<Claim>,
}

impl Board {
    pub fn new() -> Board {
        Board { tiles: [None; AREA_COUNT], claim: None }
    }

    /// The Area claimed with Land Claim, once it is played.
    pub fn claim(&self) -> Option<Claim> {
        self.claim
    }

    /// `player` claims `area` with Land Claim.
    pub fn claim_area(&mut self, area: usize, player: usize) {
        self.claim = Some(Claim { area, player });
    }

    /// The Areas Land Claim may claim, in board order: the free Areas on Mars reserved for nothing
    /// that nobody has claimed.
    pub fn claimable_areas(&self) -> impl Iterator<Item = usize> {
        (0..AREAS_ON_MARS).filter(|&area| {
            printed(area).reserved.is_none()
                && self.tiles[area].is_none()
                && self.claim.is_none_or(|claim| claim.area != area)
        })
    }

    pub fn tile(&self, area: usize) -> Option<Tile> {
        self.tiles[area]
    }

    /// How many Ocean Tiles have been placed.
    pub fn oceans(&self) -> usize {
        self.in_play(TileKind::Ocean)
    }

    /// How many Tiles of `kind` are on the board, whoever owns them.
    pub fn in_play(&self, kind: TileKind) -> usize {
        self.tiles.iter().flatten().filter(|tile| tile.kind == kind).count()
    }

    /// How many Tiles of `kind` are on Mars, whoever owns them.
    pub fn on_mars(&self, kind: TileKind) -> usize {
        self.tiles[..AREAS_ON_MARS].iter().flatten().filter(|tile| tile.kind == kind).count()
    }

    /// How many Tiles of `kind` are next to `area`.
    pub fn adjacent(&self, area: usize, kind: TileKind) -> usize {
        adjacent_areas(area).filter(|&next| self.tiles[next].is_some_and(|tile| tile.kind == kind)).count()
    }

    /// The Area of the special Tile printed with `special`'s symbol, once it is placed.
    pub fn area_of(&self, special: SpecialTile) -> Option<usize> {
        (0..AREA_COUNT).find(|&area| self.tiles[area].is_some_and(|tile| tile.special == Some(special)))
    }

    /// The Areas of `player`'s Tiles, in board order, with each Tile's kind.
    pub fn tiles_of(&self, player: usize) -> impl Iterator<Item = (usize, TileKind)> {
        (0..AREA_COUNT).filter_map(move |area| match self.tiles[area] {
            Some(tile) if tile.owner == Some(player) => Some((area, tile.kind)),
            _ => None,
        })
    }

    /// How many Tiles of `kind` `player` owns.
    pub fn owned(&self, player: usize, kind: TileKind) -> usize {
        self.tiles_of(player).filter(|&(_, each)| each == kind).count()
    }

    pub fn place(&mut self, area: usize, tile: Tile) {
        self.tiles[area] = Some(tile);
    }

    /// Every Area where `player` may make `placement`, in board order.
    pub fn areas_for(&self, placement: Placement, player: usize) -> Vec<usize> {
        let candidates = candidate_areas(placement).iter().copied();
        let areas: Vec<usize> = candidates.filter(|&area| self.allows(placement, player, area)).collect();
        if placement != Placement::usual(TileKind::Greenery) {
            return areas;
        }
        // A Greenery must go next to one of its owner's Tiles if it can.
        let next_to_own: Vec<usize> =
            areas.iter().copied().filter(|&area| self.next_to_a_tile_of(player, area)).collect();
        if next_to_own.is_empty() { areas } else { next_to_own }
    }

    /// Whether there is any Area where `player` may make `placement`: the same as `areas_for` not
    /// being empty, but quicker, as it stops at the first one. With no free Area next to its
    /// owner's Tiles, a Greenery may go on any free land.
    pub fn has_area_for(&self, placement: Placement, player: usize) -> bool {
        candidate_areas(placement).iter().any(|&area| self.allows(placement, player, area))
    }

    /// Whether `player` may make `placement` on `area`, one of its `candidate_areas`, leaving aside
    /// that a Greenery must go next to its owner's Tiles if it can. Land claimed by another Player
    /// is never theirs to use.
    fn allows(&self, placement: Placement, player: usize, area: usize) -> bool {
        if self.tiles[area].is_some() {
            return false;
        }
        if self.claim.is_some_and(|claim| claim.area == area && claim.player != player) {
            return false;
        }
        match (placement.on, placement.tile) {
            (Areas::ReservedForOceans, _)
            | (Areas::Usual, TileKind::Ocean)
            // A special Tile has no placement restriction but those its card prints.
            | (Areas::Land, _)
            | (Areas::Usual, TileKind::Greenery | TileKind::Special) => true,
            (Areas::Usual, TileKind::City) => !self.next_to_a_city(area),
            (Areas::NextToTwoCities, _) => self.adjacent(area, TileKind::City) >= 2,
            (Areas::NextToNoOtherTile, _) => adjacent_areas(area).all(|next| self.tiles[next].is_none()),
            (Areas::NextToACity, _) => self.next_to_a_city(area),
            (Areas::NextToAGreenery, _) => self.adjacent(area, TileKind::Greenery) > 0,
            // The four volcanoes are the Areas on Mars with a printed name but reserved for nothing.
            (Areas::Volcanoes, _) => printed(area).name.is_some(),
            (Areas::SteelOrTitaniumBonus, _) => mining_resource(area).is_some(),
            (Areas::SteelOrTitaniumBonusNextToOwnTile, _) => {
                mining_resource(area).is_some() && self.next_to_a_tile_of(player, area)
            }
            (Areas::NoctisCity | Areas::PhobosSpaceHaven | Areas::GanymedeColony, _) => {
                printed(area).reserved == placement.on.reservation()
            }
        }
    }

    fn next_to_a_city(&self, area: usize) -> bool {
        adjacent_areas(area).any(|next| self.tiles[next].is_some_and(|tile| tile.kind == TileKind::City))
    }

    fn next_to_a_tile_of(&self, player: usize, area: usize) -> bool {
        adjacent_areas(area).any(|next| self.tiles[next].is_some_and(|tile| tile.owner == Some(player)))
    }
}
