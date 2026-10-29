# guard.py
# every open copy, every run. the stop was set before the entry, Guard only raises it.
import time
from config import TRAIL, TAKE_HALF_AT, MAX_HOLD_H
from sniper import book, save, log, quote, sol_usd
from scout import SOL


def close(b: dict, mint: str, p: dict, now: float, why: str) -> str:
    pnl = now - p["usd"]
    day = time.strftime("%Y-%m-%d")
    b["cash"] += now
    b["day"][day] = b["day"].get(day, 0) + pnl
    del b["open"][mint]
    log("guard", p["symbol"], p["wallet"], why, pnl)
    return f"Guard {why} ${p['symbol']} · {'+' if pnl >= 0 else '-'}${abs(pnl):.2f}"


def watch() -> list[str]:
    b, events = book(), []
    for mint, p in list(b["open"].items()):
        lamports = quote(mint, SOL, p["raw"])   # a real sell quote for the whole bag
        now = lamports / 1e9 * sol_usd() if lamports else 0.0   # no route out = zero
        pct = 100 * (now / p["usd"] - 1)
        p["peak_pct"] = max(p["peak_pct"], pct)
        for at, stop in TRAIL:                  # the stop only ever moves up
            if p["peak_pct"] >= at:
                p["stop_pct"] = max(p["stop_pct"], stop)
        if pct <= p["stop_pct"]:
            events.append(close(b, mint, p, now, "stop hit"))
        elif pct >= TAKE_HALF_AT and not p.get("half"):
            b["cash"] += now / 2                # half leaves, % keeps its basis
            log("guard", p["symbol"], p["wallet"], "took half", (now - p["usd"]) / 2)
            p["raw"] //= 2; p["usd"] /= 2; p["half"] = True
            events.append(f"Guard took half ${p['symbol']} at +{pct:.0f}%")
        elif time.time() - p["t"] > MAX_HOLD_H * 3600 and p["stop_pct"] < 0:
            events.append(close(b, mint, p, now, "time out"))
    save(b)
    return events


if __name__ == "__main__":
    for e in watch():
        print(e)                                # silence means nothing moved
