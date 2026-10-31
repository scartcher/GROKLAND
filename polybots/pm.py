# pm.py
# the shared parts: find the live Up/Down market, read its book, keep a paper ledger.
# every bot in this folder only ever talks to the ledger. nothing here can send money.
import json, os, time, requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
LEDGER = "ledger.json"


def window(coin: str, minutes: int, now: float | None = None):
    """(slug, start, end) of the window open right now: btc-updown-5m-1793045700"""
    now = now or time.time()
    start = int(now) // (minutes * 60) * (minutes * 60)
    return f"{coin}-updown-{minutes}m-{start}", start, start + minutes * 60


def market(slug: str) -> dict | None:
    ev = requests.get(f"{GAMMA}/events", params={"slug": slug}, timeout=15).json()
    if not ev:
        return None
    m = ev[0]["markets"][0]
    up, down = json.loads(m["clobTokenIds"])          # outcomes are ["Up", "Down"]
    prices = json.loads(m.get("outcomePrices") or "[]")
    return {"slug": slug, "up": up, "down": down, "closed": bool(m.get("closed")),
            "won": ("up" if prices[0] == "1" else "down")
                   if m.get("closed") and prices in (["1", "0"], ["0", "1"]) else None}


def book(token: str) -> dict:
    b = requests.get(f"{CLOB}/book", params={"token_id": token}, timeout=10).json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])),
                  reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return {"bid": bids[0][0] if bids else 0.0, "ask": asks[0][0] if asks else 1.0,
            "asks": asks}


# ---------- paper ledger ----------
def load() -> dict:
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER))
    return {"orders": [], "settled": {}}


def save(L: dict):
    json.dump(L, open(LEDGER, "w"), indent=1)


def mine(L: dict, bot: str, slug: str) -> list[dict]:
    return [o for o in L["orders"] if o["bot"] == bot and o["slug"] == slug]


def held(L: dict, bot: str, slug: str) -> dict:
    """filled shares and cost per side for one bot in one market"""
    h = {"up": [0.0, 0.0], "down": [0.0, 0.0]}
    for o in mine(L, bot, slug):
        if o["filled"]:
            h[o["side"]][0] += o["size"]
            h[o["side"]][1] += o["size"] * o["price"]
    return h


def committed(L: dict, bot: str, slug: str, side: str) -> float:
    """dollars filled + resting on one side of one market"""
    return sum(o["size"] * o["price"] for o in mine(L, bot, slug) if o["side"] == side)


def bid(L: dict, bot: str, slug: str, side: str, price: float, usd: float,
        cap: float = 50):
    """a resting buy order. it fills only if someone later sells at or below it.
    one order per price per market, and never more than `cap` dollars on a side."""
    price = round(price, 2)
    if not 0.01 <= price <= 0.99 or usd <= 0:
        return
    if any(o["side"] == side and o["price"] == price for o in mine(L, bot, slug)):
        return
    if committed(L, bot, slug, side) + usd > cap:
        return
    L["orders"].append({"bot": bot, "slug": slug, "side": side, "price": price,
                        "size": round(usd / price, 2), "filled": False,
                        "t": time.time()})


def take(L: dict, bot: str, slug: str, side: str, bk: dict, usd: float,
         max_price: float, cap: float = 50) -> float:
    """buy now from the asks, never above max_price or `cap` dollars on a side."""
    usd = min(usd, cap - committed(L, bot, slug, side))
    spent = 0.0
    for price, size in bk["asks"]:
        if price > max_price or spent >= usd:
            break
        sh = min(size, (usd - spent) / price)
        L["orders"].append({"bot": bot, "slug": slug, "side": side, "price": price,
                            "size": round(sh, 2), "filled": True, "t": time.time()})
        spent += sh * price
    return spent


def sweep(L: dict, slug: str, books: dict):
    """resting bids fill when the ask comes down to them (someone sold into us)."""
    for o in L["orders"]:
        if o["slug"] == slug and not o["filled"]:
            if books[o["side"]]["ask"] <= o["price"]:
                o["filled"] = True


def settle(L: dict, get_market=market) -> list[str]:
    """pays every finished window: $1 a share on the winning side, 0 on the other."""
    out = []
    now = time.time()
    for slug in sorted({o["slug"] for o in L["orders"]} - set(L["settled"])):
        start, minutes = int(slug.split("-")[3]), int(slug.split("-")[2][:-1])
        if now < start + 60 * minutes + 30:
            continue
        m = get_market(slug)
        if not m or not m["won"]:
            continue
        L["settled"][slug] = m["won"]
        for bot in sorted({o["bot"] for o in L["orders"] if o["slug"] == slug}):
            h = held(L, bot, slug)
            cost = h["up"][1] + h["down"][1]
            if cost:
                pnl = h[m["won"]][0] - cost
                out.append(f"{bot:<11} {slug}  {m['won'].upper():<4} "
                           f"cost ${cost:.2f}  pnl {pnl:+.2f}")
    L["orders"] = [o for o in L["orders"]
                   if o["filled"] or o["slug"] not in L["settled"]]
    return out


def stats(L: dict) -> dict:
    s = {}
    for slug, won in L["settled"].items():
        for bot in {o["bot"] for o in L["orders"] if o["slug"] == slug}:
            h = held(L, bot, slug)
            cost = h["up"][1] + h["down"][1]
            if not cost:
                continue
            r = s.setdefault(bot, {"markets": 0, "green": 0, "cost": 0.0, "pnl": 0.0})
            pnl = h[won][0] - cost
            r["markets"] += 1; r["green"] += pnl > 0; r["cost"] += cost; r["pnl"] += pnl
    return s
