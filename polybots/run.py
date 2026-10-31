# run.py
# paper-runs the bots you name, every 5 seconds, on the live Polymarket books.
#   python run.py                      all 7
#   python run.py sniper99 pairs       only these
# Ctrl+C to stop. nothing here can place a real order.
import importlib, sys, time
import pm

ALL = ["sniper99", "ladder", "cheapside", "pairs", "maker15", "dipchase", "lock"]
TICK_S = 5
DAY_STOP_USD = -50          # paper bots down $50 today: everything stops


def tick(bots, L, cache):
    now = time.time()
    for b in bots:
        slug, start, end = pm.window(b.COIN, b.MINUTES, now)
        if slug not in cache:
            cache[slug] = pm.market(slug)
        m = cache[slug]
        if not m or m["closed"]:
            continue
        books = cache.get((slug, int(now) // TICK_S))
        if not books:
            books = {"up": pm.book(m["up"]), "down": pm.book(m["down"])}
            cache[(slug, int(now) // TICK_S)] = books
            pm.sweep(L, slug, books)
        b.step(L, slug, books, end - now)


def main():
    names = sys.argv[1:] or ALL
    bots = [importlib.import_module(n) for n in names]
    L, cache, last = pm.load(), {}, 0
    print("paper run:", ", ".join(names))
    while True:
        try:
            tick(bots, L, cache)
        except Exception as e:                      # one bad response, skip the tick
            print("skip:", type(e).__name__, e)
        if time.time() - last > 60:
            for line in pm.settle(L):
                print(line)
            day = sum(r["pnl"] for r in pm.stats(L).values())
            if day <= DAY_STOP_USD:
                print(f"day stop: paper pnl {day:+.2f}, stopping")
                pm.save(L)
                return
            last = time.time()
            cache = {k: v for k, v in cache.items() if not isinstance(k, tuple)}
        pm.save(L)
        time.sleep(TICK_S)


if __name__ == "__main__":
    main()
