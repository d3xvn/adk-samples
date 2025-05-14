"""
API Server for Docker deployment example.

This is a simple FastAPI server for the Docker container example.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from fastapi import FastAPI
from pydantic import BaseModel

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client with API key from environment or config
API_KEY = os.environ.get("GOOGLE_API_KEY", GOOGLE_API_KEY)
genai.configure(api_key=API_KEY)

# Get environment variables with fallbacks to config
APP_NAME = os.environ.get("APP_NAME", DEFAULT_APP_NAME)
MODEL_NAME = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

# --- Agent setup ----------------------------------------------------------

def get_answer(question: str) -> str:
    """Provides an answer to a question.
    
    Args:
        question: The question to answer.
        
    Returns:
        An answer to the question.
    """
    return f"The answer to '{question}' is 42."

# Create the agent
agent = LlmAgent(
    name="docker_agent",
    model=MODEL_NAME,
    tools=[get_answer],
    description="A simple question-answering agent for Docker deployment."
)

# Set up session service and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service
)

# --- API Models ----------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"
    user_id: str = "default"

class QueryResponse(BaseModel):
    answer: str

# --- FastAPI App ---------------------------------------------------------

app = FastAPI(title="ADK Agent API", description="Example API for ADK Agent in Docker")

@app.get("/")
def read_root():
    return {"status": "ok", "app": APP_NAME, "model": MODEL_NAME}

@app.post("/ask", response_model=QueryResponse)
async def ask_question(req: QueryRequest):
    # Ensure session exists
    if session_service.get_session(app_name=APP_NAME, user_id=req.user_id, session_id=req.session_id) is None:
        session_service.create_session(app_name=APP_NAME, user_id=req.user_id, session_id=req.session_id)
    
    # Create message content
    content = types.Content(
        role="user",
        parts=[types.Part(text=req.question)]
    )
    
    # Run the agent
    response_text = None
    async for event in runner.run_async(
        user_id=req.user_id,
        session_id=req.session_id,
        new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    
    return QueryResponse(answer=response_text or "No answer available.") 