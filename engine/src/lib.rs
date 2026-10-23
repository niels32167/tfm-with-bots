//! The Python engine module `tm_engine`: the one way into the engine for the tests,
//! the server and (later) the AI. Everything it returns is plain, JSON-serializable
//! Python data: dicts, lists, strings, numbers and None.

mod board;
mod game;
mod log;
mod random;
mod replay;
mod resources;
mod scenario;
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
    /// A new Game from its settings.
    #[new]
    #[pyo3(signature = (*, seed, players = 2))]
    fn new(seed: u64, players: usize) -> PyResult<Self> {
        let game = game::Game::new(game::Settings { players, seed }).map_err(PyValueError::new_err)?;
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
        let count = self.game.players.len();
        if player >= count {
            return Err(PyValueError::new_err(format!(
                "there is no Player with index {player}; this Game has {count} Players, indexed 0 to {}",
                count - 1
            )));
        }
        to_python(py, &view::player_view(&self.game, player))
    }

    /// Everything about the Game, including what Players hide from each other.
    /// For Hotseat and the dev panel; never for an AI Controller.
    fn full_view<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_python(py, &view::full_view(&self.game))
    }
}

fn to_python<'py>(py: Python<'py>, value: &impl Serialize) -> PyResult<Bound<'py, PyAny>> {
    Ok(pythonize(py, value)?)
}

#[pymodule]
fn tm_engine(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyGame>()?;
    module.add("MAX_SEED", game::MAX_SEED)?;
    Ok(())
}
