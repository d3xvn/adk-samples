"""
Example of Human-in-the-Loop Approval in Google's ADK.

This example demonstrates how to implement human approval steps for 
significant actions.
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

# Tool that requires human approval
def propose_action(action_type: str, details: str) -> dict:
    """Proposes an action that requires human approval.
    
    Args:
        action_type: The type of action being proposed.
        details: Specific details about the action.
        
    Returns:
        A dictionary with the proposal status.
    """
    # In a real implementation, this might:
    # - Send the proposal to a queue for human review
    # - Send an email notification
    # - Update a dashboard
    
    print(f"\n=== ACTION REQUIRING APPROVAL ===")
    print(f"Type: {action_type}")
    print(f"Details: {details}")
    
    # Simple console-based approval for demo purposes
    approval = input("Approve? (y/n): ")
    
    if approval.lower() == 'y':
        return {
            "status": "approved",
            "message": "Action approved by human reviewer",
            "action_type": action_type,
            "details": details
        }
    else:
        return {
            "status": "rejected",
            "message": "Action rejected by human reviewer",
            "action_type": action_type,
            "details": details
        }

# Create agent with human-in-the-loop design
human_oversight_agent = LlmAgent(
    name="overseen_agent",
    model=DEFAULT_MODEL,
    tools=[propose_action],
    instruction="""You are an agent with human oversight.
    For any significant action, use the propose_action tool to get approval before proceeding.
    Significant actions include:
    - Sending communications to customers
    - Making financial decisions above $100
    - Changing system settings
    - Creating or deleting accounts
    """,
    description="Agent that requires human approval for significant actions"
)

# Set up runner
session_service = InMemorySessionService()
runner = Runner(
    agent=human_oversight_agent,
    app_name=DEFAULT_APP_NAME,
    session_service=session_service
)

# Function to run the agent
def run_overseen_agent(query):
    # Create a session
    session = session_service.create_session(
        app_name=DEFAULT_APP_NAME,
        user_id=DEFAULT_USER_ID,
        session_id=DEFAULT_SESSION_ID
    )
    
    # Create content
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    
    # Run the agent
    for event in runner.run(
        user_id=DEFAULT_USER_ID,
        session_id=DEFAULT_SESSION_ID,
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
        
    print("\n=== HUMAN-IN-THE-LOOP AGENT DEMONSTRATION ===\n")
    
    # Example 1: Action requiring approval
    print("Example 1: Action requiring approval")
    result = run_overseen_agent("Please send a promotional email to all customers about our new product.")
    print(f"\nFinal result: {result}\n")
    
    # Example 2: Action requiring approval
    print("Example 2: Another action requiring approval")
    result = run_overseen_agent("Update our system settings to increase the maximum file upload size to 100MB.")
    print(f"\nFinal result: {result}\n")
    
    # Example 3: Non-significant action
    print("Example 3: Non-significant action (might not require approval)")
    result = run_overseen_agent("Tell me the current time.")
    print(f"\nFinal result: {result}\n") 