---
title: Terraforming Mars with bots
emoji: 🪐
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
short_description: An unofficial fan-made Terraforming Mars against AI bots
---

# Terraforming Mars with bots

An unofficial, non-commercial fan project: a digital *Terraforming Mars* to play in the browser against a ladder of
bots, from a Random Bot to a Search Bot. *Terraforming Mars* is a game by FryxGames; this project is not affiliated
with or endorsed by them. If you enjoy it, please [buy the game](https://fryxgames.se/product/terraforming-mars/).

**How it plays here:**
- Each visitor has their own Game against the bots: every Game needs a human. Your browser keeps an id, so reloading
  the page finds your Game again.
- Games are kept in the server's memory. A Game is forgotten 6 hours after you close the page, and all Games are lost
  whenever the Space restarts or goes to sleep. Save Replay downloads a file that Load Replay… plays on from later.
- The Space is shared, small and free. It keeps at most 100 Games at once and turns new visitors away when full, and
  if many play at once, the bots take longer to answer.
- The developer tools of the local version (the dev panel and its state editor) are off here.

The source, its rules notes and how the bots were trained are on
[GitHub](https://github.com/niels32167/tfm-with-bots). The Imitation, Value and Search Bots' models were trained on
Recorded Games: games humans played on Board Game Arena, with player names removed.
