from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import logging
import os
import json

def is_device_authorized(device_id: str) -> bool:
    """Check if device_id is in the authorized users list."""
    try:
        with open("users.txt", "r") as f:
            authorized_devices = [line.strip() for line in f if line.strip()]
        return device_id in authorized_devices
    except FileNotFoundError:
        return False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="File Server and Message Receiver")

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

class Message(BaseModel):
    device_id: str
    message: str

class GetFileRequest(BaseModel):
    device_id: str
    filename: str

@app.get("/")
async def root():
    return {"message": "Server OK."}

@app.post("/messages")
async def receive_message(message: Message):
    logger.info(f"Received message from device {message.device_id}: {message.message}")
    return JSONResponse(content={"status": "received", "device_id": message.device_id})



@app.get("/listfiles")
async def list_files(device_id: str):
    # Check if device_id is authorized
    if not is_device_authorized(device_id):
        return JSONResponse(status_code=403, content={"error": "Not Permitted"})

    try:
        with open("files.json", "r") as f:
            files = json.load(f)
        return JSONResponse(content=files)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="files.json not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing files.json")

@app.post("/getfile")
async def get_file(request: GetFileRequest):
    # Check if device_id is authorized
    if not is_device_authorized(request.device_id):
        return JSONResponse(status_code=403, content={"error": "Not Permitted"})

    file_path = f"static/{request.filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    logger.info(f"Device {request.device_id} requested file {request.filename}")
    return FileResponse(path=file_path, filename=request.filename, media_type='application/octet-stream')
