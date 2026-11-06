# LUB Bot System
Single-process stack: FastAPI + Aiogram polling + APScheduler worker + Telegram WebApp on port 8000.

## Setup
```bash
cp .env.example .env
docker compose up -d
docker exec -it lub_postgres psql -U postgres -d lub_auction -c "\dt"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cloudflared tunnel --url http://localhost:8000
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```
## Test
Send `/publish Test Console | 0.02` to the bot as an admin, then:
```bash
TEST_ITEM_ID=<uuid> python tests/simulate_auction.py
```
Expected winner: user 103 with $0.75.
