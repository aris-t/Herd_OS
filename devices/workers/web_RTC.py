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
from .worker import Worker

Gst.init(None)

class WebRTCFactory:
    def __init__(self, socket_path="/tmp/testshm"):
        self.socket_path = socket_path
        self.pipeline = None
        self.webrtc = None
        self.ice_candidates = []
        self.websocket = None
        
    def create_pipeline(self):
        pipeline_str = (
            f"shmsrc socket-path={self.socket_path} do-timestamp=true is-live=true ! "
            "video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "vp8enc deadline=1 target-bitrate=2000000 ! "
            "rtpvp8pay ! "
            "webrtcbin name=webrtc"
        )
        
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.webrtc = self.pipeline.get_by_name("webrtc")
        
        # Connect WebRTC signals
        self.webrtc.connect("on-negotiation-needed", self.on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self.on_ice_candidate)
        self.webrtc.connect("on-ice-gathering-state-notify", self.on_ice_gathering_state_notify)
        
        return self.pipeline
    
    def on_negotiation_needed(self, webrtc):
        print("📡 Creating offer...")
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, webrtc, None)
        webrtc.emit("create-offer", None, promise)
    
    def on_offer_created(self, promise, webrtc, user_data):
        reply = promise.get_reply()
        offer = reply.get_value("offer")
        
        promise = Gst.Promise.new()
        webrtc.emit("set-local-description", offer, promise)
        
        # Send offer to client
        self.send_offer(offer)
    
    def on_ice_candidate(self, webrtc, mlineindex, candidate):
        print(f"🧊 ICE candidate: {candidate}")
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({
                    "type": "ice-candidate",
                    "candidate": candidate,
                    "sdpMLineIndex": mlineindex
                })),
                asyncio.get_event_loop()
            )
    
    def on_ice_gathering_state_notify(self, webrtc, pspec):
        state = webrtc.get_property("ice-gathering-state")
        print(f"🧊 ICE gathering state: {state}")
    
    def send_offer(self, offer):
        if self.websocket:
            sdp_text = offer.sdp.as_text()
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({
                    "type": "offer",
                    "sdp": sdp_text
                })),
                asyncio.get_event_loop()
            )
    
    def set_remote_description(self, sdp_text):
        print("📥 Setting remote description...")
        sdp = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(sdp_text.encode(), sdp)
        answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdp)
        
        promise = Gst.Promise.new()
        self.webrtc.emit("set-remote-description", answer, promise)
    
    def add_ice_candidate(self, candidate, sdp_mline_index):
        print(f"🧊 Adding ICE candidate: {candidate}")
        self.webrtc.emit("add-ice-candidate", sdp_mline_index, candidate)
    
    def start(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PLAYING)
            print("▶️  Pipeline started")
    
    def stop(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            print("⏹️  Pipeline stopped")

class Camera_WebRTC(Worker):
    def __init__(self, device, name, DEBUG=False):
        super().__init__(device, name)
        self.DEBUG = DEBUG
        self.device = device
        self.webrtc_factory = WebRTCFactory()
        self.server = None
        self.clients = set()
        
    async def handle_client(self, websocket, path):
        print(f"👤 Client connected: {websocket.remote_address}")
        self.clients.add(websocket)
        
        try:
            # Create new pipeline for this client
            factory = WebRTCFactory()
            factory.websocket = websocket
            pipeline = factory.create_pipeline()
            factory.start()
            
            async for message in websocket:
                data = json.loads(message)
                
                if data["type"] == "answer":
                    factory.set_remote_description(data["sdp"])
                elif data["type"] == "ice-candidate":
                    factory.add_ice_candidate(
                        data["candidate"], 
                        data["sdpMLineIndex"]
                    )
                elif data["type"] == "start":
                    # Trigger negotiation
                    factory.webrtc.emit("create-offer", None, 
                        Gst.Promise.new_with_change_func(
                            factory.on_offer_created, 
                            factory.webrtc, 
                            None
                        )
                    )
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"👤 Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
            if 'factory' in locals():
                factory.stop()
    
    def start_websocket_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.server = websockets.serve(
            self.handle_client, 
            self.device.ip, 
            8765
        )
        
        print(f"🌐 WebSocket server running at ws://{self.device.ip}:8765")
        loop.run_until_complete(self.server)
        loop.run_forever()
    
    def run(self):
        print(f"🚀 Starting WebRTC server on {self.device.ip}")
        
        # Start WebSocket server in a separate thread
        ws_thread = threading.Thread(target=self.start_websocket_server)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Keep the main thread alive
        try:
            GLib.MainLoop().run()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.stop()
    
    def stop(self):
        self.is_stopped.value = True
        if self.server:
            self.server.close()
        print("✅ WebRTC server stopped")

"""
from your_module import Camera_WebRTC, Device

device = Device(ip="192.168.1.50")
camera = Camera_WebRTC(device, "test_camera", DEBUG=True)
camera.run()
"""

"""
import React, { useState, useRef, useEffect } from 'react';

const WebRTCPlayer = ({ serverUrl = 'ws://192.168.1.50:8765' }) => {
  const [status, setStatus] = useState('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  const videoRef = useRef(null);
  const websocketRef = useRef(null);
  const peerConnectionRef = useRef(null);

  const servers = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  const connect = async () => {
    try {
      setStatus('connecting');
      
      // Create WebSocket connection
      websocketRef.current = new WebSocket(serverUrl);
      
      websocketRef.current.onopen = async () => {
        console.log('WebSocket connected');
        
        // Create peer connection
        peerConnectionRef.current = new RTCPeerConnection(servers);
        
        peerConnectionRef.current.onicecandidate = (event) => {
          if (event.candidate && websocketRef.current) {
            websocketRef.current.send(JSON.stringify({
              type: 'ice-candidate',
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex
            }));
          }
        };
        
        peerConnectionRef.current.ontrack = (event) => {
          console.log('Received remote stream');
          if (videoRef.current) {
            videoRef.current.srcObject = event.streams[0];
          }
          setStatus('connected');
          setIsConnected(true);
        };
        
        peerConnectionRef.current.onconnectionstatechange = () => {
          console.log('Connection state:', peerConnectionRef.current.connectionState);
          if (peerConnectionRef.current.connectionState === 'failed') {
            setStatus('failed');
            disconnect();
          }
        };
        
        // Request stream
        websocketRef.current.send(JSON.stringify({ type: 'start' }));
      };
      
      websocketRef.current.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'offer') {
          console.log('Received offer');
          await peerConnectionRef.current.setRemoteDescription({
            type: 'offer',
            sdp: data.sdp
          });
          
          const answer = await peerConnectionRef.current.createAnswer();
          await peerConnectionRef.current.setLocalDescription(answer);
          
          websocketRef.current.send(JSON.stringify({
            type: 'answer',
            sdp: answer.sdp
          }));
        } else if (data.type === 'ice-candidate') {
          console.log('Received ICE candidate');
          await peerConnectionRef.current.addIceCandidate({
            candidate: data.candidate,
            sdpMLineIndex: data.sdpMLineIndex
          });
        }
      };
      
      websocketRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus('disconnected');
        setIsConnected(false);
      };
      
      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('Connection error:', error);
      setStatus('error');
    }
  };

  const disconnect = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStatus('disconnected');
    setIsConnected(false);
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'connected': return '#28a745';
      case 'connecting': return '#ffc107';
      case 'error': 
      case 'failed': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>WebRTC SHM Stream</h2>
      
      <div style={{ 
        padding: '10px', 
        borderRadius: '5px', 
        backgroundColor: getStatusColor(), 
        color: 'white',
        marginBottom: '20px'
      }}>
        Status: {status}
      </div>
      
      <video 
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ 
          width: '100%', 
          maxWidth: '640px', 
          border: '1px solid #ccc',
          borderRadius: '5px'
        }}
      />
      
      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={connect} 
          disabled={isConnected}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            marginRight: '10px',
            backgroundColor: isConnected ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isConnected ? 'not-allowed' : 'pointer'
          }}
        >
          Connect
        </button>
        
        <button 
          onClick={disconnect} 
          disabled={!isConnected}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: !isConnected ? '#ccc' : '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: !isConnected ? 'not-allowed' : 'pointer'
          }}
        >
          Disconnect
        </button>
      </div>
    </div>
  );
};

export default WebRTCPlayer;
"""

"""
<!DOCTYPE html>
<html>
<head>
    <title>WebRTC SHM Stream</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        video { width: 100%; max-width: 640px; border: 1px solid #ccc; }
        button { margin: 10px; padding: 10px 20px; font-size: 16px; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
        .connecting { background-color: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <h1>WebRTC SHM Stream Viewer</h1>
    
    <div id="status" class="status disconnected">Disconnected</div>
    
    <video id="videoElement" autoplay playsinline muted></video>
    
    <div>
        <button id="connectBtn" onclick="connect()">Connect</button>
        <button id="disconnectBtn" onclick="disconnect()" disabled>Disconnect</button>
    </div>

    <script>
        const videoElement = document.getElementById('videoElement');
        const statusDiv = document.getElementById('status');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        
        let websocket = null;
        let peerConnection = null;
        
        const servers = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        function updateStatus(message, className) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${className}`;
        }
        
        function connect() {
            updateStatus('Connecting...', 'connecting');
            connectBtn.disabled = true;
            
            // Connect to WebSocket
            websocket = new WebSocket('ws://192.168.1.50:8765');
            
            websocket.onopen = async () => {
                console.log('WebSocket connected');
                
                // Create peer connection
                peerConnection = new RTCPeerConnection(servers);
                
                peerConnection.onicecandidate = (event) => {
                    if (event.candidate) {
                        websocket.send(JSON.stringify({
                            type: 'ice-candidate',
                            candidate: event.candidate.candidate,
                            sdpMLineIndex: event.candidate.sdpMLineIndex
                        }));
                    }
                };
                
                peerConnection.ontrack = (event) => {
                    console.log('Received remote stream');
                    videoElement.srcObject = event.streams[0];
                    updateStatus('Connected', 'connected');
                    disconnectBtn.disabled = false;
                };
                
                peerConnection.onconnectionstatechange = () => {
                    console.log('Connection state:', peerConnection.connectionState);
                    if (peerConnection.connectionState === 'failed') {
                        updateStatus('Connection failed', 'disconnected');
                        disconnect();
                    }
                };
                
                // Request stream
                websocket.send(JSON.stringify({ type: 'start' }));
            };
            
            websocket.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'offer') {
                    console.log('Received offer');
                    await peerConnection.setRemoteDescription({
                        type: 'offer',
                        sdp: data.sdp
                    });
                    
                    const answer = await peerConnection.createAnswer();
                    await peerConnection.setLocalDescription(answer);
                    
                    websocket.send(JSON.stringify({
                        type: 'answer',
                        sdp: answer.sdp
                    }));
                } else if (data.type === 'ice-candidate') {
                    console.log('Received ICE candidate');
                    await peerConnection.addIceCandidate({
                        candidate: data.candidate,
                        sdpMLineIndex: data.sdpMLineIndex
                    });
                }
            };
            
            websocket.onclose = () => {
                console.log('WebSocket disconnected');
                updateStatus('Disconnected', 'disconnected');
                connectBtn.disabled = false;
                disconnectBtn.disabled = true;
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateStatus('Connection error', 'disconnected');
                connectBtn.disabled = false;
            };
        }
        
        function disconnect() {
            if (websocket) {
                websocket.close();
            }
            if (peerConnection) {
                peerConnection.close();
            }
            videoElement.srcObject = null;
            updateStatus('Disconnected', 'disconnected');
            connectBtn.disabled = false;
            disconnectBtn.disabled = true;
        }
    </script>
</body>
</html>
"""