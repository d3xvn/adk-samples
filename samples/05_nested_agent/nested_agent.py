"""
Example of Nested Agents (Agent-as-a-Tool) using Google's ADK.

This example demonstrates how to use an entire agent as a tool, allowing one agent
to call another agent as part of its workflow.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# Create a specialized sub-agent
sub_agent = LlmAgent(
    name="specialized_agent",
    model=DEFAULT_MODEL,
    description="A specialized agent with specific capabilities",
    instruction=(
        "You are the specialized agent. Take the user's request string "
        "and return exactly: "Specialized result: <their request>"."
    )
)

# Create an agent tool from the sub-agent
nested_tool = AgentTool(agent=sub_agent)

# Use this tool in another agent
super_agent = LlmAgent(
    name="supervisor",
    model=DEFAULT_MODEL,
    tools=[nested_tool],
    output_key="delegated_response",
    description="Delegates the user's request to a specialist and returns the result.",
    instruction=(
        "You are the supervisor. When the user gives you a request, "
        "call `specialized_tool(request)` and return *only* what that tool returns."
    ))

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
    agent=super_agent,
    app_name=APP_NAME,
    session_service=session_service
)

def run_supervisor(query: str) -> str:
    msg = types.Content(role="user", parts=[types.Part(text=query)])
    for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=msg):
        if event.is_final_response():
            return event.content.parts[0].text
    return "No response received."


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    response = run_supervisor("Please transform this text")
    print(f"Result: {response}") 