from fastapi import FastAPI, File, UploadFile
import shutil
import uuid
import os
from fastapi import Form

app = FastAPI()
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

VideoQueue = []  # Simple queue to hold video processing tasks

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    animalID: str = Form(...),
    trialID: str = Form(...),
    deviceID: str = Form(...)
):
    video_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{video_id}.mp4"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store metadata with the video (example: add to queue)
    VideoQueue.append({
        "video_id": video_id,
        "file_path": file_path,
        "animalID": animalID,
        "trialID": trialID,
        "deviceID": deviceID
    })

    # Trigger processing asynchronously
    process_video_async(file_path, video_id)
    return {
        "status": "processing",
        "id": video_id,
        "animalID": animalID,
        "trialID": trialID,
        "deviceID": deviceID
    }

# Animal Management Endpoints
@app.get("/animals")
async def list_animals():
    # Simulate a database of animals
    animals = [
        {"id": "1", "name": "Lion", "age": 5},
        {"id": "2", "name": "Tiger", "age": 4},
        {"id": "3", "name": "Elephant", "age": 10},
    ]
    return animals

@app.get("/animals/{animal_id}")
async def get_animal(animal_id: str):
    # Simulate a database lookup
    animal = {"id": animal_id, "name": "Lion", "age": 5}
    return animal

@app.get("/animals/{animal_id}/trials")
async def list_trials(animal_id: str):
    # Simulate a database of trials for the animal
    trials = [
        {"trial_id": "trial1", "date": "2023-10-01"},
        {"trial_id": "trial2", "date": "2023-10-02"},
    ]
    return trials

@app.get("/animals/{animal_id}/{trial}")
async def get_animal(animal_id: str, trial: str):
    # Simulate a database lookup
    animal = {"id": animal_id, "name": "Lion", "age": 5}
    return animal


# Updates
@app.get("/status")
async def get_status():
    return {"status": "ok"}


@app.get("/queue")
async def get_queue():
    return {"queue": Queue}


@app.get("/changelog")
async def get_changelog():
    changelog = [
        {"version": "1.0.0", "changes": "Initial release with video upload and animal management."},
        {"version": "1.1.0", "changes": "Added queue management for video processing."},
        {"version": "1.2.0", "changes": "Improved error handling and logging."},
    ]
    return changelog