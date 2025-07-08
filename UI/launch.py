import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import zenoh

app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Heartbeat tracking
HEARTBEATS = {}
TTL = 10  # seconds

# Zenoh setup
zenoh_session = zenoh.open({})
zenoh_sub = None

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Zenoh subscriber callback
def heartbeat_listener(sample):
    key = sample.key_expr
    value = sample.payload.decode()
    HEARTBEATS[key] = {"value": value, "timestamp": time.time()}

# Background task: subscribe to Zenoh and clean up expired heartbeats
async def zenoh_subscriber():
    global zenoh_sub
    zenoh_sub = zenoh_session.declare_subscriber(
        "global/iff", heartbeat_listener
    )
    while True:
        # Remove expired heartbeats
        now = time.time()
        expired = [k for k, v in HEARTBEATS.items() if now - v["timestamp"] > TTL]
        for k in expired:
            del HEARTBEATS[k]
        # Broadcast current heartbeats
        await manager.broadcast({"heartbeats": list(HEARTBEATS.values())})
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(zenoh_subscriber())

@app.websocket("/ws/heartbeats")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/zenoh/command/")
async def send_zenoh_command(key: str, value: str):
    zenoh_session.put(key, value.encode())
    return {"status": "sent", "key": key, "value": value}

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
    <body>
    <h1>Zenoh IFF Heartbeat Backend</h1>
    </body>
    </html>
    """)