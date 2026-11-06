import hmac, hashlib, json, time, os, urllib.request
from urllib.parse import urlencode

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_BOT_TOKEN")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def build_signed_init_data(user_id: int, username: str) -> str:
    user_json = json.dumps({"id": user_id, "username": username}, separators=(",", ":"))
    payload = {"auth_date": str(int(time.time())), "query_id": "AAHdF6IQAAAAAN0XohDhrOrc", "user": user_json}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(payload)


def submit_test_bid(item_id: str, user_id: int, username: str, amount: str):
    body = json.dumps({"item_id": item_id, "bid_amount": amount}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/api/bids", data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "X-Telegram-Init-Data": build_signed_init_data(user_id, username)})
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[{username} -> ${amount}] HTTP {resp.status}: {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"[{username} -> ${amount}] HTTP {e.code}: {e.read().decode()}")


if __name__ == "__main__":
    ITEM = os.getenv("TEST_ITEM_ID", "00000000-0000-0000-0000-000000000000")
    submit_test_bid(ITEM, 101, "bob_bidder", "0.50")
    submit_test_bid(ITEM, 102, "carol_bidder", "0.50")
    submit_test_bid(ITEM, 103, "alice_winner", "0.75")
    submit_test_bid(ITEM, 104, "dave_bidder", "1.20")
    submit_test_bid(ITEM, 104, "dave_bidder", "1.30")
    time.sleep(2.1)
    submit_test_bid(ITEM, 104, "dave_bidder", "1.20")
