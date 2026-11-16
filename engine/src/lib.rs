//! The Python engine module `tm_engine`: the one way into the engine for the tests,
//! the server and (later) the AI. Everything it returns is plain, JSON-serializable
//! Python data: dicts, lists, strings, numbers and None.

mod board;
mod card_actions;
mod card_code;
mod card_flow;
mod card_resources;
mod card_set;
mod cards;
mod corporations;
mod deal;
mod deck;
mod draft;
mod expenses;
mod game;
mod log;
mod milestones_and_awards;
mod playing_cards;
mod prelude_cards;
mod random;
mod random_bot;
mod replay;
mod resources;
mod sampling;
mod scenario;
mod scoring;
mod targets;
mod triggers;
mod view;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pythonize::{depythonize, pythonize};
use serde::Serialize;

/// A Game of Terraforming Mars, always either over or waiting on one Decision.
#[pyclass(name = "Game", module = "tm_engine")]
struct PyGame {
    game: game::Game,
}

#[pymethods]
impl PyGame {
    /// A new Game from its settings, with the Draft unless `draft` is false. Without
    /// `corporations`, as a Replay saved before they existed plays, nobody has one. With `prelude`,
    /// each Player is dealt Prelude Cards at setup, and the deck has Prelude's Project Cards. A `deal`
    /// gives the first player and the cards in the order dealt and drawn, as a dict (see deal.rs).
    #[new]
    #[pyo3(signature = (*, seed, players = 2, draft = true, corporations = true, prelude = false, deal = None))]
    fn new(
        seed: u64,
        players: usize,
        draft: bool,
        corporations: bool,
        prelude: bool,
        deal: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let deal = deal
            .map(|deal| {
                depythonize(deal).map_err(|error| PyValueError::new_err(format!("invalid deal: {error}")))
            })
            .transpose()?;
        let settings = game::Settings {
            players,
            seed,
            implemented_cards_first: false,
            draft,
            corporations,
            prelude,
            deal,
        };
        let game = game::Game::new(settings).map_err(PyValueError::new_err)?;
        Ok(PyGame { game })
    }

    /// A Game started from a Scenario, given as a dict. Anything left out takes the normal defaults.
    #[staticmethod]
    fn from_scenario(scenario: &Bound<'_, PyAny>) -> PyResult<Self> {
        let invalid = |reason: String| PyValueError::new_err(format!("invalid Scenario: {reason}"));
        let scenario: scenario::Scenario =
            depythonize(scenario).map_err(|error| invalid(error.to_string()))?;
        let game = scenario.start().map_err(invalid)?;
        Ok(PyGame { game })
    }

    /// This Game's position as a Scenario, in the form `from_scenario` reads.
    /// For the dev panel; never for an AI Controller, as it holds every hand and the deck order.
    fn to_scenario<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &self.game.to_scenario())
    }

    /// The Game a Replay describes, rebuilt by replaying its picks from the start: all of
    /// them, or only the first `step` (step 0 is the Game before any pick).
    #[staticmethod]
    #[pyo3(signature = (replay, step = None))]
    fn from_replay(replay: &Bound<'_, PyAny>, step: Option<usize>) -> PyResult<Self> {
        let invalid = |reason: String| PyValueError::new_err(format!("invalid Replay: {reason}"));
        let replay: replay::Replay = depythonize(replay).map_err(|error| invalid(error.to_string()))?;
        let game = replay.rebuild(step).map_err(invalid)?;
        Ok(PyGame { game })
    }

    /// An independent copy: changing either Game never changes the other.
    fn copy(&self) -> Self {
        PyGame { game: self.game.clone() }
    }

    /// The Decision the Game is waiting on, or None once it is over.
    #[getter]
    fn decision<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &view::decision(&self.game))
    }

    /// Answers the current Decision with its Option at `index`. Pass the Decision's
    /// `sequence` number to have a stale pick rejected rather than applied to a later Decision.
    #[pyo3(signature = (index, sequence = None))]
    fn pick(&mut self, index: usize, sequence: Option<u64>) -> PyResult<()> {
        self.game.pick(index, sequence).map_err(|error| PyValueError::new_err(error.to_string()))
    }

    /// Plays on with a Random Bot for every Player: random Options, `picks` of them or until
    /// the Game is over. The same `seed` always picks the same way from the same position.
    #[pyo3(signature = (*, seed, picks = None))]
    fn play_randomly(&mut self, seed: u64, picks: Option<usize>) {
        random_bot::play_randomly(&mut self.game, seed, picks);
    }

    /// The Replay so far: where this Game started and the index of every Option picked.
    #[getter]
    fn replay<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &self.game.replay)
    }

    /// The game log: one plain-language line for each thing that has happened.
    #[getter]
    fn log(&self) -> Vec<String> {
        self.game.log.iter().map(|event| event.text()).collect()
    }

    /// Whether the Game is over.
    #[getter]
    fn is_over(&self) -> bool {
        self.game.is_over()
    }

    /// Each Player's final score once the Game is over, otherwise None.
    #[getter]
    fn scores<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &self.game.scores())
    }

    /// How many Players the Game has.
    #[getter]
    fn players(&self) -> usize {
        self.game.players.len()
    }

    /// The seed this Game was created with.
    #[getter]
    fn seed(&self) -> u64 {
        self.game.settings.seed
    }

    /// Everything `player` (an index from 0) is allowed to know.
    fn player_view<'py>(&self, py: Python<'py>, player: usize) -> PyResult<Bound<'py, PyAny>> {
        self.check_player(player)?;
        to_python(py, &view::player_view(&self.game, player))
    }

    /// What makes Sampled Positions for `player` at this position: Games dealt from what their Player
    /// View holds, never from the cards they can't see.
    fn sampler(&self, player: usize) -> PyResult<PySampler> {
        self.check_player(player)?;
        Ok(PySampler { sampler: sampling::Sampler::new(&self.game, player) })
    }

    /// Everything about the Game, including what Players hide from each other.
    /// For Hotseat and the dev panel; never for an AI Controller.
    fn full_view<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &view::full_view(&self.game))
    }
}

impl PyGame {
    fn check_player(&self, player: usize) -> PyResult<()> {
        let count = self.game.players.len();
        if player >= count {
            return Err(PyValueError::new_err(format!(
                "there is no Player with index {player}; this Game has {count} Players, indexed 0 to {}",
                count - 1
            )));
        }
        Ok(())
    }
}

/// Makes Sampled Positions for one Player at one position. It holds the position inside the engine,
/// where Python can't reach it, and offers nothing but samples.
#[pyclass(name = "Sampler", module = "tm_engine", frozen)]
struct PySampler {
    sampler: sampling::Sampler,
}

#[pymethods]
impl PySampler {
    /// A Sampled Position: a new Game. The same seed always gives the same Game.
    #[pyo3(signature = (*, seed))]
    fn sample(&self, seed: u64) -> PyGame {
        PyGame { game: self.sampler.sample(seed) }
    }
}

/// The card catalog: the printed data of every card, Project Cards in number order and then
/// the Corporations. Each call returns a new list, so changing it changes nothing else.
#[pyfunction]
fn card_catalog(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    to_python(py, &*cards::CARD_CATALOG)
}

fn to_python<'py>(py: Python<'py>, value: &impl Serialize) -> PyResult<Bound<'py, PyAny>> {
    Ok(pythonize(py, value)?)
}

#[pymodule]
fn tm_engine(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyGame>()?;
    module.add_class::<PySampler>()?;
    module.add_function(wrap_pyfunction!(card_catalog, module)?)?;
    module.add("MAX_SEED", game::MAX_SEED)?;
    Ok(())
}
