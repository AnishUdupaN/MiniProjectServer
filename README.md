# FastAPI File Server and Message Receiver

A simple FastAPI server that serves static files, receives messages from client devices, and handles user authentication with device management.

## Features

- User login with username/password verification
- Device ID generation and management (one active device per user)
- Receive JSON messages via POST to `/messages`
- List available files from files.json via GET to `/listfiles`
- Download files via POST to `/getfile` with validation
- Basic logging for received messages and file requests

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

```bash
uvicorn main:app --reload
```

The server will start at http://127.0.0.1:8001

## API Endpoints

- `GET /`: Root endpoint
- `POST /login`: Authenticate user and generate device ID
  - Body: `{"username": "string", "password": "string"}`
  - Response: `{"login": "pass", "error": "None"}` or `{"login": "fail", "error": "Wrong username or password"}`
- `POST /check`: Check location and return device ID
  - Body: `{"username": "string", "location": "coordinates"}`
  - Response: `{"Error": "None", "device_id": "current_device_id"}` or `{"Error": "Location Check Failed", "device_id": None}`
 - `POST /messages`: Receive messages from devices
   - Body: `{"username": "string", "device_id": "string", "Error": "string", "message": "string"}`
  - Response: `{"username": "string", "device_id": "string", "Error": "client_Error_value", "Message": "string"}` or with "Error": "Not Authorized" and removes pair from deviceid.json
- `GET /listfiles?username={username}&device_id={device_id}`: Get list of available files from files.json (requires authorization)
- `POST /getfile`: Download a specific file
  - Body: `{"username": "string", "device_id": "string", "filename": "string"}`
  - Both /listfiles and /getfile require valid username and device_id pair from deviceid.json

## File Structure

- `users.json`: Contains username:password pairs for authentication
- `deviceid.json`: Contains username:device_id mappings (one per user, updated on login)
- `files.json`: List of available files with metadata
- `static/`: Directory containing the actual files to be served

## Client Usage Examples

### 1. Login to get device ID
```bash
curl -X POST "http://127.0.0.1:8001/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "password": "pass1"}'
```
Response (success):
```json
{
  "login": "pass",
  "error": "None"
}
```
Response (failure):
```json
{
  "login": "fail",
  "error": "Wrong username or password"
}
```

### 2. List available files (after login)
```bash
curl -X GET "http://127.0.0.1:8001/listfiles?username=user1&device_id=AbCdEf"
```
Response:
```json
[
  {
    "filename": "a.py",
    "viewtype": "normal",
    "expire": "none"
  },
  {
    "filename": "b.jpeg",
    "viewtype": "onetime",
    "expire": "none"
  }
]
```

### 3. Download a file (after login)
```bash
curl -X POST "http://127.0.0.1:8001/getfile" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "device_id": "AbCdEf", "filename": "a.py"}' \
     --output downloaded_a.py
```

### 4. Check location and get device ID
```bash
curl -X POST "http://127.0.0.1:8001/check" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "location": "37.7749,-122.4194"}'
```
Response (success):
```json
{
  "Error": "None",
  "device_id": "AbCdEf"
}
```

### 5. Send a message (requires valid username and device_id)
```bash
curl -X POST "http://127.0.0.1:8001/messages" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "device_id": "AbCdEf", "message": "Hello from client"}'
```
Response (success):
```json
{
  "username": "user1",
  "device_id": "AbCdEf",
  "Error": "None",
  "Message": "Hello from client"
}
```
Response (unauthorized):
```json
{
  "username": "user1",
  "device_id": "wrongid",
  "Error": "Not Authorized",
  "Message": "Hello from client"
}
```

## Testing

You can test the endpoints with curl:

### Test login (success):
```bash
curl -X POST "http://127.0.0.1:8001/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "password": "pass1"}'
```

### Test login (failure):
```bash
curl -X POST "http://127.0.0.1:8001/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "password": "wrongpass"}'
```

### Test check location:
```bash
curl -X POST "http://127.0.0.1:8001/check" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "location": "37.7749,-122.4194"}'
```

### Test message endpoint (authorized):
```bash
curl -X POST "http://127.0.0.1:8001/messages" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "device_id": "AbCdEf", "Error": "None", "message": "Hello from client"}'
```

### Test message endpoint (unauthorized):
```bash
curl -X POST "http://127.0.0.1:8001/messages" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "device_id": "wrongid", "Error": "None", "message": "Hello from client"}'
```

### Test list files (authorized):
```bash
curl -X GET "http://127.0.0.1:8001/listfiles?username=user1&device_id=AbCdEf"
```

### Test list files (unauthorized):
```bash
curl -X GET "http://127.0.0.1:8001/listfiles?username=user1&device_id=wrongid"
```

### Test file download:
```bash
curl -X POST "http://127.0.0.1:8001/getfile" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "device_id": "AbCdEf", "filename": "a.py"}' \
     --output downloaded_file.py \
     --fail
```

### Test message endpoint:
```bash
curl -X POST "http://127.0.0.1:8001/messages" \
     -H "Content-Type: application/json" \
     -d '{"device_id": "AbCdEf", "message": "Hello from device"}'
```
