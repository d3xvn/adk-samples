"""
Example of Tool Context Access in Google's ADK.

This example demonstrates how tools can access contextual information using the
special tool_context parameter.
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
from google.adk.tools import ToolContext
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)


# Tool with context access
def process_document(document_name: str, analysis_query: str, tool_context: ToolContext) -> dict:
    """Analyzes a document using context from memory.

    Args:
        document_name: Name of the document to analyze.
        analysis_query: The specific analysis to perform.
        tool_context: Access to state and other context variables.

    Returns:
        A dictionary with analysis results or error information.
    """
    # Access session state
    previous_queries = tool_context.state.get("previous_queries", [])

    # Update state with the new query
    tool_context.actions.state_delta = {
        "previous_queries": previous_queries + [analysis_query]
    }

    # Actual document processing would go here
    return {
        "status": "success",
        "analysis": f"Analysis of '{document_name}' regarding '{analysis_query}'",
        "query_history": previous_queries + [analysis_query]
    }


# Create the agent with the tool
document_agent = LlmAgent(
    name="document_analyzer",
    model=DEFAULT_MODEL,
    output_key="analysis_result",
    tools=[process_document],
    description="Analyzes a document and records each query in history.",
    instruction=(
        "You are a document analysis agent. When the user asks "
        "'Analyze <document_name> for <analysis_query>', extract both parts, "
        "call `process_document(document_name, analysis_query, tool_context)`, "
        "and return *only* the resulting JSON dictionary."
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
    agent=document_agent,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the agent
def run_document_agent(query):
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
        
    # Run multiple queries to show state persistence
    print("First query:")
    response1 = run_document_agent("Analyze report.pdf for sales trends")
    print(response1)
    
    print("\nSecond query:")
    response2 = run_document_agent("Analyze report.pdf for market share")
    print(response2) 