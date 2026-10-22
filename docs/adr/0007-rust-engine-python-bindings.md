# Rust engine, called from Python

The engine is written in Rust and exposed to Python through PyO3 bindings. AI training happens in Python with PyTorch.

The speed requirement (ADR 0004) rules out pure Python. Rust beats C++ here because it is just as fast, game states copy trivially, and the compiler catches many bugs before they run. Go was rejected because calling it from Python is awkward, so training would have to reach the engine over a socket.

The user mostly writes Python, so most engine code will be written with Claude's help.
