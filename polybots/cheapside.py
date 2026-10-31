# cheapside.py  · rebuilt from pspspsps5 (+$299,217 all-time, BTC/ETH/SOL only)
# what the fills show: 34% of his buys are under 10c, 27% are over 80c. late in the
# window he buys the loser for pennies and tops up the leader. one replay: BTC Down
# 3-10c $11.11 -> $141.09, ETH Down 4-6c $8.21 -> $168.50.
from pm import bid, take

NAME, COIN, MINUTES = "cheapside", "btc", 5
LAST_S = 150
CHEAP = (0.03, 0.05, 0.07, 0.10)
CHEAP_USD = 2
LEAD_MAX, LEAD_USD = 0.85, 10


def step(L, slug, books, t_left):
    if t_left > LAST_S:
        return
    lead = "up" if books["up"]["ask"] > books["down"]["ask"] else "down"
    lag = "down" if lead == "up" else "up"
    for p in CHEAP:
        bid(L, NAME, slug, lag, p, CHEAP_USD)
    if 0.80 <= books[lead]["ask"] <= LEAD_MAX and t_left < 60:
        take(L, NAME, slug, lead, books[lead], LEAD_USD, LEAD_MAX)
