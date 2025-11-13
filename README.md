# FastAPI File Server and Message Receiver

A simple FastAPI server that serves static files and receives messages from client devices.

## Features

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
- `POST /messages`: Receive messages from devices
  - Body: `{"device_id": "string", "message": "string"}`
- `GET /listfiles?device_id={device_id}`: Get list of available files from files.json (requires authorization)
- `POST /getfile`: Download a specific file
  - Body: `{"device_id": "string", "filename": "string"}`
  - Both endpoints require the device_id to be authorized via users.txt

## Testing

You can test the endpoints with curl:

### Test message endpoint:
```bash
curl -X POST "http://127.0.0.1:8001/messages" \
     -H "Content-Type: application/json" \
     -d '{"device_id": "device123", "message": "Hello from device"}'
```

### Test file download:
```bash
curl -X POST "http://127.0.0.1:8001/getfile" \
     -H "Content-Type: application/json" \
     -d '{"device_id": "device123", "filename": "a.py"}' \
     --output downloaded_file.py
```

### Test list files (authorized):
```bash
curl -X GET "http://127.0.0.1:8001/listfiles?device_id=device123"
```

### Test list files (unauthorized):
```bash
curl -X GET "http://127.0.0.1:8001/listfiles?device_id=unauthorized"
```
