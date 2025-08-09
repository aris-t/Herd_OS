import os
import argparse
import requests
import json
import hmac
import hashlib
import time
import base64
from hashlib import md5
from utils.setup_logger import setup_logger
from tenacity import retry, stop_after_attempt, wait_fixed
import sys

# Logging setup
logger = setup_logger("Upload_Service")

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'device.cfg')
    defaults = {
        "upload_target": "10.0.0.1",
        "upload_port": 9001,
        "upload_api_endpoint": "/upload_chunk",
        "upload_api_key": "your_default_api_key",
        "upload_secret_key": "default_secret_key",
        "upload_chunk_size": 10  # MB
    }
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        upload_target = config.get("upload_target", defaults["upload_target"])
        upload_port = config.get("upload_port", defaults["upload_port"])
        upload_endpoint = config.get("upload_api_endpoint", defaults["upload_api_endpoint"])
        upload_api_key = config.get("upload_api_key", defaults["upload_api_key"])
        upload_secret_key = config.get("upload_secret_key", defaults["upload_secret_key"])
        upload_chunk_size = config.get("upload_chunk_size", defaults["upload_chunk_size"])
        device_id = config.get("device_id", "unknown_device")
        
        # Construct full URL
        if not upload_target.startswith('http'):
            upload_url = f"http://{upload_target}:{upload_port}{upload_endpoint}"
        else:
            upload_url = f"{upload_target}{upload_endpoint}"
            
        return {
            "upload_url": upload_url,
            "api_key": upload_api_key,
            "secret_key": upload_secret_key,
            "device_id": device_id,
            "chunk_size": upload_chunk_size * 1024 * 1024  # Convert MB to bytes
        }
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")
        return {
            "upload_url": f"http://{defaults['upload_target']}:{defaults['upload_port']}{defaults['upload_api_endpoint']}",
            "api_key": defaults["upload_api_key"],
            "secret_key": defaults["upload_secret_key"],
            "device_id": "unknown_device",
            "chunk_size": defaults["upload_chunk_size"] * 1024 * 1024
        }

# Load configuration values
config = load_config()
CHUNK_SIZE = config["chunk_size"]
UPLOAD_URL = os.getenv("UPLOAD_ENDPOINT", config["upload_url"])
API_KEY = os.getenv("API_KEY", config["api_key"])
SECRET_KEY = config["secret_key"]
DEVICE_ID = config["device_id"]

def generate_auth_token(device_id, timestamp=None):
    """
    Generate a cryptographically signed token that can be verified by the server.
    
    Format: device_id:timestamp:signature
    Where signature = HMAC-SHA256(device_id:timestamp, secret_key)
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Create the message to sign
    message = f"{device_id}:{timestamp}"
    
    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Create the token
    token = f"{device_id}:{timestamp}:{signature}"
    
    # Base64 encode for safe transport
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

def generate_chunks(filepath):
    filesize = os.path.getsize(filepath)
    total_chunks = (filesize + CHUNK_SIZE - 1) // CHUNK_SIZE
    with open(filepath, "rb") as f:
        for i in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)
            yield i, total_chunks, chunk_data

def md5_chunk(data):
    return md5(data).hexdigest()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def upload_chunk(filename, chunk_index, total_chunks, chunk_data):
    # Generate a fresh auth token for each request
    auth_token = generate_auth_token(DEVICE_ID)
    
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'X-Device-ID': DEVICE_ID,
        'X-Chunk-Index': str(chunk_index),
        'X-Total-Chunks': str(total_chunks),
        'X-File-Name': filename,
        'X-Chunk-MD5': md5_chunk(chunk_data),
    }
    files = {'chunk': (f"{filename}.part{chunk_index}", chunk_data)}

    logger.info(f"Uploading chunk {chunk_index + 1}/{total_chunks}")
    
    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"✅ Chunk {chunk_index + 1}/{total_chunks} uploaded successfully")
        
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection failed for chunk {chunk_index + 1}/{total_chunks} - server unreachable")
        raise
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout for chunk {chunk_index + 1}/{total_chunks}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error for chunk {chunk_index + 1}/{total_chunks}: {e.response.status_code} - {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed for chunk {chunk_index + 1}/{total_chunks}: {str(e)}")
        raise

def upload_file_in_chunks(filepath):
    server_avalible = False
    try:
        if not os.path.exists(filepath):
            logger.error(f"❌ File not found: {filepath}")
            return False
            
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            file_md5 = md5(f.read()).hexdigest()
        logger.info(f"\nMD5: '{filename}': {file_md5}")
        
        # Test server connectivity first
        try:
            test_response = requests.get(UPLOAD_URL.replace('/upload_chunk', '/health'), timeout=10)
            server_avalible = True
            logger.info("✅ Server is reachable")
        except requests.exceptions.RequestException:
            logger.warning("⚠️  Could not verify server health...")

        if server_avalible:
            uploaded_chunks = 0
            total_chunks = None
            
            for index, total, chunk in generate_chunks(filepath):
                total_chunks = total
                try:
                    upload_chunk(filename, index, total, chunk)
                    uploaded_chunks += 1
                except Exception as e:
                    logger.error(f"❌ Failed to upload chunk {index + 1}/{total} after all retries: {str(e)}")
                    logger.error(f"Upload stopped. {uploaded_chunks}/{total_chunks} chunks uploaded successfully")
                    return False
            
            logger.info(f"✅ All {total_chunks} chunks uploaded successfully")
            return True
        else:
            logger.error("❌ Server is not reachable. Upload aborted.")
            return False
        
    except FileNotFoundError:
        logger.error(f"❌ File not found: {filepath}")
        return False
    except PermissionError:
        logger.error(f"❌ Permission denied accessing file: {filepath}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during upload: {str(e)}")
        return False