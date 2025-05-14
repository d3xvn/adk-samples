"""
Example of REST API Deployment for ADK Agents.

This example demonstrates how to wrap an ADK agent in a web server using FastAPI
and expose it as an HTTP endpoint.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import uvicorn

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# --- Agent setup ----------------------------------------------------------

def answer_question(question: str) -> str:
    """Provides an answer to a question.
    
    Args:
        question: The question to answer.
        
    Returns:
        Answer to the question.
    """
    return f"The answer to '{question}' is: 42"

agent = LlmAgent(
    name="api_agent",
    model=DEFAULT_MODEL,
    tools=[answer_question],
    description="A question-answering agent exposed as an API"
)

session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name=DEFAULT_APP_NAME,
    session_service=session_service
)

# --- Request/Response models ----------------------------------------------

class QueryRequest(BaseModel):
    query: str
    session_id: str = None
    user_id: str = None

class QueryResponse(BaseModel):
    user_id: str
    session_id: str
    response: str

# --- FastAPI app ----------------------------------------------------------

app = FastAPI(title="ADK Agent API")

@app.post("/query", response_model=QueryResponse)
async def query_agent(req: QueryRequest):
    # generate IDs if missing
    user_id = req.user_id or f"user_{uuid.uuid4().hex[:8]}"
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"

    # ensure session exists
    if session_service.get_session(app_name="api_app", user_id=user_id, session_id=session_id) is None:
        session_service.create_session(app_name="api_app", user_id=user_id, session_id=session_id)

    # build message
    content = types.Content(
        role="user",
        parts=[types.Part(text=req.query)]
    )

    # stream until final and grab the text
    response_text = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text

    return QueryResponse(
        user_id=user_id,
        session_id=session_id,
        response=response_text or ""
    )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    # each WS connection gets its own user_id
    user_id = f"ws_user_{uuid.uuid4().hex[:8]}"

    # ensure session exists
    if session_service.get_session(app_name="api_app", user_id=user_id, session_id=session_id) is None:
        session_service.create_session(app_name="api_app", user_id=user_id, session_id=session_id)

    # let client know its user_id
    await ws.send_json({"type": "session_init", "user_id": user_id, "session_id": session_id})

    try:
        while True:
            query = await ws.receive_text()
            content = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )

            # stream all events, pushing each as JSON
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                payload = {
                    "type": "event",
                    "id": event.id,
                    "author": event.author,
                }
                if event.content and event.content.parts:
                    payload["text"] = event.content.parts[0].text
                if event.is_final_response():
                    payload["is_final"] = True

                await ws.send_json(payload)

    except WebSocketDisconnect:
        # client closed connection
        pass
    except Exception as e:
        # on error, close cleanly
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()

if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    uvicorn.run(app, host="0.0.0.0", port=8000)