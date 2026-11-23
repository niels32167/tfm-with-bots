"""Starts the server: `uv run python -m server` for the local one, beside vite's dev server.

Hosted for anyone with its link (ADR 0014), as the Hugging Face Space runs it:
`python -m server --hosted --thinkers 2 --host 0.0.0.0 --port 7860 --gui gui/dist`.
"""

import argparse
from pathlib import Path

import uvicorn

from server.app import Hosting, create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Terraforming Mars server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1", help="the address to listen on; 0.0.0.0 for every one")
    parser.add_argument("--hosted", action="store_true", help="a Game for each Visitor, with the dev panel off")
    parser.add_argument(
        "--thinkers", type=int, help="hosted: how many bots may think at once (default: the cores this process may use)"
    )
    parser.add_argument("--gui", type=Path, help="the built GUI's folder (gui/dist), to serve it on the same port")
    arguments = parser.parse_args()
    hosting = None
    if arguments.hosted:
        hosting = Hosting() if arguments.thinkers is None else Hosting(thinkers=arguments.thinkers)
    app = create_app(hosting=hosting, gui=arguments.gui)
    uvicorn.run(app, host=arguments.host, port=arguments.port)


if __name__ == "__main__":
    main()
