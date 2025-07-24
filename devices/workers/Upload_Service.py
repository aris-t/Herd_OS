import os
import argparse
import logging
import requests
from hashlib import md5
from tenacity import retry, stop_after_attempt, wait_fixed

# Configuration
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
UPLOAD_URL = os.getenv("UPLOAD_ENDPOINT", "http://192.168.1.5:9001/upload_chunk")
API_KEY = os.getenv("API_KEY", "your_default_api_key")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChunkUploader")

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
    response = requests.post(UPLOAD_URL, files=files, headers=headers)
    response.raise_for_status()

def upload_file_in_chunks(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_md5 = md5(f.read()).hexdigest()
    logger.info(f"\nMD5: '{filename}': {file_md5}")
    for index, total, chunk in generate_chunks(filepath):
        upload_chunk(filename, index, total, chunk)
    logger.info("✅ All chunks uploaded")

def main():
    parser = argparse.ArgumentParser(description="Chunked upload for large files.")
    parser.add_argument("filepath", help="Path to the file to upload")
    args = parser.parse_args()
    upload_file_in_chunks(args.filepath)

if __name__ == "__main__":
    main()
