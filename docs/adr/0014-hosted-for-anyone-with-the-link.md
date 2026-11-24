# Hosted for anyone with the link

The Game is also hosted, so that anyone with the link can play it without running the server. It runs on Render's
free instance, from a public image on GitHub's registry, `ghcr.io/niels32167/terraforming-mars` (the user's call on
2026-11-23), at https://terraforming-mars-latest.onrender.com. The image is built from the `Dockerfile` by `deploy/push_image.sh`. It holds the engine, the CPU build
of torch, the three models and the built GUI, which the server sends on the same port as its WebSocket. The local
server is unchanged.

**What is hosted.** Each Visitor plays their own Game against the bots. Their browser keeps a Visitor id, sent as
`/ws?visitor=<id>`, so reloading finds their Game again. Humans playing each other from different browsers was left
out: it needs invite links and a Player View for each human.

On a hosted server (`python -m server --hosted`):
- The dev panel and its state editor are off. Save and Load Replay stay.
- Every Game needs a human, so bots don't play each other on a shared computer.
- Bots play without settings (no `search?seconds=60`). Beside the Search Bot's usual 1 s there is a registered one
  with 5 s (`search_5s`, the user's call on 2026-11-24): a tenth of a core buys 1 s too little search (README).
- At most `THINKERS` bots think at once (1 by default), across every Visitor's Game.
- At most 100 Visitors are kept, and one is forgotten 6 hours after closing their last connection.
- The bots' models are loaded at startup, not when a Visitor's bot first thinks.
- Games live in memory, so they are lost when the instance restarts or sleeps.

**Render's free instance**, by its terms on 2026-11-23:
- It has a tenth of a core and 512 MB.
- It sleeps after 15 minutes without traffic and takes about a minute to wake.

Measured in Docker at those limits, the server:
- answers 23 s after starting;
- uses about 230–300 MB with every model loaded;
- keeps a Visitor's longest wait over a Search Bot's Turn to 2.9 s in 40 s of play.

Live on Render, 30 s of play against the Search Bot reached Generation 7, with a longest wait of 2.8 s.

Those are for the Search Bot's usual 1 s. With 5 s, on 2026-11-24 and a tenth of the laptop's core, 200 s of play kept
a Visitor's longest wait for one pick to 5.0 s and used 388 MB at most. Other Visitors' bots wait their turn meanwhile.

**Considered options:**
- *A Hugging Face Space.* It was prepared first. But Docker Spaces on the free hardware now need a PRO subscription
  (about $9 a month): creating one was refused.
- *Fly.io.* It has no free tier for new accounts; it costs a few dollars a month.
- *Koyeb.* Its free instance matches Render's but needs a card.
- *Google Cloud Run.* It cuts WebSockets off after at most an hour and may drop Games held in memory.

**What this publishes.** The image is public, so anyone can pull it and read what it holds. That is the project's
source, already public on GitHub with the card texts. ADR 0003 used them because the project was private; the GitHub
repository has been public since before this decision, and hosting makes the Game itself public as well.

The image also holds the three models the bots play with: `imitation.pt`, `imitation-draft-buy.pt` and `value.pt`,
all trained on Recorded Games. This revisits ADR 0012's "nothing is published" for these models alone, the user's
call. The logs, the positions and anything else derived from them stay out of git and unpublished, and the models
hold no player names.

**Open points:**
- **The GUI's title font, Prototype,** is free for personal use only.
- **FryxGames may object** to a public digital version. If they do, the service and the image come down.
