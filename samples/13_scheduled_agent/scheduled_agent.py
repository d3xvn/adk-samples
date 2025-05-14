"""
Example of Scheduled Execution for ADK Agents.

This example demonstrates how to run agents on a schedule or trigger them based
on external events.
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
import time
import schedule
import json
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# Create an agent that summarizes data
def summarize_data(source: str) -> str:
    """Summarizes data from a source.
    
    Args:
        source: The name or identifier of the data source.
        
    Returns:
        A summary of the data.
    """
    # In a real implementation, this would fetch and analyze data
    return f"Summary of data from {source}: Key metrics are trending upward."

summary_agent = LlmAgent(
    name="summary_agent",
    model=DEFAULT_MODEL,
    tools=[summarize_data],
    description="An agent that summarizes data on a schedule"
)

# Set up runner
session_service = InMemorySessionService()
runner = Runner(
    agent=summary_agent,
    app_name=DEFAULT_APP_NAME,
    session_service=session_service
)

# Function to run the summary job
def run_summary_job():
    print(f"Running scheduled summary job at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create a unique session for this run
    session_id = f"job_{int(time.time())}"
    session = session_service.create_session(
        app_name=DEFAULT_APP_NAME,
        user_id=DEFAULT_USER_ID,
        session_id=session_id
    )
    
    # Create content with the job request
    content = types.Content(
        role="user",
        parts=[types.Part(text="Summarize today's data from our analytics database")]
    )
    
    # Run the agent
    summary = None
    for event in runner.run(
        user_id=DEFAULT_USER_ID,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            summary = event.content.parts[0].text
    
    if summary:
        # In a real implementation, you might:
        # - Send an email with the summary
        # - Store it in a database
        # - Trigger an alert if certain conditions are met
        print(f"Summary generated: {summary}")
        
        # Example: Write to a log file
        with open("summaries.log", "a") as log_file:
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": session_id,
                "summary": summary
            }
            log_file.write(json.dumps(log_entry) + "\n")
    else:
        print("No summary generated.")

# Schedule the job to run daily at 8:00 AM
schedule.every().day.at("08:00").do(run_summary_job)

# Run the scheduler
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    print("Starting scheduler...")
    # Run once immediately for testing
    run_summary_job()
    
    # Then run on schedule
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute 