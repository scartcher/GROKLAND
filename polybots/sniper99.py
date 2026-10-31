# sniper99.py  · rebuilt from BoneOhio (+$353,669 all-time, 183,404 markets)
# what the fills show: in the last ~2 minutes of a 5m window he buys the side that is
# already at 94-99c. one side only. tiny edge, thousands of times a day.
from pm import take

NAME, COIN, MINUTES = "sniper99", "btc", 5
LAST_S = 120          # only act in the final 2 minutes
MIN_P, MAX_P = 0.94, 0.99
USD = 20              # per market


def step(L, slug, books, t_left):
    if t_left > LAST_S:
        return
    for side in ("up", "down"):
        bk = books[side]
        if MIN_P <= bk["ask"] <= MAX_P:
            take(L, NAME, slug, side, bk, USD, MAX_P, cap=USD)
            return                                     # never both sides
