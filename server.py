import os
import json
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from urllib.parse import parse_qs

import websockets
from websockets.exceptions import ConnectionClosed
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

#DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_API_KEY = "87a2edbe9275968ac8ff4a87ce988ff803a80457" 
if not DEEPGRAM_API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

app = FastAPI()

# Serve index.html explicitly
@app.get("/")
def index():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

# Mount /static → ./public
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")


@dataclass
class Room:
    clients: Set[WebSocket] = field(default_factory=set)
    deepgram_ws: Optional[websockets.WebSocketClientProtocol] = None
    recv_task: Optional[asyncio.Task] = None
    keepalive_task: Optional[asyncio.Task] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


rooms: Dict[str, Room] = {}


def deepgram_ws_url():
    params = {
        "model": "nova-3",
        "interim_results": "true",
        "punctuate": "true",
        "smart_format": "true",
        "endpointing": "250",
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"wss://api.deepgram.com/v1/listen?{qs}"


async def broadcast(room_id: str, payload: dict):
    room = rooms.get(room_id)
    if not room:
        return
    msg = json.dumps(payload)
    for ws in list(room.clients):
        try:
            await ws.send_text(msg)
        except Exception:
            room.clients.discard(ws)


async def ensure_deepgram(room_id: str):
    room = rooms[room_id]
    async with room.lock:
        if room.deepgram_ws and room.deepgram_ws.open:
            return

        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        dg = await websockets.connect(deepgram_ws_url(), additional_headers=headers)
        room.deepgram_ws = dg

        async def keepalive():
            while True:
                await asyncio.sleep(3.5)
                if dg.open:
                    await dg.send(json.dumps({"type": "KeepAlive"}))

        async def receiver():
            async for message in dg:
                data = json.loads(message)
                alt = (data.get("channel", {})
                           .get("alternatives", [{}])[0])
                transcript = alt.get("transcript", "").strip()
                if transcript:
                    await broadcast(room_id, {
                        "type": "stt",
                        "isFinal": data.get("is_final", False),
                        "transcript": transcript
                    })

        room.keepalive_task = asyncio.create_task(keepalive())
        room.recv_task = asyncio.create_task(receiver())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    qs = parse_qs(ws.scope["query_string"].decode())
    room_id = qs.get("room", [""])[0]
    mode = qs.get("mode", ["viewer"])[0]

    if not room_id:
        await ws.close(code=1008)
        return

    room = rooms.setdefault(room_id, Room())
    room.clients.add(ws)

    await ensure_deepgram(room_id)

    try:
        if mode == "viewer":
            while True:
                await ws.receive_text()
        else:
            while True:
                msg = await ws.receive()
                audio = msg.get("bytes")
                if audio:
                    await room.deepgram_ws.send(audio)
    except WebSocketDisconnect:
        pass
    finally:
        room.clients.discard(ws)

