# ladder.py  · rebuilt from Haunting-Cheese / 0x50f7 (+$556,440 all-time)
# what the fills show: penny bids at 1-8c on BTC/ETH/SOL/BNB 5m. most expire or lose a
# few dollars. once in a while someone panic-sells into them: one window paid
# $225.36 -> $8,508.07 when Down was dumped into his 1c-8c rungs.
from pm import bid

NAME, COIN, MINUTES = "ladder", "btc", 5
RUNGS = {0.08: 2, 0.06: 2, 0.04: 3, 0.02: 4, 0.01: 5}   # price: dollars
FROM_S = 200          # place the ladder once the window has 200 s left


def step(L, slug, books, t_left):
    if t_left > FROM_S:
        return
    for side in ("up", "down"):
        for price, usd in RUNGS.items():
            bid(L, NAME, slug, side, price, usd)       # bid() skips rungs already there
