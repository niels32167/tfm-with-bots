"""Fitting Prices by Matches (ticket 11): a separable CMA-ES tunes the weights. Whether the fitted
weights are stronger is for Matches to say; these tests check the search and the weights' round trip."""

import random

from ai.fit_prices import SeparableCMAES, weights_at
from ai.prices import DEFAULT


def test_the_search_finds_the_least_of_a_bowl_from_samples_alone():
    target = [3.0, -2.0, 0.5, 1.0]
    search = SeparableCMAES([0.0] * 4, step=1.0, population=10, random_numbers=random.Random(1))

    for _ in range(80):
        points = search.ask()
        search.tell(points, [sum((x - t) ** 2 for x, t in zip(point, target, strict=True)) for point in points])

    assert all(abs(m - t) < 0.05 for m, t in zip(search.mean, target, strict=True))


def test_the_starting_point_is_the_starting_weights_and_steps_are_shares_of_them():
    assert weights_at([0.0] * len(DEFAULT.vector())) == DEFAULT
    doubled = weights_at([0.6931471805599453] + [0.0] * (len(DEFAULT.vector()) - 1))
    assert doubled.vector()[1:] == DEFAULT.vector()[1:]


def test_weights_stay_within_what_makes_sense():
    # A MegaCredit next Generation can't be worth more than one now.
    assert weights_at([5.0] * len(DEFAULT.vector())).discount < 1
