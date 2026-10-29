# config.py
# every number in GROKLAND lives here. the crew reads this file, it never writes it.

MODEL = "grok-4.7"            # console.x.ai -> Models if the API rejects it
PAPER = True                  # week one: real signals, real prices, fake fills
RPC = "https://api.mainnet-beta.solana.com"   # use a Helius/Triton URL when live

# money
CAP_USD = 100                 # the whole bankroll the crew may ever touch
TICKET_PCT = 0.10             # 10% of current equity per copy, never more
MAX_OPEN = 3                  # open copies at the same time
DAILY_LOSS_HALT_USD = 25      # down $25 today: no new copies until tomorrow

# scout
WALLETS = "wallets.txt"       # one smart wallet per line. you pick them, not the bot
MIN_BUY_SOL = 0.5             # ignore dust buys from the wallets you follow
MAX_SIGNAL_AGE_S = 120        # a buy older than 2 minutes is not a signal anymore

# filter: hard rules, one number each. any break = killed
FILTER = {
    "dev_max_pct": 5,         # dev wallet holding over 5%
    "min_liq_usd": 25_000,    # liquidity under $25k
    "top10_max_pct": 35,      # top 10 holders over 35% (pools and lockers not counted)
    "max_insiders": 0,        # bundled buys: any insider network Rugcheck can see
    "max_h1_change": 100,     # already up 100% in the last hour
    "min_age_min": 20,        # pool younger than 20 minutes
}

# analyst
WALLET_SOLD_PCT = 30          # the wallet you copy already sold 30% of its bag
WALLET_MIN_WINRATE = 55       # after 5 copies, a wallet under 55% wins gets muted
MIN_CONFIDENCE = 0.65         # Grok's X read has to be this sure, or it's a skip

# guard: exits exist before the entry
STOP_PCT = -8                 # hard stop, set before every copy
TRAIL = [(20, 0), (50, 25), (100, 60)]   # peak +20% -> stop at entry, +50 -> +25 ...
TAKE_HALF_AT = 150            # +150%: half the bag goes
MAX_HOLD_H = 4                # 4 hours and the trail never armed: out

# files
SIGNALS, LOG, BOOK = "signals.jsonl", "copylog.csv", "book.json"
