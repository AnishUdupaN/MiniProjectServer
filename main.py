
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
from dotenv import load_dotenv
from shapely.geometry import Point, Polygon
import aiofiles
# Set up logging to log.log
logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    latitude: str
    longitude: str
    altitude: str

class ShaRequest(BaseModel):
    username: str
    sha256: str

class CheckFailed(BaseModel):
    username: str
    message: str

class GetFileRequest(BaseModel):
    username: str
    device_id: str
    filename: str


async def location_check(latitude,longitude):
    #use https://www.map-tools.com/coordinates to get the coordinates of points of an polygon easily
    async with aiofiles.open("areamap.json", "r") as f:
        content = await f.read()
        poly_coords_dict = json.loads(content)
    polygon_vertices = []
    for lat_str, lon_str in poly_coords_dict.items():
        lon_float = float(lon_str)
        lat_float = float(lat_str)
        polygon_vertices.append((lon_float, lat_float)) # Append as (lon, lat)

    test_point_tuple = (longitude,latitude) # Store as (lon, lat)
    polygon = Polygon(polygon_vertices)
    point = Point(test_point_tuple)
    is_inside = polygon.contains(point)
    touches_boundary = polygon.touches(point)
    if is_inside:
        return True
    elif touches_boundary:
        return True
    else:
        return False

def sha_check(sha256):
    #Function to check if the given hash matches to that of the original one.
    # get the sha256 by using "keytool -list -v -keystore ~/Public/Public/Mini\ Project/keypasswordispassword.jks"
    #look for sha256 hash and remove the ":" and convert it into lower case.
    load_dotenv()
    hash=os.getenv("HASH")
    hash=(hash.replace(":","")).lower()
    if hash==sha256:
        return True
    else:
        return False


async def is_device_authorized(username: str, device_id: str) -> bool:
    """Check if username and device_id match in deviceid.json."""
    try:
        async with aiofiles.open("deviceid.json", "r") as f:
            content = await f.read()
            device_data = json.loads(content)
        return device_data.get(username) == device_id
    except (FileNotFoundError, json.JSONDecodeError):
        return False



@app.get("/")
async def root():
    return {"message": "Server OK."}

@app.post("/messages")
async def receive_message(message: Message):
    logger.info(f"User {message.username}: Received message input - device_id: {message.device_id}, Error: {message.Error}, message: {message.message}")
    # Check if username and device_id are authorized
    if not await is_device_authorized(message.username, message.device_id):
        logger.warning(f"User {message.username}: Malpractice - Wrong device_id: {message.device_id}")
        # Remove the pair if it exists
        try:
            async with aiofiles.open("deviceid.json", "r") as f:
                content = await f.read()
                device_data = json.loads(content)
            if message.username in device_data:
                del device_data[message.username]
                async with aiofiles.open("deviceid.json", "w") as f:
                    await f.write(json.dumps(device_data))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"User {message.username}: Error removing device pair - {str(e)}")
        return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": "Not Authorized", "Message": None})
    if (message.Error!="None"):
        logger.warning(f"User {message.username}: Malpractice - Client reported error: {message.Error}")
        #the client is reporting the device check failure status
        try:
            async with aiofiles.open("deviceid.json", "r") as f:
                content = await f.read()
                device_data = json.loads(content)
            if message.username in device_data:
                del device_data[message.username]
                async with aiofiles.open("deviceid.json", "w") as f:
                    await f.write(json.dumps(device_data))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"User {message.username}: Error removing device pair on error report - {str(e)}")
        return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": None, "Message": "Received the error '"+message.Error+"'"})
    logger.info(f"User {message.username}: Message received successfully: {message.message}")
    return JSONResponse(content={"username": message.username, "device_id": message.device_id, "Error": None, "Message": "Message '"+message.message+ "' Received"})

@app.post("/login")
async def login(request: LoginRequest):
    logger.info(f"User {request.username}: Login attempt with password")
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"User {request.username}: Error loading users.json - {str(e)}")
        return JSONResponse(status_code=500, content={"login": "fail", "error": "Server error"})

    if request.username in users and users[request.username] == request.password:
        logger.info(f"User {request.username}: Login successful")
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
        logger.warning(f"User {request.username}: Login failed - Wrong username or password")
        return JSONResponse(content={"login": "fail", "error": "Wrong username or password"})

