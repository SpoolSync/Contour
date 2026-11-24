# Contour end-to-end test

Runs the real app against local Firebase emulators (Auth + Firestore with the live Pixora rules), in headless Chrome with a fake camera that shows a barcode. Two test accounts are created each run with random emails and passwords; nothing touches the real Pixora project.

1. `firebase emulators:start --project pixora-bca1f` in this folder (put the current `firestore.rules` next to `firebase.json`).
2. Serve the app: `python3 -m http.server 8765` from the repo root.
3. `python3 tests/e2e.py` — needs Python Playwright, Google Chrome and ffmpeg. Screenshots land in `tests/shots/`.
