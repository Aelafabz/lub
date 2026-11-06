import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from fastapi import HTTPException, Header
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def verify_telegram_webapp_data(init_data: str) -> dict:
    try:
        parsed_data = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed initData")

    if "hash" not in parsed_data:
        raise HTTPException(status_code=401, detail="Missing hash")

    received_hash = parsed_data.pop("hash")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=BOT_TOKEN.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=403, detail="Invalid WebApp signature")

    user_data = json.loads(parsed_data.get("user", "{}"))
    if not user_data.get("id"):
        raise HTTPException(status_code=400, detail="User ID missing in payload")

    return user_data

async def get_current_user(x_telegram_init_data: str = Header(...)) -> dict:
    return verify_telegram_webapp_data(x_telegram_init_data)
