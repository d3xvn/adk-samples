"""
Example of a Sequential Agent using Google's ADK.

This agent executes tools in a specific order, creating a data pipeline that
processes information step by step.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# Define tools as functions
def extract_data(input_text: str) -> str:
    """Extracts raw data from input.

    Args:
        input_text: The text to extract data from.

    Returns:
        The extracted raw data.
    """
    return input_text.upper()


def clean_data(data: str) -> str:
    """Cleans the provided data.

    Args:
        data: The data to clean.

    Returns:
        The cleaned data.
    """
    return data.strip()


# Create individual agents for each step
extract_agent = LlmAgent(
    name="extract_agent",
    model=DEFAULT_MODEL,
    tools=[extract_data],
    instruction=(
        "You are a data extraction agent. "
        "When given the user message as `input_text`, "
        "call the Python function `extract_data(input_text)` and return *only* its output."
    ),
    description="Extracts data from input",
    output_key="raw_data"
)

clean_agent = LlmAgent(
    name="clean_agent",
    model=DEFAULT_MODEL,
    tools=[clean_data],
    instruction=(
        "You are a data cleaning agent. "
        "Take the extracted data in `raw_data`, "
        "call the Python function `clean_data(raw_data)`, and return *only* the cleaned data."
    ),
    description="Cleans extracted data"
)

# Create sequential agent with the proper sub-agents
sequential_agent = SequentialAgent(
    name="sequential_pipeline",
    sub_agents=[extract_agent, clean_agent],
    description="Runs extract_agent then clean_agent, in order."
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
    agent=sequential_agent,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the sequential agent using the runner
def run_sequential_agent(input_text):
    # Create content from user input
    content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)]
    )

    # Run the agent with the runner
    final_response = "No response received."
    for event in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
    ):
        if event.is_final_response():
            final_response = event.content.parts[0].text

    return final_response


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    result = run_sequential_agent("  hello world  ")
    print(f"Result: {result}") 