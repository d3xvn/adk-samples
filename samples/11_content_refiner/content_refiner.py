"""
Example of Iterative Content Refinement using Google's ADK.

This example demonstrates how to use a LoopAgent for iterative content refinement,
repeatedly improving content until a quality threshold is met.
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

# Define tools for content creation and critique
def generate_draft(topic: str) -> str:
    """Creates an initial draft on a topic.
    
    Args:
        topic: The topic to write about.
        
    Returns:
        Initial draft content.
    """
    return f"Initial draft about {topic}: This is a basic overview of the subject matter..."


def improve_draft(draft: str, feedback: str) -> str:
    """Improves a draft based on feedback.
    
    Args:
        draft: The current draft content.
        feedback: Feedback for improvement.
        
    Returns:
        Improved draft content.
    """
    # In a real implementation, this would make specific improvements
    return f"Improved draft based on feedback: {draft}\n\nAddressed issues: {feedback}"

# Create agents
writer_agent = LlmAgent(
    name="writer",
    model=DEFAULT_MODEL,
    tools=[generate_draft, improve_draft],
    output_key="current_draft",
    description="Writes and refines content drafts",
    instruction=(
        "You are the writer. On the first iteration, extract the topic from the user message "
        "and call `generate_draft(topic)`. On subsequent iterations, take `current_draft` from state "
        "and `feedback` from state, call `improve_draft(current_draft, feedback)`. "
        "Return *only* the new draft string."
    )
)

class CriticAgent(BaseAgent):
    """Agent that evaluates content quality and provides feedback."""
    
    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(self, context):
        state = context.session.state
        draft = state.get("current_draft", "")
        iteration = state.get("iteration", 0)

        # simple "quality" model: +25 points per revision
        quality = min(iteration * 25, 100)

        if quality >= 90:
            feedback = "Draft is excellent—no further changes needed."
            yield Event(
                author=self.name,
                content=types.Content(
                    role="assistant",
                    parts=[types.Part(text=feedback)]
                ),
                actions=EventActions(escalate=True)  # break the loop
            )
        else:
            feedback = f"Quality {quality}/100. Needs more clarity and detail."
            # bump iteration and store feedback
            yield Event(
                author=self.name,
                content=types.Content(
                    role="assistant",
                    parts=[types.Part(text=feedback)]
                ),
                actions=EventActions(state_delta={
                    "feedback": feedback,
                    "iteration": iteration + 1
                })
            )

critic_agent = CriticAgent(name="critic")

# Create loop agent for iterative refinement
content_refiner = LoopAgent(
    name="content_refiner",
    sub_agents=[writer_agent, critic_agent],
    max_iterations=5,
    description="Iteratively refines content until quality threshold is met"
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
    agent=content_refiner,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the content refiner
def run_content_refiner(topic: str) -> str:
    # seed the loop
    svc_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    svc_session.state["iteration"] = 0

    prompt = types.Content(
        role="user",
        parts=[types.Part(text=f"Create high-quality content about: {topic}")]
    )
    final = None

    for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=prompt):
        # capture only when the writer_agent emits a draft _and_ loop is about to end
        if event.is_final_response() and event.author == "writer":
            final = event.content.parts[0].text

    return (final or "No response received.").strip()


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    result = run_content_refiner("artificial intelligence ethics")
    print(result) 