# dipchase.py  · rebuilt from 0xc533 "dangerously-skip-permissions" (+$254,190)
# what the fills show, one 5m window: PAIR both sides early, DIP bids on the side that
# drops to 12-19c, CHASE the leader from 31c up once the move is clear, small HEDGE on
# the other side. 0 sells. $139,939 of his profit is rebates and rewards.
from pm import bid, take, held

NAME, COIN, MINUTES = "dipchase", "btc", 5
PAIR_USD, DIP_USD, CHASE_USD, HEDGE_USD = 5, 4, 10, 2


def step(L, slug, books, t_left):
    up, down = books["up"]["ask"], books["down"]["ask"]
    if t_left > 240:                                   # PAIR: first minute
        if up + down <= 1.01:
            bid(L, NAME, slug, "up", up - 0.01, PAIR_USD)
            bid(L, NAME, slug, "down", down - 0.01, PAIR_USD)
    elif t_left > 120:                                 # DIP: cheap side 12-19c
        for side, ask in (("up", up), ("down", down)):
            if ask <= 0.25:
                for p in (0.19, 0.15, 0.12):
                    bid(L, NAME, slug, side, p, DIP_USD)
    elif t_left > 20:                                  # CHASE + HEDGE
        lead = "up" if up > down else "down"
        lag = "down" if lead == "up" else "up"
        room = held(L, NAME, slug)[lead][1] < 3 * CHASE_USD
        if room and 0.60 <= books[lead]["ask"] <= 0.86:
            take(L, NAME, slug, lead, books[lead], CHASE_USD, 0.86)
            bid(L, NAME, slug, lag, 0.05, HEDGE_USD)
