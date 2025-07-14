import os, requests

def upload_file_in_chunks(filepath, url, chunk_size=5 * 1024 * 1024):
    with open(filepath, 'rb') as f:
        i = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            try:
                r = requests.post(
                    url,
                    files={"chunk": chunk},
                    data={"index": i}
                )
                r.raise_for_status()
            except Exception as e:
                print(f"Retry chunk {i} due to {e}")
                f.seek(i * chunk_size)
                continue
            i += 1