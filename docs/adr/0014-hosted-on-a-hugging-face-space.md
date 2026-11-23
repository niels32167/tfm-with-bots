# Hosted on a Hugging Face Space for anyone with the link

The Game is also hosted, so that anyone with the link can play it without running the server: a public Hugging Face
Space, built from the `Dockerfile` (the user's call on 2026-11-23). The image holds the engine, the CPU build of torch,
the three models and the built GUI, which the server sends on the same port as its WebSocket. The local server is
unchanged.

**What is hosted.** Each Visitor plays their own Game against the bots. Their browser keeps a Visitor id, sent as
`/ws?visitor=<id>`, so reloading finds their Game again. Humans playing each other from different browsers was left
out: it needs invite links and a Player View for each human.

On a hosted server (`python -m server --hosted`):
- The dev panel and its state editor are off. Save and Load Replay stay.
- Every Game needs a human, so bots don't play each other on a shared computer.
- Bots play without settings (no `search?seconds=60`).
- At most two bots think at once, across every Visitor's Game: the free Space has 2 cores (`--thinkers 2`).
- At most 100 Visitors are kept, and one is forgotten 6 hours after closing their last connection.
- Games live in memory, so they are lost when the Space restarts or sleeps.

**Considered options:**
- *Fly.io.* It keeps the image and models private and its link unlisted, but costs a few dollars a month.
- *Render's free tier.* Its 512 MB is too little for torch and the engine.
- *Google Cloud Run.* It cuts WebSockets off after at most an hour and may drop Games held in memory.

The Space is free, with 2 cores and 16 GB, enough for torch.

**What this publishes.** A public Space shows its files, so the project's source is published there as it already
is on GitHub, with the card texts. ADR 0003 used them because the project was private, and the GitHub repository has
been public since before this decision; the Space makes the Game itself public as well. The three models the bots play with are published too:
- `imitation.pt`, `imitation-draft-buy.pt` and `value.pt`, all trained on Recorded Games.

This revisits ADR 0012's "nothing is published" for these models alone, the user's call. The logs, the positions and
anything else derived from them stay out of git and unpublished, and the models hold no player names.

**Open points:**
- **The GUI's title font, Prototype,** is free for personal use only.
- **FryxGames may object** to a public digital version. If they do, the Space comes down.
