# sniper.py
# sizes the copy, prices it with a real Jupiter quote, writes it into the book.
import csv, json, os, time, requests
from config import LOG, BOOK, PAPER, CAP_USD, TICKET_PCT, MAX_OPEN, STOP_PCT
from config import DAILY_LOSS_HALT_USD
from scout import SOL, USDC

JUP = "https://lite-api.jup.ag/swap/v1/quote"


def quote(src: str, dst: str, amount: int) -> int | None:
    params = {"inputMint": src, "outputMint": dst, "amount": amount, "slippageBps": 300}
    q = requests.get(JUP, params=params, timeout=15).json()
    return int(q["outAmount"]) if "outAmount" in q else None


def sol_usd() -> float:
    return quote(SOL, USDC, 10**9) / 1e6


def book() -> dict:
    if os.path.exists(BOOK):
        return json.load(open(BOOK))
    return {"cash": CAP_USD, "open": {}, "day": {}}


def save(b: dict):
    json.dump(b, open(BOOK, "w"), indent=1)


def log(agent: str, symbol: str, wallet: str, event: str, pnl=""):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "agent", "symbol", "wallet", "event", "pnl_usd"])
        pnl = round(pnl, 2) if pnl != "" else ""
        w.writerow([time.strftime("%H:%M:%S"), agent, symbol, wallet, event, pnl])


def limits(b: dict) -> str | None:
    if len(b["open"]) >= MAX_OPEN:
        return "all slots busy"
    if b["day"].get(time.strftime("%Y-%m-%d"), 0) <= -DAILY_LOSS_HALT_USD:
        return "daily loss halt"
    return None


def copy(mint: str, symbol: str, wallet: str) -> str:
    b = book()
    equity = b["cash"] + sum(p["usd"] for p in b["open"].values())
    usd = round(min(b["cash"], equity * TICKET_PCT), 2)
    lamports = int(usd / sol_usd() * 1e9)
    raw = quote(SOL, mint, lamports)        # what you'd really get, slippage in
    if not raw:
        return f"no route for {symbol}"
    if not PAPER:
        return f"APPROVE: buy ${usd} of {symbol} ({mint}) yourself, in your own wallet"
    b["cash"] -= usd
    b["open"][mint] = {"symbol": symbol, "wallet": wallet, "usd": usd, "raw": raw,
                       "peak_pct": 0, "stop_pct": STOP_PCT, "t": time.time()}
    save(b)
    log("sniper", symbol, wallet, f"copied {lamports / 1e9:.2f} SOL")
    return f"Sniper copied ${symbol} · {lamports / 1e9:.2f} SOL (${usd})"
