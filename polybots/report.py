# report.py  · the morning read: one line per bot, then Grok says which one to pause.
#   python report.py          table only
#   python report.py grok     table + Grok's read (needs XAI_API_KEY in ../.env)
import os, sys, requests
import pm

MODEL = "grok-4.7"
PROMPT = """You review a paper trading desk of 7 Polymarket Up/Down bots. Each line is
bot, markets settled, green markets, dollars spent, paper pnl. Answer in 5 short lines:
which bot to keep, which to pause, and the one number that made you decide.
Do not invent numbers that are not in the table.

{table}"""


def table() -> str:
    rows = sorted(pm.stats(pm.load()).items(), key=lambda kv: -kv[1]["pnl"])
    out = [f"{'bot':<10} {'mkts':>5} {'green':>6} {'spent':>9} {'pnl':>9}"]
    for bot, r in rows:
        out.append(f"{bot:<10} {r['markets']:>5} {r['green']:>6} "
                   f"{r['cost']:>9.2f} {r['pnl']:>+9.2f}")
    return "\n".join(out)


def key() -> str:
    for path in (".env", "../.env"):
        if os.path.exists(path):
            for line in open(path):
                if line.startswith("XAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit("no XAI_API_KEY in .env")


def ask_grok(t: str) -> str:
    r = requests.post("https://api.x.ai/v1/responses", timeout=90,
                      headers={"Authorization": f"Bearer {key()}"},
                      json={"model": MODEL, "input": PROMPT.format(table=t)})
    r.raise_for_status()
    msg = [o for o in r.json()["output"] if o["type"] == "message"][-1]
    return msg["content"][0]["text"]


if __name__ == "__main__":
    t = table()
    print(t)
    if sys.argv[1:] == ["grok"]:
        print("\n" + ask_grok(t))
