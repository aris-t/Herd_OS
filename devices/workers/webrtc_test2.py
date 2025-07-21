#!/usr/bin/env python3

import asyncio
import websockets
import gi
import json

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")
gi.require_version("GstSdp", "1.0")
from gi.repository import Gst, GstWebRTC, GstSdp

Gst.init(None)

PIPELINE_DESC = '''
videotestsrc is-live=true pattern=ball !
videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay pt=96 name=pay
webrtcbin name=sendrecv bundle-policy=max-bundle
'''


class WebRTCStreamer:
    def __init__(self, signaling_url):
        self.signaling_url = signaling_url
        self.pipe = None
        self.webrtc = None
        self.ws = None

    async def start(self):
        self.ws = await websockets.connect(self.signaling_url)
        print("🔗 Connected to signaling server")
        await self.loop()

    def on_negotiation_needed(self, element):
        print("📡 Negotiation needed")
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, None)
        element.emit("create-offer", None, promise)

    def on_offer_created(self, promise, element, _):
        print("📄 SDP offer created")
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value("offer")
        element.emit("set-local-description", offer, None)
        sdp = offer.sdp.as_text()
        msg = json.dumps({"offer": {"type": "offer", "sdp": sdp}})
        asyncio.get_event_loop().create_task(self.ws.send(msg))

    def on_ice_candidate(self, _, mlineindex, candidate):
        msg = json.dumps({
            "ice": {
                "candidate": candidate,
                "sdpMLineIndex": mlineindex
            }
        })
        asyncio.get_event_loop().create_task(self.ws.send(msg))

    async def handle_sdp(self, data):
        if "answer" in data:
            print("📄 Received SDP answer")
            sdp = data["answer"]["sdp"]
            res, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(
                GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            self.webrtc.emit("set-remote-description", answer, None)
            
                # Link payloader to webrtcbin once remote SDP is set
            pay = self.pipe.get_by_name("pay")
            pay_src = pay.get_static_pad("src")
            sinkpad = self.webrtc.get_request_pad("sink_%u")
            if sinkpad and pay_src:
                result = pay_src.link(sinkpad)
                print("🔗 Linked pay to webrtcbin:", result)
            else:
                print("❌ Could not link pay to webrtcbin")



        elif "ice" in data:
            ice = data["ice"]
            self.webrtc.emit("add-ice-candidate", ice["sdpMLineIndex"], ice["candidate"])

    async def loop(self):
        async for msg in self.ws:
            data = json.loads(msg)
            await self.handle_sdp(data)

    def start_pipeline(self):
        self.pipe = Gst.parse_launch(PIPELINE_DESC)
        self.webrtc = self.pipe.get_by_name("sendrecv")

        self.webrtc.connect("on-negotiation-needed", self.on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self.on_ice_candidate)

        self.pipe.set_state(Gst.State.PLAYING)
        print("✅ Pipeline running. Waiting for signaling...")

def main():
    signaling_url = "ws://192.168.1.50:8443"  # Update as needed
    streamer = WebRTCStreamer(signaling_url)
    streamer.start_pipeline()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(streamer.start())

if __name__ == "__main__":
    main()
