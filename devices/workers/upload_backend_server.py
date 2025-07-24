# uvicorn upload_backend_server:app --reload

import os
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.responses import JSONResponse
from hashlib import md5
from typing import Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChunkedUploadServer")

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
CHUNKS_DIR = UPLOAD_DIR / "chunks"
CHUNKS_DIR.mkdir(exist_ok=True)

@app.post("/upload_chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    x_chunk_index: int = Header(...),
    x_total_chunks: int = Header(...),
    x_file_name: str = Header(...),
    x_chunk_md5: Optional[str] = Header(None),
):
    try:
        file_base = Path(x_file_name).name
        chunk_dir = CHUNKS_DIR / file_base
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_path = chunk_dir / f"{x_chunk_index}.part"
        content = await chunk.read()

        if x_chunk_md5:
            actual_md5 = md5(content).hexdigest()
            if actual_md5 != x_chunk_md5:
                raise HTTPException(status_code=400, detail="MD5 checksum mismatch")

        with open(chunk_path, "wb") as f:
            f.write(content)

        # Check if all chunks received
        received_chunks = list(chunk_dir.glob("*.part"))
        if len(received_chunks) == x_total_chunks:
            logger.info(f"✅ All chunks received for {x_file_name}. Reassembling...")
            output_path = UPLOAD_DIR / file_base
            with open(output_path, "wb") as outfile:
                for i in range(x_total_chunks):
                    part_path = chunk_dir / f"{i}.part"
                    with open(part_path, "rb") as infile:
                        outfile.write(infile.read())
            # Calculate MD5 of the reassembled file
            with open(output_path, "rb") as f:
                file_md5 = md5(f.read()).hexdigest()
            # Optional: clean up chunk files
            for part in received_chunks:
                part.unlink()
            chunk_dir.rmdir()
            logger.info(f"\nMD5: {x_file_name}: {file_md5}")
            return JSONResponse(content={"status": "ok", "md5": file_md5})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
