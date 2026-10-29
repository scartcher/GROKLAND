# filter.py
# six hard rules from two free APIs. no model, no opinion. missing data kills.
import time, requests
from config import FILTER as F

RC = "https://api.rugcheck.xyz/v1/tokens/{}/report"
DS = "https://api.dexscreener.com/tokens/v1/solana/{}"


def facts(mint: str) -> dict:
    rc = requests.get(RC.format(mint), timeout=20).json()
    pairs = requests.get(DS.format(mint), timeout=15).json() or []
    liq = lambda p: (p.get("liquidity") or {}).get("usd", 0)
    pool = max(pairs, key=liq) if pairs else {}
    supply = rc["token"]["supply"]
    skip = set(rc.get("knownAccounts") or {})   # pool vault + lockers aren't whales
    holders = [h for h in rc["topHolders"] if h["owner"] not in skip]
    born = pool.get("pairCreatedAt")
    return {
        "symbol": rc["tokenMeta"]["symbol"],
        "dev_pct": 100 * rc["creatorBalance"] / supply if supply else None,
        "liq_usd": liq(pool) or None,
        "top10_pct": round(sum(h["pct"] for h in holders[:10]), 1),
        "insiders": len(rc.get("insiderNetworks") or []),
        "h1_change": (pool.get("priceChange") or {}).get("h1"),
        "age_min": (time.time() * 1000 - born) / 60000 if born else None,
        "authority": rc["mintAuthority"] or rc["freezeAuthority"],
    }


def kill(f: dict) -> str | None:
    if None in (f["dev_pct"], f["liq_usd"], f["h1_change"], f["age_min"]):
        return "missing data"
    if f["authority"]:                        return "mint or freeze still open"
    if f["dev_pct"] > F["dev_max_pct"]:       return "Dev wallet >5%"
    if f["liq_usd"] < F["min_liq_usd"]:       return "Liquidity under $25k"
    if f["top10_pct"] > F["top10_max_pct"]:   return "Top 10 holders >35%"
    if f["insiders"] > F["max_insiders"]:     return "Bundled buys"
    if f["h1_change"] > F["max_h1_change"]:   return "Already +100% 1h"
    if f["age_min"] < F["min_age_min"]:       return "Pool too young"
    return None
