# scout.py
# watches every wallet in wallets.txt, writes each fresh buy into signals.jsonl.
import json, os, time, requests
from config import RPC, WALLETS, MIN_BUY_SOL, MAX_SIGNAL_AGE_S, SIGNALS

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"


def rpc(method: str, params: list):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    for wait in (0, 2, 5, 10):              # the free RPC rate-limits: back off, retry
        time.sleep(wait)
        r = requests.post(RPC, json=body, timeout=20)
        if r.status_code != 429 and "result" in r.json():
            return r.json()["result"]
    raise RuntimeError(f"{method}: {r.status_code} {r.text[:120]}")


def amounts(balances: list, wallet: str) -> dict:
    return {b["mint"]: float(b["uiTokenAmount"]["uiAmount"] or 0)
            for b in balances if b.get("owner") == wallet}


def buys(wallet: str, limit: int = 15) -> list[dict]:
    out = []
    for s in rpc("getSignaturesForAddress", [wallet, {"limit": limit}]):
        if s["err"] or time.time() - (s["blockTime"] or 0) > MAX_SIGNAL_AGE_S:
            continue
        tx = rpc("getTransaction", [s["signature"], {"encoding": "jsonParsed",
                 "maxSupportedTransactionVersion": 1}])   # v1 txs exist now, 0 errors
        if not tx:
            continue
        m = tx["meta"]
        keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
        if wallet not in keys:
            continue
        i = keys.index(wallet)
        sol = (m["preBalances"][i] - m["postBalances"][i]) / 1e9
        pre = amounts(m["preTokenBalances"], wallet)
        for mint, now in amounts(m["postTokenBalances"], wallet).items():
            got = now - pre.get(mint, 0)
            if mint not in (SOL, USDC, USDT) and got > 0 and sol >= MIN_BUY_SOL:
                out.append({"t": s["blockTime"], "wallet": wallet, "mint": mint,
                            "sol": round(sol, 3), "tokens": got, "sig": s["signature"]})
    return out


if __name__ == "__main__":
    wallets = [w.strip() for w in open(WALLETS) if w.strip() and w[0] != "#"]
    seen = set()
    if os.path.exists(SIGNALS):
        seen = {json.loads(l)["sig"] for l in open(SIGNALS)}
    with open(SIGNALS, "a") as f:
        for w in wallets:
            for b in buys(w):
                if b["sig"] not in seen:
                    f.write(json.dumps(b) + "\n")
                    who, what = f"{w[:4]}..{w[-4:]}", b["mint"][:6]
                    print(f"SCOUT {who} bought {what}.. {b['sol']} SOL")
