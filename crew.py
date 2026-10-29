# crew.py
# one pass of the crew: Scout, Filter, Analyst, Sniper, Guard. the first "no" ends it.
import json, os, subprocess, sys
from collections import Counter
from config import SIGNALS
import filter as hard
import analyst
from sniper import book, limits, copy, log
from guard import watch

DONE = "done.txt"                       # every signal and mint judged once, never twice


def run():
    subprocess.run([sys.executable, "scout.py"])
    done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
    sigs = [json.loads(l) for l in open(SIGNALS)] if os.path.exists(SIGNALS) else []
    kills = Counter()
    for s in sigs:
        if s["sig"] in done or s["mint"] in done:
            continue
        done |= {s["sig"], s["mint"]}
        open(DONE, "a").write(f"{s['sig']}\n{s['mint']}\n")
        try:
            f = hard.facts(s["mint"])
        except Exception:
            kills["api down, skipped"] += 1
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
    for why, n in kills.most_common():
        print(f"{n:>5} killed · {why}")


if __name__ == "__main__":
    run()
