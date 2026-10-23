//! The Tharsis board: every Area, what it is reserved for, its placement bonus, and the
//! Tiles placed on it so far.
//!
//! Areas are indexed from 0: the 61 Areas on Mars row by row from the top and each row
//! from the left, then the two Areas off Mars. People know them by name instead. Rows are
//! lettered A to J, skipping I, as the open-source game labels them, so "E3" is the third
//! Area of the fifth row: Noctis City.

use serde::{Deserialize, Serialize};

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

/// The Areas next to `area`. Areas off Mars have none.
pub fn adjacent_areas(area: usize) -> impl Iterator<Item = usize> {
    // Counted in half-Areas from the left edge of the widest row, an Area's neighbours in
    // the rows above and below are one half-Area to either side, and those in its own row two.
    const NEIGHBOURS: [(isize, isize); 6] = [(-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1)];
    let neighbours = match row_and_position(area) {
        Some((row, position)) => {
            let (row, column) = (row as isize, half_column(row, position));
            NEIGHBOURS.map(|(rows, columns)| area_at(row + rows, column + columns))
        }
        None => [None; 6],
    };
    neighbours.into_iter().flatten()
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
}

impl TileKind {
    pub fn name(self) -> &'static str {
        match self {
            TileKind::Ocean => "Ocean",
            TileKind::Greenery => "Greenery",
            TileKind::City => "City",
        }
    }

    /// As a sentence names it: "an Ocean", "a Greenery", "a City".
    pub fn with_article(self) -> String {
        let article = if self == TileKind::Ocean { "an" } else { "a" };
        format!("{article} {}", self.name())
    }
}

/// A Tile on the board. Oceans belong to nobody.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Tile {
    pub kind: TileKind,
    pub owner: Option<usize>,
}

/// The Tiles on the board, by Area.
#[derive(Clone, Debug)]
pub struct Board {
    tiles: [Option<Tile>; AREA_COUNT],
}

impl Board {
    pub fn new() -> Board {
        Board { tiles: [None; AREA_COUNT] }
    }

    pub fn tile(&self, area: usize) -> Option<Tile> {
        self.tiles[area]
    }

    /// How many Ocean Tiles have been placed.
    pub fn oceans(&self) -> usize {
        self.tiles.iter().flatten().filter(|tile| tile.kind == TileKind::Ocean).count()
    }

    /// How many Tiles of `kind` are next to `area`.
    pub fn adjacent(&self, area: usize, kind: TileKind) -> usize {
        adjacent_areas(area).filter(|&next| self.tiles[next].is_some_and(|tile| tile.kind == kind)).count()
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

    /// Every Area where `player` may place `tile`, in board order.
    pub fn areas_for(&self, tile: TileKind, player: usize) -> Vec<usize> {
        match tile {
            TileKind::Ocean => self.free_ocean_areas().collect(),
            TileKind::Greenery => {
                // A Greenery must go next to one of its owner's Tiles if it can.
                let next_to_own: Vec<usize> =
                    self.free_land().filter(|&area| self.next_to_a_tile_of(player, area)).collect();
                if next_to_own.is_empty() { self.free_land().collect() } else { next_to_own }
            }
            TileKind::City => self.city_areas().collect(),
        }
    }

    /// Whether there is any Area for `tile`: the same as `areas_for` not being empty, but
    /// quicker, as it stops at the first one.
    pub fn has_area_for(&self, tile: TileKind) -> bool {
        match tile {
            TileKind::Ocean => self.free_ocean_areas().next().is_some(),
            // With no free Area next to its owner's Tiles, a Greenery may go on any free land.
            TileKind::Greenery => self.free_land().next().is_some(),
            TileKind::City => self.city_areas().next().is_some(),
        }
    }

    fn free_ocean_areas(&self) -> impl Iterator<Item = usize> {
        (0..AREAS_ON_MARS)
            .filter(|&area| printed(area).reserved == Some(Reservation::Ocean) && self.tiles[area].is_none())
    }

    /// The free Areas on Mars that are reserved for nothing.
    fn free_land(&self) -> impl Iterator<Item = usize> {
        (0..AREAS_ON_MARS).filter(|&area| printed(area).reserved.is_none() && self.tiles[area].is_none())
    }

    fn city_areas(&self) -> impl Iterator<Item = usize> {
        self.free_land().filter(|&area| !self.next_to_a_city(area))
    }

    fn next_to_a_city(&self, area: usize) -> bool {
        adjacent_areas(area).any(|next| self.tiles[next].is_some_and(|tile| tile.kind == TileKind::City))
    }

    fn next_to_a_tile_of(&self, player: usize, area: usize) -> bool {
        adjacent_areas(area).any(|next| self.tiles[next].is_some_and(|tile| tile.owner == Some(player)))
    }
}
