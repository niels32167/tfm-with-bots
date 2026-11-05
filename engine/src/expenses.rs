//! What a Player spends MegaCredits on besides a card and a card's action: Standard Projects,
//! Milestones, Awards and cards bought. Each costs MegaCredits and nothing else, but with Helion, heat
//! may pay them too, so each may ask how to pay.

use crate::board::{Areas, Placement, TileKind};
use crate::card_flow::{CARD_PRICE, Keeping};
use crate::game::{DecisionOption, Game, StandardProject, Waiting};
use crate::log::LogEvent;
use crate::milestones_and_awards::{Award, MILESTONE_COST, Milestone};
use crate::playing_cards::Payment;
use crate::resources::Resource;
use crate::triggers::Happened;

/// Something the current Player pays for, as an Action or for the cards they buy.
#[derive(Clone, Copy, Debug)]
pub enum Expense {
    StandardProject(StandardProject),
    Milestone(Milestone),
    /// Funding `award`, the price of the next Award funded being `cost`.
    Award {
        award: Award,
        cost: i32,
    },
    /// The cards they bought in a Research phase. Nothing is paid until every Player is done buying,
    /// but they say now how they will pay.
    BoughtCards,
    /// The cards they buy of those they are looking at.
    KeptCards(Keeping),
}

impl Game {
    /// What `expense` costs the current Player.
    pub fn expense_cost(&self, expense: Expense) -> i32 {
        let player = self.current_player;
        match expense {
            Expense::StandardProject(project) => self.standard_project_cost(player, project),
            Expense::Milestone(_) => MILESTONE_COST,
            Expense::Award { cost, .. } => cost,
            Expense::BoughtCards => CARD_PRICE * self.players[player].buying.bought.len() as i32,
            Expense::KeptCards(keeping) => keeping.price * keeping.kept.len() as i32,
        }
    }

    /// `expense` as a label writes it: "the Asteroid Standard Project", "2 cards".
    pub fn expense_text(&self, expense: Expense) -> String {
        let cards = |count: i32| format!("{count} card{}", if count == 1 { "" } else { "s" });
        match expense {
            Expense::StandardProject(project) => format!("the {} Standard Project", project.name()),
            Expense::Milestone(milestone) => format!("the {} Milestone", milestone.name()),
            Expense::Award { award, .. } => format!("the {} Award", award.name()),
            Expense::BoughtCards => cards(self.players[self.current_player].buying.bought.len() as i32),
            Expense::KeptCards(keeping) => cards(keeping.kept.len() as i32),
        }
    }

    /// Every way the current Player may pay for `expense`, the most MegaCredits first.
    fn expense_payments(&self, expense: Expense) -> Vec<Payment> {
        let player = self.current_player;
        self.ways_to_pay(player, self.expense_cost(expense), 0, 0, self.usable_heat(player, 0))
    }

    /// Every way the current Player may pay for `expense`, as Options.
    pub(crate) fn expense_options(&self, expense: Expense) -> Vec<DecisionOption> {
        self.expense_payments(expense).into_iter().map(DecisionOption::PayExpense).collect()
    }

    /// The current Player pays for `expense`, asked how if there is more than one way, and it is
    /// carried out. Without heat to pay with, the only way is MegaCredits, known without listing them,
    /// which a Random Bot's Game does thousands of times a second.
    pub(crate) fn spend_on(&mut self, expense: Expense) {
        if self.usable_heat(self.current_player, 0) == 0 {
            let megacredits = self.expense_cost(expense);
            return self.carry_out_expense(expense, Payment { megacredits, ..Payment::NOTHING });
        }
        match self.expense_payments(expense)[..] {
            [only_way] => self.carry_out_expense(expense, only_way),
            _ => self.wait_on(Waiting::Expense(expense)),
        }
    }

    /// The current Player pays for the expense they were asked about, in the way they chose.
    pub(crate) fn pay_expense(&mut self, payment: Payment) {
        let Some(Waiting::Expense(expense)) = self.waiting.take() else {
            panic!("only a Player asked how to pay for something pays for it")
        };
        self.carry_out_expense(expense, payment);
    }

    fn carry_out_expense(&mut self, expense: Expense, payment: Payment) {
        let player = self.current_player;
        if let Expense::BoughtCards = expense {
            self.players[player].buying.heat = payment.heat;
            return self.next_player_buys();
        }
        self.pay(player, payment);
        match expense {
            Expense::StandardProject(project) => {
                let cost = self.standard_project_cost(player, project);
                self.log.push(LogEvent::UsedStandardProject { player, project, cost });
                self.log_heat_paid(player, payment.heat);
                self.set_off(Happened::StandardProject { player, project });
                self.carry_out_standard_project(player, project);
            }
            Expense::Milestone(milestone) => {
                self.claimed_milestones[milestone.index()] = Some(player);
                self.log.push(LogEvent::ClaimedMilestone { player, milestone });
                self.log_heat_paid(player, payment.heat);
                self.finish_unless_placing();
            }
            Expense::Award { award, cost } => {
                self.funded_awards[award.index()] = Some(player);
                self.log.push(LogEvent::FundedAward { player, award, cost });
                self.log_heat_paid(player, payment.heat);
                self.finish_unless_placing();
            }
            Expense::BoughtCards => unreachable!("the cards bought are paid for once every Player is done"),
            Expense::KeptCards(keeping) => self.keep_cards_paid_for(keeping, payment.heat),
        }
    }

    /// If `heat` paid part of what `player` just paid for, the log says so.
    pub(crate) fn log_heat_paid(&mut self, player: usize, heat: i32) {
        if heat > 0 {
            self.log.push(LogEvent::PaidWithHeat { player, heat });
        }
    }

    /// `player`, having paid for `project`, carries it out.
    fn carry_out_standard_project(&mut self, player: usize, project: StandardProject) {
        match project {
            StandardProject::SellPatents => unreachable!("Sell Patents begins with the cards to sell"),
            StandardProject::PowerPlant => self.change_production(player, Resource::Energy, 1),
            StandardProject::Asteroid => self.raise_temperature(player),
            StandardProject::Aquifer => self.place_ocean(Areas::Usual),
            StandardProject::Greenery => self.place(Placement::usual(TileKind::Greenery)),
            StandardProject::City => {
                self.change_production(player, Resource::MegaCredits, 1);
                self.place(Placement::usual(TileKind::City));
            }
        }
        self.finish_unless_placing();
    }
}
