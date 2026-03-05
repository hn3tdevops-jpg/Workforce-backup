Frontend (Vite + React)

Quickstart:

1. cd frontend
2. npm install
3. npm run dev

The dev server proxies / and /api to the backend at http://localhost:8000 so start the FastAPI server (e.g. `uvicorn app.main:app --reload`) and then run the frontend.

Serving built UI from FastAPI:

- Build the frontend: `npm run build` which outputs `dist/`.
- Start the FastAPI server; if the `frontend/dist` directory exists the app will mount it at `/ui` (open http://localhost:8000/ui).
