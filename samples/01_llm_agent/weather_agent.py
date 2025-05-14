"""
Example of a basic LLM Agent using Google's ADK.

This agent uses the Gemini model to decide which tool to call and how to call it
based on natural language instructions.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

import google.generativeai as genai
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# Define a simple tool
def get_weather(city: str) -> str:
    """Gets the current weather for a city.
    
    Args:
        city: The name of the city to get weather for.
        
    Returns:
        A string with the weather description.
    """
    return f"The weather in {city} is sunny."

# Create the agent
agent = LlmAgent(
    name="weather_agent",
    model=DEFAULT_MODEL,
    tools=[get_weather],
    description="A helpful assistant that can check weather."
)

# Set up runner and session for execution
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
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Run the agent using the runner
def run_query(query):
    # Create content from user query
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    
    # Run the agent with the runner
    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )
    
    # Process events to get the final response
    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    
    return "No response received."

# Example of usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    response = run_query("What's the weather like in Berlin?")
    print(response) 