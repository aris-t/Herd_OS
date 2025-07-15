#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstWebRTC', '1.0')
gi.require_version('GstSdp', '1.0')
from gi.repository import Gst, GstWebRTC, GstSdp, GLib
import json
import asyncio
import websockets
import threading

Gst.init(None)

class WebRTCTest:
    def __init__(self, loop):
        self.pipeline = None
        self.webrtc = None
        self.websocket = None
        self.loop = loop  # Store the event loop reference
        
    def create_pipeline(self):
        # Simple test pattern instead of SHM for testing
        pipeline_str = (
            "videotestsrc pattern=ball ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "vp8enc deadline=1 ! "
            "rtpvp8pay ! "
            "webrtcbin name=webrtc"
        )
        
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.webrtc = self.pipeline.get_by_name("webrtc")
        
        self.webrtc.connect("on-negotiation-needed", self.on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self.on_ice_candidate)
        
    def on_negotiation_needed(self, webrtc):
        print("📡 Creating offer...")
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, webrtc, None)
        webrtc.emit("create-offer", None, promise)
    
    def on_offer_created(self, promise, webrtc, user_data):
        reply = promise.get_reply()
        offer = reply.get_value("offer")
        
        promise = Gst.Promise.new()
        webrtc.emit("set-local-description", offer, promise)
        
        if self.websocket and self.loop:
            sdp_text = offer.sdp.as_text()
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self.websocket.send(json.dumps({
                        "type": "offer",
                        "sdp": sdp_text
                    }))
                )
            )
    
    def on_ice_candidate(self, webrtc, mlineindex, candidate):
        print(f"🧊 ICE: {candidate}")
        if self.websocket and self.loop:
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self.websocket.send(json.dumps({
                        "type": "ice-candidate",
                        "candidate": candidate,
                        "sdpMLineIndex": mlineindex
                    }))
                )
            )

    def set_answer(self, sdp_text):
        ret, sdp = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(sdp_text.encode(), sdp)
        answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdp)
        
        promise = Gst.Promise.new()
        self.webrtc.emit("set-remote-description", answer, promise)

    def add_ice(self, candidate, mline_index):
        self.webrtc.emit("add-ice-candidate", mline_index, candidate)

    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        print("▶️ Started")

# WebSocket handler
async def handle_client(websocket):
    print(f"👤 Client: {websocket.remote_address}")
    
    test = WebRTCTest(asyncio.get_event_loop())
    test.websocket = websocket
    test.create_pipeline()
    test.start()
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "answer":
                test.set_answer(data["sdp"])
            elif data["type"] == "ice-candidate":
                test.add_ice(data["candidate"], data["sdpMLineIndex"])
            elif data["type"] == "start":
                # Trigger offer creation
                test.webrtc.emit("create-offer", None, 
                    Gst.Promise.new_with_change_func(test.on_offer_created, test.webrtc, None))
                    
    except websockets.exceptions.ConnectionClosed:
        print("👤 Client disconnected")
    finally:
        if test.pipeline:
            test.pipeline.set_state(Gst.State.NULL)

def start_server():
    async def run_server():
        async with websockets.serve(handle_client, "localhost", 8765):
            print("🌐 WebSocket: ws://localhost:8765")
            await asyncio.Future()  # run forever
    
    asyncio.run(run_server())

if __name__ == "__main__":
    print("🚀 Starting WebRTC test...")
    
    # Start WebSocket in thread
    ws_thread = threading.Thread(target=start_server)
    ws_thread.daemon = True
    ws_thread.start()
    
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("\n🛑 Bye!")