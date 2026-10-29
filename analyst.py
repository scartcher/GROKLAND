# analyst.py
# deep checks: is the wallet any good, did it already sell, what does X say.
import csv, datetime, json, os, requests
from config import MODEL, LOG, WALLET_SOLD_PCT, WALLET_MIN_WINRATE, MIN_CONFIDENCE
from scout import rpc

PROMPT = """You are the ANALYST in GROKLAND, a paper copy-trading crew on Solana.
A smart wallet just bought ${symbol} (mint {mint}). Code already checked dev share,
liquidity, top 10, insiders, pump size and pool age. Do not re-check those numbers.
Search X for this exact mint and ticker from the last 48 hours and answer only:
is this a real community, or a copycat ticker / paid raid / one-account hype?
Return JSON only: {{"verdict": "COPY" or "SKIP", "confidence": 0-1,
"x_read": "<=15 words", "main_risk": "<=12 words"}}
If you find almost nothing, verdict is SKIP."""


def _key() -> str:
    for line in open(".env"):
        if line.startswith("XAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no XAI_API_KEY in .env")


def winrate(wallet: str) -> tuple[int, float]:
    rows = list(csv.DictReader(open(LOG))) if os.path.exists(LOG) else []
    done = [float(r["pnl_usd"]) for r in rows if r["wallet"] == wallet and r["pnl_usd"]]
    return len(done), 100 * sum(p > 0 for p in done) / len(done) if done else 100.0


def sold_pct(wallet: str, mint: str, bought: float) -> float:
    accs = rpc("getTokenAccountsByOwner",
               [wallet, {"mint": mint}, {"encoding": "jsonParsed"}])
    info = [a["account"]["data"]["parsed"]["info"] for a in accs["value"]]
    now = sum(float(i["tokenAmount"]["uiAmount"] or 0) for i in info)
    return max(0.0, 100 * (1 - now / bought)) if bought else 100.0


def ask_grok(symbol: str, mint: str) -> dict:
    since = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    r = requests.post("https://api.x.ai/v1/responses", timeout=90,
        headers={"Authorization": f"Bearer {_key()}"},
        json={"model": MODEL, "max_turns": 2,
              "input": PROMPT.format(symbol=symbol, mint=mint),
              "tools": [{"type": "x_search", "from_date": since}]})
    r.raise_for_status()
    msg = [o for o in r.json()["output"] if o["type"] == "message"][-1]
    text = msg["content"][0]["text"]
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


def kill(sig: dict, symbol: str) -> tuple[str | None, dict]:
    n, wr = winrate(sig["wallet"])
    if n >= 5 and wr < WALLET_MIN_WINRATE:
        return f"Wallet win-rate <{WALLET_MIN_WINRATE}%", {}
    if sold_pct(sig["wallet"], sig["mint"], sig["tokens"]) >= WALLET_SOLD_PCT:
        return "Wallet sold early", {}
    try:
        g = ask_grok(symbol, sig["mint"])
    except Exception as e:                  # a failed call is a skip, never a copy
        return f"grok failed: {type(e).__name__}", {}
    if g.get("verdict") != "COPY" or g.get("confidence", 0) < MIN_CONFIDENCE:
        return f"X read: {g.get('x_read', 'skip')}", g
    return None, g
