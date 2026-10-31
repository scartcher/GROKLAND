# GROKLAND

A 5-agent Grok Bot crew that copies smart wallets on Solana. Paper mode first.

| agent | file | what it does | cost |
|---|---|---|---|
| Scout | scout.py | reads every fresh buy of the wallets in wallets.txt from Solana RPC | free |
| Filter | filter.py | kills a token that breaks one of 6 hard rules (Rugcheck + DexScreener) | free |
| Analyst | analyst.py | checks the wallet's win rate, whether it already sold, then asks Grok to read X | 1 Grok call |
| Sniper | sniper.py | sizes the copy and prices it with a real Jupiter quote | free |
| Guard | guard.py | stop at -8% before entry, trails it up, takes half at +150% | free |
| Safety | safety.py | pauses buys when rugcheck is down, stops the crew at -15% on the day | free |

`crew.py` runs all five in order. `config.py` holds every number.

## install (inside Grok Bot)

1. Open your bot's computer, click **Take over**, open the terminal.
2. Get the files:
   ```bash
   git clone https://github.com/scartcher/grokland /workspace/grokland
   cd /workspace/grokland
   pip install -r requirements.txt
   ```
3. Save your xAI key without it showing on screen:
   ```bash
   read -rs -p "xai key: " K && printf 'XAI_API_KEY=%s\n' "$K" > .env && unset K && chmod 600 .env
   ```
4. Add 10 to 30 wallets to `wallets.txt`, one per line.
5. Test one pass:
   ```bash
   python crew.py
   ```
   You see `SCOUT ... bought ...` lines and kill counts. Nothing copied is normal.
6. Click **I'm done**, then tell the bot:
   `Every 2 minutes, in /workspace/grokland run python crew.py. Only post lines that start with "Sniper copied" or "Guard".`

## polybots (new)

`polybots/` = 7 Polymarket Up/Down bots rebuilt from 7 real wallets that made $3.3M+. Paper only. See polybots/README.md.

## safety (added Oct 31)

One night rugcheck started failing at 1:12 AM and the crew kept copying. Four rugs went through.
Now:

- missing data = kill. an empty rugcheck report never passes the Filter
- rugcheck errors twice in a row = no new buys until it answers again (Guard keeps watching open copies)
- max 10% of equity in one coin, never a second copy of a coin you already hold
- down 15% since the day began = the crew writes a `STOP` file and stops itself
- phone ping: install the ntfy app, subscribe to a topic, put it in `NTFY_TOPIC` in config.py
- to stop it by hand: `touch STOP`. to restart: `rm STOP`

## files it creates

- `signals.jsonl` every buy Scout saw
- `copylog.csv` every kill, copy and exit with the reason
- `book.json` cash and open copies
- `done.txt` signals already judged
- `health.json` rugcheck error streak and start-of-day equity
- `STOP` only when the crew stopped itself (or you made it)

## going live

`PAPER = True` in config.py means real signals and real prices with fake fills. Run a week on paper, read copylog.csv, then set `PAPER = False`: Sniper stops buying and posts an approval line, you buy in your own wallet.

Not financial advice. Most memecoins go to zero.
