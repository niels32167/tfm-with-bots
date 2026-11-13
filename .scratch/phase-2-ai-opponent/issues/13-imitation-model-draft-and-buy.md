# 13 — Imitation Model for Draft and buy

**What to build:** The first trained model: it predicts which cards strong Players draft and buy, trained on Recorded Games. These are about 40% of Decisions, and their data is ready. The Controller uses it for those Decisions and the Card Economy Bot for the rest.

Installing PyTorch needs my OK when this ticket starts. Check that it uses the RTX 3050, or fall back to the CPU and say so.

Keep Games apart for testing by whole Game, not by Decision, and test on Games from later dates than training where dates allow. The first questions are how high the rating filter can go before data runs out, and whether Games without Prelude help.

**Blocked by:** 11 — Card Economy Bot; 12 — Position encoding

**Status:** ready-for-agent

- [ ] One command trains a model within the laptop's limits, can resume, and saves it with its encoding version and the settings used.
- [ ] On held-out Games it predicts picks better than each baseline: a random pick, the most-kept card overall, and the Card Economy Bot's Prices. Accuracy is reported by Decision kind, Generation and rating.
- [ ] The Controller with this model beats the Card Economy Bot in a Match with the interval above 50%. If it doesn't, the reason is investigated and recorded before moving on.
- [ ] Results for rating filters, and for training with and without Games without Prelude, are recorded under Comments.
- [ ] On held-out Games, its keep rate for each card is compared with Players' (the dataset's, which ticket 08 checked against tfmstats.com's Starting Hand page), with the largest differences explained under Comments.
- [ ] It has learned synergies: for the 10 Corporation and Prelude pairs with the highest lift on tfmstats.com's Combinations page, and enough Games, it rates each part higher with the other than without. The result is recorded under Comments.
- [ ] A small test overfits a few hand-written positions without a GPU.
- [ ] It is selectable in the GUI, and a pick takes well under a second.

## Comments
