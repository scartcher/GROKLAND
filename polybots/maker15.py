# maker15.py  · rebuilt from gabigol (+$354,210 all-time, BTC 15m only)
# what the fills show: 0 sells in 5,000 fills, both sides on 74% of markets, avg ticket
# $7.70, $41,838 of the profit is maker rebates. he rests a ladder under the market and
# lets takers come to him. one whale market-bought $10,000 of Up and filled 52 of his
# Down bids from 56c to 5c in one second: $247.95 -> $936.06.
from pm import bid

NAME, COIN, MINUTES = "maker15", "btc", 15
STEPS = (0.03, 0.08, 0.15, 0.25, 0.40)   # how far under the current bid each rung sits
USD = 8


def step(L, slug, books, t_left):
    if t_left < 60:
        return
    for side in ("up", "down"):
        top = books[side]["bid"]
        for d in STEPS:
            if top - d >= 0.02:
                bid(L, NAME, slug, side, top - d, USD, cap=40)
