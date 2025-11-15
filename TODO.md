# TODO List for Project Update

- [x] Restructure files.json to per-user format (object with user keys, arrays of {filename, viewtype})
- [x] Update /listfiles endpoint in main.py to return only files for the authenticated user
- [x] Update /getfile endpoint in main.py to check file in user's list and remove onetime files after sending
- [ ] Test the updated endpoints for correct functionality
