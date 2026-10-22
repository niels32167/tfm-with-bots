"""Starts the local server: `uv run python -m server`."""

import argparse

import uvicorn

from server.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Terraforming Mars local server")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()
    uvicorn.run(create_app(), host="127.0.0.1", port=arguments.port)


if __name__ == "__main__":
    main()
