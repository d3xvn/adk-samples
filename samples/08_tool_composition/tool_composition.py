"""
Example of Tool Composition in Google's ADK.

This example demonstrates how to create tools that call other tools,
enabling more complex behaviors.
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


# Basic tool
def get_data(source: str) -> str:
    """Gets raw data from a specified source.

    Args:
        source: The name or URL of the data source.

    Returns:
        The raw data as a string.
    """
    return f"Raw data from {source}: 42, 17, 23, 8, 15"


# Tool that uses the first tool
def analyze_data(source: str) -> str:
    """Analyzes data from a specified source.

    Args:
        source: The name or URL of the data source.

    Returns:
        Analysis of the data.
    """
    # Get the data first
    raw_data = get_data(source)

    # Parse and analyze it
    numbers = [int(n.strip()) for n in raw_data.split(":", 1)[1].split(",")]
    total = sum(numbers)
    average = total / len(numbers)

    return f"Analysis of {source}:\n- Total: {total}\n- Average: {average:.2f}"


# Create the agent with both tools
data_agent = LlmAgent(
    name="data_analyzer",
    model=DEFAULT_MODEL,
    tools=[analyze_data],
    output_key="analysis_summary",
    description="Fetches raw data and returns its analysis.",
    instruction=(
        "You are the data analyzer. When the user says "
        "'Analyze data from <source>', extract the <source> string, "
        "call `analyze_data(source)`, and return *only* its output."
    )
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
    agent=data_agent,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the agent
def run_data_agent(query):
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
        
    response = run_data_agent("Analyze data from database_alpha")
    print(response) 