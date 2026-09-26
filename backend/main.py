from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.websocket import websocket_endpoint
from ai.assistant import generate_meeting_summary
from backend.websocket import (
    websocket_endpoint,
    meeting_messages
)
app = FastAPI(
    title="AI Meeting Assistant",
    description="Real-time AI powered meeting assistant",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():

    return {
        "message": "AI Meeting Assistant Backend is Running"
    }


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):

    await websocket_endpoint(websocket)

@app.post("/meeting/summary")
async def meeting_summary():

    transcript = "\n".join(
        [
            f"{item['username']}: {item['message']}"
            for item in meeting_messages
        ]
    )

    summary = generate_meeting_summary(
        transcript
    )

    return {
        "summary": summary
    }


@app.post("/meeting/summary")
async def meeting_summary():

    transcript = "\n".join(
        [
            f"{item['username']}: {item['message']}"
            for item in meeting_messages
        ]
    )

    print("TRANSCRIPT:")
    print(transcript)

    summary = generate_meeting_summary(transcript)

    return {
        "summary": summary
    }