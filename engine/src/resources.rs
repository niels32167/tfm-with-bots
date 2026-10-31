//! The six Resources a Player stockpiles, and an amount of each: used both for what a
//! Player holds and for their Production.

use std::ops::{Index, IndexMut};

use serde::{Deserialize, Serialize};

/// MegaCredit Production may go down to -5; every other Production stays at 0 or above.
pub const MIN_MEGACREDIT_PRODUCTION: i32 = -5;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Resource {
    #[serde(rename = "megacredits")]
    MegaCredits,
    Steel,
    Titanium,
    Plants,
    Energy,
    Heat,
}

impl Resource {
    /// In the order printed on the player board.
    pub const ALL: [Resource; 6] = [
        Resource::MegaCredits,
        Resource::Steel,
        Resource::Titanium,
        Resource::Plants,
        Resource::Energy,
        Resource::Heat,
    ];

    /// "1 plant", "2 plants", "3 MegaCredits", "4 steel".
    pub fn counted(self, amount: i32) -> String {
        let plural = match self {
            Resource::MegaCredits | Resource::Plants if amount != 1 => "s",
            _ => "",
        };
        format!("{amount} {}{plural}", self.name())
    }

    /// The lowest its Production may go.
    pub fn min_production(self) -> i32 {
        if self == Resource::MegaCredits { MIN_MEGACREDIT_PRODUCTION } else { 0 }
    }

    /// Its name in the singular, as in "MegaCredit Production" or "plant Production".
    pub fn name(self) -> &'static str {
        match self {
            Resource::MegaCredits => "MegaCredit",
            Resource::Steel => "steel",
            Resource::Titanium => "titanium",
            Resource::Plants => "plant",
            Resource::Energy => "energy",
            Resource::Heat => "heat",
        }
    }
}

/// An amount of each Resource.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Resources {
    pub megacredits: i32,
    pub steel: i32,
    pub titanium: i32,
    pub plants: i32,
    pub energy: i32,
    pub heat: i32,
}

impl Resources {
    /// Each amount `times` over.
    pub fn times(self, times: i32) -> Resources {
        let mut multiplied = self;
        for resource in Resource::ALL {
            multiplied[resource] *= times;
        }
        multiplied
    }
}

impl Index<Resource> for Resources {
    type Output = i32;

    fn index(&self, resource: Resource) -> &i32 {
        match resource {
            Resource::MegaCredits => &self.megacredits,
            Resource::Steel => &self.steel,
            Resource::Titanium => &self.titanium,
            Resource::Plants => &self.plants,
            Resource::Energy => &self.energy,
            Resource::Heat => &self.heat,
        }
    }
}

impl IndexMut<Resource> for Resources {
    fn index_mut(&mut self, resource: Resource) -> &mut i32 {
        match resource {
            Resource::MegaCredits => &mut self.megacredits,
            Resource::Steel => &mut self.steel,
            Resource::Titanium => &mut self.titanium,
            Resource::Plants => &mut self.plants,
            Resource::Energy => &mut self.energy,
            Resource::Heat => &mut self.heat,
        }
    }
}
