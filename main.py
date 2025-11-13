from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
import json
import uuid
import random
import string

def is_device_authorized(username: str, device_id: str) -> bool:
    """Check if username and device_id match in deviceid.json."""
    try:
        with open("deviceid.json", "r") as f:
            device_data = json.load(f)
        return device_data.get(username) == device_id
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="File Server and Message Receiver")

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

class Message(BaseModel):
    username: str
    device_id: str
    Error: Optional[str] = None
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CheckRequest(BaseModel):
    username: str
    location: str

class GetFileRequest(BaseModel):
    username: str
    device_id: str
    filename: str

@app.get("/")
async def root():
    return {"message": "Server OK."}

@app.post("/messages")
async def receive_message(message: Message):
    # Check if username and device_id are authorized
    if not is_device_authorized(message.username, message.device_id):
        # Remove the pair if it exists
        try:
            with open("deviceid.json", "r") as f:
                device_data = json.load(f)
            if message.username in device_data:
                del device_data[message.username]
                with open("deviceid.json", "w") as f:
                    json.dump(device_data, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": "Not Authorized", "Message": None})
    if (message.Error!="None"):
        try:
            with open("deviceid.json", "r") as f:
                device_data = json.load(f)
            if message.username in device_data:
                del device_data[message.username]
                with open("deviceid.json", "w") as f:
                    json.dump(device_data, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": None, "Message": "Received the error '"+message.Error+"'"})
    logger.info(f"Received message from user {message.username} device {message.device_id}: Error {message.Error} {message.message}")
    return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": None, "Message": "Message '"+message.message+ "' Received"})

@app.post("/login")
async def login(request: LoginRequest):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return JSONResponse(status_code=500, content={"login": "fail", "error": "Server error"})

    if request.username in users and users[request.username] == request.password:
        # Generate a random 6-letter string as device_id
        device_id = ''.join(random.choices(string.ascii_letters, k=6))
        # Update deviceid.json
        try:
            with open("deviceid.json", "r") as f:
                device_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            device_data = {}

        device_data[request.username] = device_id
        with open("deviceid.json", "w") as f:
            json.dump(device_data, f)

        return JSONResponse(content={"login": "pass", "error": None})
    else:
        return JSONResponse(content={"login": "fail", "error": "Wrong username or password"})

@app.post("/check")
async def check_location(request: CheckRequest):
    # For now, always true
    if True:
        try:
            with open("deviceid.json", "r") as f:
                device_data = json.load(f)
            device_id = device_data.get(request.username)
            if device_id:
                return JSONResponse(content={"Error": None, "device_id": device_id})
            else:
                return JSONResponse(content={"Error": "User not found", "device_id": None})
        except (FileNotFoundError, json.JSONDecodeError):
            return JSONResponse(content={"Error": "Server error", "device_id": None})
    else:
        # Remove the pair if it exists (by username only)
        try:
            with open("deviceid.json", "r") as f:
                device_data = json.load(f)
            if request.username in device_data:
                del device_data[request.username]
                with open("deviceid.json", "w") as f:
                    json.dump(device_data, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return JSONResponse(content={"Error": "Location Check Failed", "device_id": None})

@app.get("/listfiles")
async def list_files(username: str, device_id: str):
    # Check if username and device_id are authorized
    if not is_device_authorized(username, device_id):
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
    # Check if username and device_id are authorized
    if not is_device_authorized(request.username, request.device_id):
        return JSONResponse(status_code=403, content={"error": "Not Permitted"})

    file_path = f"static/{request.filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    logger.info(f"User {request.username} with device {request.device_id} requested file {request.filename}")
    return FileResponse(path=file_path, filename=request.filename, media_type='application/octet-stream')
