#!/usr/bin/env python3
"""
Authentication Token Verifier for Upload Service

This utility helps verify the cryptographically signed tokens sent by devices.
The server should use this to validate incoming upload requests.
"""

import hmac
import hashlib
import base64
import time
import json
import os

def load_device_secrets(config_path=None):
    """
    Load device secrets from config file.
    In production, this should be stored securely on the server.
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'device.cfg')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return {
            "secret_key": config.get("upload_secret_key"),
            "known_devices": [config.get("device_id")]  # In production, this would be a database
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def verify_auth_token(token, max_age_seconds=300):
    """
    Verify an authentication token from a device.
    
    Args:
        token (str): Base64 encoded token from Authorization header
        max_age_seconds (int): Maximum age of token to prevent replay attacks
    
    Returns:
        dict: {"valid": bool, "device_id": str, "error": str}
    """
    try:
        # Load server-side secrets
        secrets = load_device_secrets()
        if not secrets:
            return {"valid": False, "device_id": None, "error": "Server configuration error"}
        
        secret_key = secrets["secret_key"]
        known_devices = secrets["known_devices"]
        
        # Decode the token
        try:
            decoded_token = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        except Exception:
            return {"valid": False, "device_id": None, "error": "Invalid token encoding"}
        
        # Parse token components: device_id:timestamp:signature
        parts = decoded_token.split(':')
        if len(parts) != 3:
            return {"valid": False, "device_id": None, "error": "Invalid token format"}
        
        device_id, timestamp_str, provided_signature = parts
        
        # Check if device is known
        if device_id not in known_devices:
            return {"valid": False, "device_id": device_id, "error": "Unknown device"}
        
        # Validate timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return {"valid": False, "device_id": device_id, "error": "Invalid timestamp"}
        
        current_time = int(time.time())
        if current_time - timestamp > max_age_seconds:
            return {"valid": False, "device_id": device_id, "error": "Token expired"}
        
        if timestamp > current_time + 60:  # Allow 60 seconds clock skew
            return {"valid": False, "device_id": device_id, "error": "Token from future"}
        
        # Verify signature
        message = f"{device_id}:{timestamp}"
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(provided_signature, expected_signature):
            return {"valid": False, "device_id": device_id, "error": "Invalid signature"}
        
        return {"valid": True, "device_id": device_id, "error": None}
        
    except Exception as e:
        return {"valid": False, "device_id": None, "error": f"Verification error: {str(e)}"}

def test_token_system():
    """Test the token generation and verification system"""
    print("Testing Authentication Token System...")
    
    # Import the token generator
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'devices', 'workers'))
    
    try:
        from devices.workers.Upload_Service import generate_auth_token, DEVICE_ID
        
        # Generate a token
        token = generate_auth_token(DEVICE_ID)
        print(f"Generated token: {token}")
        
        # Verify the token
        result = verify_auth_token(token)
        print(f"Verification result: {result}")
        
        if result["valid"]:
            print("✅ Token system is working correctly!")
        else:
            print(f"❌ Token verification failed: {result['error']}")
            
    except ImportError as e:
        print(f"❌ Could not import Upload_Service: {e}")

if __name__ == "__main__":
    test_token_system()
