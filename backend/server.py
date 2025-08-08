import json, random, datetime
from typing import Optional, Dict, Set
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from twitch import TwitchIRCClient
from follows import get_follows

app = FastAPI(title="LUDIK BOT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_channel_keywords: Dict[str, str] = {}
_participants: Dict[str, Dict[str, dict]] = {}

def exact_match(msg: str, kw: Optional[str]) -> bool:
    return (kw is not None) and (msg.strip() == kw)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/chat/stream")
async def chat_stream(channel: str, keyword: Optional[str] = None):
    ch = channel.lstrip('#').lower()
    if keyword is not None:
        _channel_keywords[ch] = keyword

    client = TwitchIRCClient(ch)

    async def gen():
        async for user, text, is_sub in client.stream():
            kw = _channel_keywords.get(ch)
            if kw and exact_match(text, kw):
                _participants.setdefault(ch, {})
                if user.lower() not in _participants[ch]:
                    _participants[ch][user.lower()] = {"username": user, "subscriber": is_sub, "last_win_at": None}
                elif is_sub:
                    _participants[ch][user.lower()]["subscriber"] = True
            yield "data: " + json.dumps({"channel": ch, "user": user, "text": text, "subscriber": is_sub}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

@app.get("/api/participants")
async def list_participants(channel: str):
    ch = channel.lstrip('#').lower()
    items = list(_participants.get(ch, {}).values())
    items.sort(key=lambda x: x["username"].lower())
    return {"participants": items}

@app.post("/api/participants/clear")
async def clear_participants(channel: str):
    ch = channel.lstrip('#').lower()
    _participants[ch] = {}
    return {"ok": True}

@app.post("/api/winner")
async def winner(channel: str, only_subscribers: bool = False):
    ch = channel.lstrip('#').lower()
    pool = [p for p in _participants.get(ch, {}).values() if (p["subscriber"] or not only_subscribers)]
    if not pool:
        return {"winner": None}
    w = random.choice(pool)["username"]
    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    _participants[ch][w.lower()]["last_win_at"] = ts
    return {"winner": w, "winner_last_win_at": ts}

@app.get("/api/export")
async def export_csv(channel: str):
    ch = channel.lstrip('#').lower()
    rows = ["username,subscriber,last_win_at"]
    for p in _participants.get(ch, {}).values():
        rows.append(f"{p['username']},{int(p['subscriber'])},{p['last_win_at'] or ''}")
    return PlainTextResponse("\n".join(rows), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="participants_{ch}.csv"'})

@app.get("/api/coin")
async def coin():
    return {"coin": random.choice(["heads","tails"])}

@app.get("/api/follows_lookup")
async def follows_lookup(user: str):
    try:
        return await get_follows(user)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)

# Static frontend (built into ./web by Docker)
try:
    app.mount("/", StaticFiles(directory="web", html=True), name="web")
except Exception:
    pass
