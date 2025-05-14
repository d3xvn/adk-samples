"""
Example of a Loop Agent using Google's ADK.

This agent repeats a specific tool or agent until a condition is met,
enabling iterative refinement or repeated querying.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.events import Event, EventActions
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)


# Define tools
def guess_number(input_text: str) -> str:
    """Makes a guess at the target number.

    Args:
        input_text: Context for the guess.

    Returns:
        A string containing the guessed number.
    """
    # This is just a mockup - would have actual logic in a real implementation
    return "Is it 42?"


# Create an agent for guessing
guess_agent = LlmAgent(
    name="guesser",
    model=DEFAULT_MODEL,
    description="Makes a guess at the target number.",
    instruction=(
        "You are a number-guessing agent. On each turn, "
        "call `guess_number(input_text)` and return *only* its output."
    ),
    tools=[guess_number],
    output_key="last_response"
)


# Create a custom checker agent that determines when to stop looping
class CheckerAgent(BaseAgent):
    """Agent that checks if the guessed number is correct."""

    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(self, context):
        # pull the last guess out of state
        last = context.session.state.get("last_response", "")
        # keep looping until we actually saw "42"
        found = "42" in last

        # "continue" vs "stop" is your protocol
        verdict = "stop" if found else "continue"

        # ALWAYS supply an EventActions instance (cannot be None)
        actions = EventActions(escalate=found)

        yield Event(
            author=self.name,
            content=types.Content(
                role="assistant",
                parts=[types.Part(text=verdict)]
            ),
            actions=actions
        )


# Create the checker agent
checker_agent = CheckerAgent(name="checker")

# Create loop agent with proper configuration
loop_agent = LoopAgent(
    name="guessing_loop",
    sub_agents=[guess_agent, checker_agent],
    max_iterations=5,
    description="Repeatedly guesses a number until correct or max iterations reached",
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
    agent=loop_agent,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the loop agent using the runner
def run_loop_agent(query):
    # Create content from user query
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )

    # Run the agent with the runner
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
        
    result = run_loop_agent("Start guessing")
    print(f"Final result: {result}") 