# polybots

7 Polymarket Up/Down bots, rebuilt from the public fills of 7 real wallets that made
$3.3M+ between them. One file per bot. Paper only: they write to `ledger.json`, nothing
here can place a real order.

| file | rebuilt from | what it does |
|---|---|---|
| sniper99.py | BoneOhio, +$353,669 | last 2 min of BTC 5m, buys the side already at 94-99c |
| ladder.py | Haunting-Cheese, +$556,440 | penny bids 1-8c on both sides, waits for a panic seller |
| cheapside.py | pspspsps5, +$299,217 | late: loser for pennies, leader at 80-85c |
| pairs.py | 0xb55fa, +$1.29M | bids both sides so Up + Down costs at most $0.96 |
| maker15.py | gabigol, +$354,210 | BTC 15m, rests a ladder under the bid, never sells |
| dipchase.py | dangerously-skip-permissions, +$254,190 | pair, dip bids 12-19c, chase the leader, small hedge |
| lock.py | almach, +$252,234 | keeps buying the weaker side until both outcomes are green |

The wallets' strategies are read from their public trades. Their code is not public:
these files are my rebuild of what the fills show, not their bots.

## run

```bash
cd polybots
pip install requests
python run.py                  # all 7, paper, every 5 seconds
python run.py sniper99 lock    # only these two
python report.py               # table: markets, green, spent, paper pnl per bot
python report.py grok          # same table + Grok says which bot to pause
```

Inside Grok Bot: clone GROKLAND, then tell the bot
`Every morning at 9, in /workspace/grokland/polybots run python report.py grok and send me the answer.`
and keep `python run.py` running in its terminal.

## the honest catch

On a fair market with no rebates and nobody panic-selling, all 7 lose a little. I ran
them on a simulated BTC random walk for 6 hours: sniper99 -$17.55 on $1,380, maker15
+$141.55, the rest small losses. The real wallets win on three things this code does not
give you: speed, maker rebates (gabigol $41,838, dangerously-skip-permissions $139,939)
and other traders dumping into their bids. Run a week on paper before you even think
about real money.

## limits built in

- one order per price per market, max $50 a side unless a bot sets its own cap
- `run.py` stops everything at -$50 paper pnl
- `report.py` never trades, it only reads the ledger
