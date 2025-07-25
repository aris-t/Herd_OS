import os
import argparse
import requests
from hashlib import md5
from utils.setup_logger import setup_logger
from tenacity import retry, stop_after_attempt, wait_fixed
import sys

# Logging setup
logger = setup_logger("Upload_Service")

# Configuration
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
UPLOAD_URL = os.getenv("UPLOAD_ENDPOINT", "http://192.168.1.10:9001/upload_chunk")
API_KEY = os.getenv("API_KEY", "your_default_api_key")

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
    headers = {
        'Authorization': f'Bearer {API_KEY}',
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
            logger.info("✅ Server is reachable")
        except requests.exceptions.RequestException:
            logger.warning("⚠️  Could not verify server health, proceeding anyway...")
        
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
        
    except FileNotFoundError:
        logger.error(f"❌ File not found: {filepath}")
        return False
    except PermissionError:
        logger.error(f"❌ Permission denied accessing file: {filepath}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during upload: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Chunked upload for large files.")
    parser.add_argument("filepath", help="Path to the file to upload")
    args = parser.parse_args()
    
    success = upload_file_in_chunks(args.filepath)
    if not success:
        logger.error("❌ Upload failed")
        sys.exit(1)
    else:
        logger.info("✅ Upload completed successfully")

if __name__ == "__main__":
    main()