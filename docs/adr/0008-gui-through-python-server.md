# The GUI reaches the engine through a local Python server

The browser GUI talks over a WebSocket to a small local Python server, which drives the Rust engine through the same Python bindings the AI training uses. It does not talk to the engine directly, and the engine is not compiled for the browser.

This keeps one route into the engine for both people and AI. When the AI is trained, playing against it in the GUI needs no new plumbing: the PyTorch model runs inside that same server.
