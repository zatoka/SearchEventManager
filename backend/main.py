"""
SearchEventsManager API - Main FastAPI application.
"""
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_db
from routes.venues import router as venues_router
from routes.events import router as events_router
from routes.regions import router as regions_router

print("=" * 50)
print("SearchEventsManager Backend Starting...")
print(f"Python version: {sys.version}")
print(f"Frozen: {getattr(sys, 'frozen', False)}")
if getattr(sys, "frozen", False):
    print(f"MEIPASS: {sys._MEIPASS}")
print(f"Current file: {__file__}")
print(f"Current dir: {Path(__file__).parent}")
print("=" * 50)

app = FastAPI(
    title="SearchEventsManager API",
    description="API for managing venues and scraping events",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database and create tables if necessary.
@app.on_event("startup")
async def initialize_database():
    db = await get_db()
    await db.close()
    print("Database initialized successfully.")

# Register the complete application routes.
app.include_router(venues_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(regions_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "SearchEventsManager API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8002

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1

    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

