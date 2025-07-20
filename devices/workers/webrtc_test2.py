#!/usr/bin/env python3

import asyncio
import json
import websockets
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")
from gi.repository import Gst, GstWebRTC, GLib

Gst.init(None)


class WebRTCStreamer:
    def __init__(self):
        self.pipe = None
        self.webrtc = None

    def start_pipeline(self):
        pipeline = Gst.parse_launch(
            "shmsrc socket-path=/tmp/testshm do-timestamp=true is-live=true ! "
            "video/x-raw,format=I420,width=2304,height=1296,framerate=30/1 ! "
            "videoconvert ! queue ! "
            "vp8enc deadline=1 ! rtpvp8pay ! "
            "application/x-rtp,media=video,encoding-name=VP8,payload=96 ! "
            "webrtcbin name=webrtcbin stun-server=stun://stun.l.google.com:19302"
        )

        self.pipe = pipeline
        self.webrtc = pipeline.get_by_name("webrtcbin")

        self.webrtc.connect("on-negotiation-needed", self.on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self.send_ice_candidate_message)

        pipeline.set_state(Gst.State.PLAYING)

    async def on_offer_created(self, promise):
        reply = promise.get_reply()
        offer = reply.get_value("offer")
        self.webrtc.emit("set-local-description", offer, None)
        text = offer.sdp.as_text()
        await self.send_sdp("offer", text)

    def on_negotiation_needed(self, element):
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, None)
        element.emit("create-offer", None, promise)

    def send_ice_candidate_message(self, element, mlineindex, candidate):
        message = json.dumps({
            "ice": {
                "candidate": candidate,
                "sdpMLineIndex": mlineindex,
            }
        })
        asyncio.ensure_future(self.ws.send(message))

    async def send_sdp(self, kind, sdp):
        message = json.dumps({
            kind: {
                "type": kind,
                "sdp": sdp,
            }
        })
        await self.ws.send(message)

    async def consume_signaling(self, ws):
        self.ws = ws
        async for msg in ws:
            data = json.loads(msg)
            if "answer" in data:
                sdp = data["answer"]["sdp"]
                answer = Gst.SDPMessage.new()
                Gst.SDPMessage.parse_buffer(sdp.encode(), answer)
                desc = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, answer)
                self.webrtc.emit("set-remote-description", desc, None)
            elif "ice" in data:
                candidate = data["ice"]["candidate"]
                sdp_mline_index = data["ice"]["sdpMLineIndex"]
                self.webrtc.emit("add-ice-candidate", sdp_mline_index, candidate)

    async def start_signaling(self, signaling_url):
        async with websockets.connect(signaling_url) as ws:
            await self.consume_signaling(ws)


def main():
    streamer = WebRTCStreamer()
    streamer.start_pipeline()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(streamer.start_signaling("ws://localhost:8443/ws"))
    loop.run_forever()


if __name__ == "__main__":
    main()
