# simple_signaling_server.py
import asyncio
import websockets

clients = set()

async def handler(ws):
    print(f"🔌 Client connected from {ws.remote_address}")
    print("HIT")
    print(ws)
    clients.add(ws)
    try:
        async for msg in ws:
            print(msg)
            for c in clients:
                if c != ws:
                    await c.send(msg)
    finally:
        clients.remove(ws)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8443):
        print("Signaling server running at ws://0.0.0.0:8443")
        await asyncio.Future()  # run forever

asyncio.run(main())
