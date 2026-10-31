# safety.py
# added after Oct 31: rugcheck went down at 1:12 AM and the crew kept buying.
# three switches: rugcheck error streak pauses buys, -15% on the day stops
# the crew, and a STOP file you can create by hand.
import json, os, time, requests
from config import HEALTH, STOP_FILE, FILTER_FAILS_PAUSE, DAY_STOP_PCT
from config import NTFY_TOPIC


def _load() -> dict:
    if os.path.exists(HEALTH):
        return json.load(open(HEALTH))
    return {"fails": 0, "day": {}}


def _save(h: dict):
    json.dump(h, open(HEALTH, "w"), indent=1)


def ping(msg: str):
    print(msg)
    topic = NTFY_TOPIC or os.getenv("NTFY_TOPIC", "")
    if topic:                                # free phone push: install ntfy, subscribe
        try:
            requests.post(f"https://ntfy.sh/{topic}", data=msg.encode(), timeout=10)
        except requests.RequestException:
            pass


def stopped() -> bool:
    return os.path.exists(STOP_FILE)


def stop(why: str):
    open(STOP_FILE, "w").write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {why}\n")
    ping(f"GROKLAND stopped itself: {why}. delete the STOP file to restart")


def filter_failed() -> bool:
    """one more rugcheck failure. True = buys are paused now."""
    h = _load()
    h["fails"] += 1
    _save(h)
    if h["fails"] == FILTER_FAILS_PAUSE:
        ping(f"Filter offline: rugcheck failed {h['fails']}x in a row, no new buys")
    return h["fails"] >= FILTER_FAILS_PAUSE


def filter_ok():
    h = _load()
    if h["fails"] >= FILTER_FAILS_PAUSE:
        ping("Filter back online, buys resume")
    h["fails"] = 0
    _save(h)


def day_check(equity: float) -> bool:
    """remembers equity at the first run of the day. True = day stop hit."""
    h, day = _load(), time.strftime("%Y-%m-%d")
    start = h["day"].setdefault(day, equity)
    _save(h)
    return equity <= start * (1 - DAY_STOP_PCT / 100)