@app.post("/checklocation")
async def check_location(request: CheckRequest):
    logger.info(f"User {request.username}: Location check input - lat: {request.latitude}, lon: {request.longitude}, alt: {request.altitude}")
    # altitude is an additional information which has no use as of now
    print("Location:",request.latitude,request.longitude,request.altitude)
    if await location_check(float(request.latitude),float(request.longitude)):
        logger.info(f"User {request.username}: Location check passed")
        try:
            async with aiofiles.open("deviceid.json", "r") as f:
                content = await f.read()
                device_data = json.loads(content)
            device_id = device_data.get(request.username)
            if device_id:
                return JSONResponse(content={"Error": None, "device_id": device_id})
            else:
                logger.warning(f"User {request.username}: Location check passed but user not in deviceid.json")
                return JSONResponse(content={"Error": "User not found in the logged in users list,try logging in again", "device_id": None})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"User {request.username}: Error reading deviceid.json after location check - {str(e)}")
            return JSONResponse(content={"Error": "Server error", "device_id": None})
    else:
        logger.warning(f"User {request.username}: Malpractice - Location check failed")
        # Remove the pair if it exists (by username only)
        try:
            async with aiofiles.open("deviceid.json", "r") as f:
                content = await f.read()
                device_data = json.loads(content)
            if request.username in device_data:
                del device_data[request.username]
                async with aiofiles.open("deviceid.json", "w") as f:
                    await f.write(json.dumps(device_data))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"User {request.username}: Error removing device pair after location fail - {str(e)}")
        return JSONResponse(content={"Error": "Location Check Failed", "device_id": None})

@app.post("/shacheck")
async def check_sha(request: ShaRequest):
    logger.info(f"User {request.username}: SHA check input - sha256: {request.sha256}")
    # For now, always true
    if sha_check(request.sha256):
        logger.info(f"User {request.username}: SHA check passed")
        return JSONResponse(content={"error": None})
    else:
        logger.warning(f"User {request.username}: Malpractice - SHA check failed")
        # Remove the pair if it exists (by username only)
        try:
            async with aiofiles.open("deviceid.json", "r") as f:
                content = await f.read()
                device_data = json.loads(content)
            if request.username in device_data:
                del device_data[request.username]
                async with aiofiles.open("deviceid.json", "w") as f:
                    await f.write(json.dumps(device_data))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"User {request.username}: Error removing device pair after SHA fail - {str(e)}")
        return JSONResponse(content={"error": "Integrity Check Failed"})

@app.post("/checkfailed")
async def check_sha(request: CheckFailed):
    logger.warning(f"User {request.username}: Malpractice - Check failed message: {request.message}")
    # For now, always true
    print(request.username,request.message)
    return JSONResponse(content={"error": None})
    

@app.get("/listfiles")
async def list_files(username: str, device_id: str):
    logger.info(f"User {username}: List files request with device_id: {device_id}")
    # Check if username and device_id are authorized
    if not await is_device_authorized(username, device_id):
        logger.warning(f"User {username}: Malpractice - Unauthorized list files attempt with device_id: {device_id}")
        return JSONResponse(status_code=403, content={"error": "Not Permitted"})

    try:
        async with aiofiles.open("files.json", "r") as f:
            content = await f.read()
            files = json.loads(content)
        user_files = files.get(username, [])
        logger.info(f"User {username}: Listed files successfully")
        return JSONResponse(content=user_files)
    except FileNotFoundError as e:
        logger.error(f"User {username}: Error - files.json not found - {str(e)}")
        raise HTTPException(status_code=404, detail="files.json not found")
    except json.JSONDecodeError as e:
        logger.error(f"User {username}: Error parsing files.json - {str(e)}")
        raise HTTPException(status_code=500, detail="Error parsing files.json")

@app.post("/getfile")
async def get_file(request: GetFileRequest):
    logger.info(f"User {request.username}: Get file request - device_id: {request.device_id}, filename: {request.filename}")
    # Check if username and device_id are authorized
    if not await is_device_authorized(request.username, request.device_id):
        logger.warning(f"User {request.username}: Malpractice - Unauthorized get file attempt with device_id: {request.device_id}")
        return JSONResponse(status_code=403, content={"error": "Not Permitted"})

    try:
        async with aiofiles.open("files.json", "r") as f:
            content = await f.read()
            files = json.loads(content)
        user_files = files.get(request.username, [])
        file_entry = next((f for f in user_files if f["filename"] == request.filename), None)
        if not file_entry:
            logger.warning(f"User {request.username}: File not accessible: {request.filename}")
            raise HTTPException(status_code=403, detail="File not accessible to user")
    except FileNotFoundError as e:
        logger.error(f"User {request.username}: Error - files.json not found - {str(e)}")
        raise HTTPException(status_code=404, detail="files.json not found")
    except json.JSONDecodeError as e:
        logger.error(f"User {request.username}: Error parsing files.json - {str(e)}")
        raise HTTPException(status_code=500, detail="Error parsing files.json")

    file_path = f"static/{request.filename}"
    if not os.path.exists(file_path):
        logger.error(f"User {request.username}: File not found on server: {request.filename}")
        raise HTTPException(status_code=404, detail="File not found on server")

    logger.info(f"User {request.username}: File requested successfully: {request.filename}")

    # If viewtype is onetime, remove from user's list before sending
    if file_entry["viewtype"] == "onetime":
        user_files.remove(file_entry)
        files[request.username] = user_files
        async with aiofiles.open("files.json", "w") as f:
            await f.write(json.dumps(files))

    return FileResponse(path=file_path, filename=request.filename, media_type='application/octet-stream')
