# lock.py  · rebuilt from almach (+$252,234 all-time, 123,099 markets)
# what the fills show: buys both sides of a 15m window and keeps buying the cheaper one
# until BOTH outcomes are green, then stops. one window: both-green at 401 s, broken at
# 423 s, locked for good at 611 s -> IF UP +$149.14 / IF DOWN +$75.05.
from pm import take, held

NAME, COIN, MINUTES = "lock", "btc", 15
USD = 6
MAX_USD = 300


def step(L, slug, books, t_left):
    if t_left < 30:
        return
    h = held(L, NAME, slug)
    cost = h["up"][1] + h["down"][1]
    if_up, if_down = h["up"][0] - cost, h["down"][0] - cost
    if cost and if_up > 0 and if_down > 0:
        return                                         # locked: green either way
    if cost >= MAX_USD:
        return
    side = "up" if if_up < if_down else "down"         # fix the weaker outcome
    if books[side]["ask"] <= 0.60:
        take(L, NAME, slug, side, books[side], USD, 0.60, MAX_USD / 2)
