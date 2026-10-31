# pairs.py  · rebuilt from 0xb55fa (+$1.29M all-time, +$42,163 in one week)
# what the fills show: buys BOTH sides on ~80% of 5m markets. Up + Down always pays $1,
# so if the pair costs under $1 the market is green whatever BTC does. in one week:
# pair cost under $1 on 2,072 markets -> 1,534 green. over $1 on 1,958 -> 468 green.
from pm import bid, held

NAME, COIN, MINUTES = "pairs", "btc", 5
EDGE = 0.04           # bids sit so that up + down costs at most $0.96
USD = 10              # per side, per refresh
MAX_SIDE_USD = 40


def step(L, slug, books, t_left):
    if t_left < 30:
        return
    mid_up = (books["up"]["bid"] + books["up"]["ask"]) / 2
    up_px = round(mid_up - EDGE / 2, 2)
    down_px = round(1 - EDGE - up_px, 2)               # up + down = 1 - EDGE
    h = held(L, NAME, slug)
    if h["up"][0] <= h["down"][0] + 20:                # keep the two legs even
        bid(L, NAME, slug, "up", up_px, USD, MAX_SIDE_USD)
    if h["down"][0] <= h["up"][0] + 20:
        bid(L, NAME, slug, "down", down_px, USD, MAX_SIDE_USD)
