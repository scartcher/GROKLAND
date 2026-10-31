# crew.py
# one pass of the crew: Scout, Filter, Analyst, Sniper, Guard. the first "no" ends it.
import json, os, subprocess, sys, time
from collections import Counter
from config import SIGNALS, MAX_SIGNAL_AGE_S
import filter as hard
import analyst
from sniper import book, limits, copy, log
from guard import watch
import safety

DONE = "done.txt"                       # every signal and mint judged once, never twice


def run():
    if safety.stopped():
        print("STOP file found: crew is off. delete STOP to restart")
        return
    subprocess.run([sys.executable, "scout.py"])
    done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
    sigs = [json.loads(l) for l in open(SIGNALS)] if os.path.exists(SIGNALS) else []
    kills = Counter()
    for s in sigs:
        if s["sig"] in done or s["mint"] in done:
            continue
        if time.time() - s["t"] > MAX_SIGNAL_AGE_S * 3:
            continue                            # waited out an outage: too late now
        try:
            f = hard.facts(s["mint"])
        except hard.NoData:                     # rugcheck up, report empty: kill
            f = None
        except Exception:                       # 502, timeout, rate limit
            kills["rugcheck error"] += 1
            if safety.filter_failed():          # 2 in a row: Filter offline,
                kills["buys paused"] += 1       # no buys until it answers again
                break
            continue
        safety.filter_ok()
        done |= {s["sig"], s["mint"]}
        open(DONE, "a").write(f"{s['sig']}\n{s['mint']}\n")
        if f is None:
            kills["missing data"] += 1
            log("filter", s["mint"][:6], s["wallet"], "killed: missing data")
            continue
        why = hard.kill(f)
        if why:
            kills[why] += 1
            log("filter", f["symbol"], s["wallet"], f"killed: {why}")
            continue
        busy = limits(book())
        if busy:
            log("sniper", f["symbol"], s["wallet"], f"skipped: {busy}")
            continue
        why, g = analyst.kill(s, f["symbol"])
        if why:
            kills[why] += 1
            log("analyst", f["symbol"], s["wallet"], f"killed: {why}")
            continue
        log("analyst", f["symbol"], s["wallet"], f"passed · {g['x_read']}")
        print(copy(s["mint"], f["symbol"], s["wallet"]))
    for e in watch():
        print(e)
    b = book()
    equity = b["cash"] + sum(p["usd"] for p in b["open"].values())
    if safety.day_check(equity):
        safety.stop(f"down {safety.DAY_STOP_PCT}% today, equity ${equity:.2f}")
    for why, n in kills.most_common():
        print(f"{n:>5} killed · {why}")


if __name__ == "__main__":
    run()
