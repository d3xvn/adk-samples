"""
Example of creating a Basic Tool in Google's ADK.

This example shows how to define a Python function to use as a tool and
how an LLM agent can use it to respond to requests.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

def greet_user(name: str) -> str:
    """Greets the user by name.
    
    Args:
        name: The name of the user to greet.
        
    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"

# Create the agent with the function as a tool
greeting_agent = LlmAgent(
    name="greeter",
    model=DEFAULT_MODEL,
    tools=[greet_user],
    description="Agent that can greet users"
)

# Set up runner and session
APP_NAME = DEFAULT_APP_NAME
USER_ID = DEFAULT_USER_ID
SESSION_ID = DEFAULT_SESSION_ID

# Create session service and session
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)

# Create runner
runner = Runner(
    agent=greeting_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Run the agent
def run_greeting_agent(query):
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    
    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            return event.content.parts[0].text
    
    return "No response received."

# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    response = run_greeting_agent("Say hello to Alice")
    print(response) 