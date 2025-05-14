"""
Example of a Parallel Agent using Google's ADK.

This agent runs multiple tools concurrently through async I/O and returns
their results as a batch.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import ParallelAgent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)


# Define some example tools
def get_weather(city: str) -> str:
    """Gets the current weather for a city."""
    return f"The weather in {city} is sunny."


def get_news(topic: str) -> str:
    """Gets the latest news on a topic."""
    return f"Latest news about {topic}: Everything is great!"


# Create individual agents for different tasks
weather_agent = LlmAgent(
    name="weather_agent",
    model=DEFAULT_MODEL,
    tools=[get_weather],
    instruction=(
        "Extract the city name from the user query, call get_weather(city), "
        "and return only that result."
    ),
    description="Provides weather information",
    output_key = "weather_info"
)

news_agent = LlmAgent(
    name="news_agent",
    model=DEFAULT_MODEL,
    tools=[get_news],
    instruction=(
        "Extract the topic from the user query, call get_news(topic), "
        "and return only that result."
    ),
    description="Provides news updates",
    output_key="news_info"
)

# Create a parallel agent with proper agents as sub-agents
parallel_agent = ParallelAgent(
    name="parallel_fetcher",
    sub_agents=[weather_agent, news_agent],
    description="Fetch weather & news at the same time"
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
    agent=parallel_agent,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the parallel agent using the runner
def run_parallel_agent(query):
    # Create content from user query
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    replies = []

    # Run the agent with the runner
    for event in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
    ):
        if event.content:
            replies.append(event.content.parts[0].text)
    return replies


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    result = run_parallel_agent("Berlin")
    print("Parallel agent results:")
    for i, reply in enumerate(result):
        print(f"{i+1}. {reply}") 