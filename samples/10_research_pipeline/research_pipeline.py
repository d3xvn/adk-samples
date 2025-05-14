"""
Example of Multi-Source Research Pipeline using Google's ADK.

This example demonstrates parallel composition with a research pipeline that searches
multiple sources in parallel and then merges the results.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the root config
from config import GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_APP_NAME, DEFAULT_USER_ID, DEFAULT_SESSION_ID

from google.adk.agents import ParallelAgent, LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)


# Define research tools for different sources
def search_news(topic: str) -> str:
    """Searches news sources for information on a topic.
    
    Args:
        topic: The topic to search for.
        
    Returns:
        News search results as a string.
    """
    return f"News results for {topic}: Latest developments include XYZ..."


def search_academic(topic: str) -> str:
    """Searches academic databases for information on a topic.
    
    Args:
        topic: The topic to search for.
        
    Returns:
        Academic search results as a string.
    """
    return f"Academic results for {topic}: Recent papers discuss ABC..."


def search_social(topic: str) -> str:
    """Searches social media for information on a topic.
    
    Args:
        topic: The topic to search for.
        
    Returns:
        Social media trends as a string.
    """
    return f"Social media trends for {topic}: People are discussing DEF..."


# Create agents for each research source
news_agent = LlmAgent(
    name="news_researcher",
    model=DEFAULT_MODEL,
    tools=[search_news],
    output_key="news_results",
    description="Researches news sources",
    instruction=(
        "You are the news researcher. Extract the topic from the user query, "
        "call `search_news(topic)`, and return only the raw string."
    )
)

academic_agent = LlmAgent(
    name="academic_researcher",
    model=DEFAULT_MODEL,
    tools=[search_academic],
    output_key="academic_results",
    description="Researches academic sources",
    instruction=(
        "You are the academic researcher. Extract the topic, "
        "call `search_academic(topic)`, and return only the raw string."
    )
)

social_agent = LlmAgent(
    name="social_researcher",
    model=DEFAULT_MODEL,
    tools=[search_social],
    output_key="social_results",
    description="Researches social media trends",
    instruction=(
        "You are the social media researcher. Extract the topic, "
        "call `search_social(topic)`, and return only the raw string."
    )
)

# Create parallel research agent
parallel_research = ParallelAgent(
    name="parallel_researcher",
    sub_agents=[news_agent, academic_agent, social_agent],
    description="Fetches news, academic, and social results in parallel"
)

# Create a merger agent to combine results
def merge_research(news: str, academic: str, social: str) -> str:
    """Merges research results from multiple sources.
    
    Args:
        news: News research results.
        academic: Academic research results.
        social: Social media research results.
        
    Returns:
        Combined research report.
    """
    return f"""Combined Research Report:

News Insights: {news}

Academic Findings: {academic}

Social Trends: {social}

This comprehensive view provides a well-rounded perspective on the topic.
"""

merger_agent = LlmAgent(
    name="research_merger",
    model=DEFAULT_MODEL,
    tools=[merge_research],
    output_key="merged_report",
    description="Merges research from multiple sources",
    instruction=(
        "You have three pieces of state: `news_results`, `academic_results`, "
        "and `social_results`. Call `merge_research(news_results, academic_results, social_results)` "
        "and return *only* the resulting combined report string."
    )
)

# Create a sequential pipeline that does parallel research then merges
research_pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[parallel_research, merger_agent],
    description="Runs parallel research and then merges the outputs"
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
    agent=research_pipeline,
    app_name=APP_NAME,
    session_service=session_service
)


# Run the research pipeline
def run_research(topic: str) -> str:
    prompt = types.Content(
        role="user",
        parts=[types.Part(text=f"Research this topic: {topic}")]
    )

    merged_report = None

    # Fully consume the event stream
    for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=prompt):
        # Only capture the merger agent's final response
        if (
            event.is_final_response()
            and event.author == "research_merger"
            and event.content and event.content.parts
        ):
            merged_report = event.content.parts[0].text

    return (merged_report or "No response received.").strip()


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    result = run_research("quantum computing")
    print(result) 