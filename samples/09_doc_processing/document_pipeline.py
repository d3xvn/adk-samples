"""
Example of Document Processing Pipeline using Google's ADK.

This example demonstrates sequential composition with a document processing
pipeline that extracts text, analyzes sentiment, and generates a summary.
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


# Define tool functions for different stages
def extract_text(document_path: str) -> str:
    """Extracts text from a document file.
    
    Args:
        document_path: Path to the document file.
        
    Returns:
        Extracted text content.
    """
    return f"This is sample content for processing from {document_path}."


def analyze_sentiment(text: str) -> dict:
    """Analyzes sentiment of the provided text.
    
    Args:
        text: The text to analyze.
        
    Returns:
        Dictionary with sentiment analysis results.
    """
    positive = ["good", "great", "excellent"]
    negative = ["bad", "poor", "terrible"]
    lc = text.lower()
    pos = sum(w in lc for w in positive)
    neg = sum(w in lc for w in negative)
    tone = "positive" if pos > neg else "negative" if neg > pos else "neutral"
    return {"sentiment": tone, "positive_score": pos, "negative_score": neg}


def generate_summary(text: str, sentiment_data: dict) -> str:
    """Generates a summary based on text and sentiment data.
    
    Args:
        text: The original text.
        sentiment_data: Dictionary with sentiment analysis results.
        
    Returns:
        Generated summary string.
    """
    word_count = len(text.split())
    tone = sentiment_data["sentiment"]
    return f"Summary: {word_count} words, overall tone is {tone}."


# Create agents for each step
extract_agent = LlmAgent(
    name="extractor",
    model=DEFAULT_MODEL,
    tools=[extract_text],
    output_key="extracted_text",
    description="Extracts text from the given document path.",
    instruction=(
        "You are the extractor. The user says 'Process this document: <path>'. "
        "Extract the <path> part, call `extract_text(path)`, and return only the extracted text."
    )
)

analyze_agent = LlmAgent(
    name="analyzer",
    model=DEFAULT_MODEL,
    tools=[analyze_sentiment],
    description="Analyzes sentiment in text",
    output_key="sentiment_data",
    instruction=(
        "You are the analyzer. Take the text in `extracted_text`, "
        "call `analyze_sentiment(extracted_text)`, and return only the resulting JSON."
    )
)

summary_agent = LlmAgent(
    name="summarizer",
    model=DEFAULT_MODEL,
    tools=[generate_summary],
    output_key="final_summary",
    description="Summarizes text with sentiment data.",
    instruction=(
        "You are the summarizer. Given `extracted_text` and `sentiment_data`, "
        "call `generate_summary(extracted_text, sentiment_data)` and return only the summary string."
    )
)

# Create the sequential pipeline
document_pipeline = SequentialAgent(
    name="document_processor",
    sub_agents=[extract_agent, analyze_agent, summary_agent],
    description="Extracts text, runs sentiment analysis, then summarizes."
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
    agent=document_pipeline,
    app_name=APP_NAME,
    session_service=session_service
)


def run_document_pipeline(document_path: str) -> str:
    prompt = types.Content(
        role="user",
        parts=[types.Part(text=f"Process this document: {document_path}")]
    )
    final_summary = None

    for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=prompt):
        # capture the summarizer's final output
        if event.is_final_response() and event.content and event.content.parts:
            final_summary = event.content.parts[0].text
        # keep looping until the generator naturally ends

    return (final_summary or "No response received.").strip()


# Example usage
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
        sys.exit(1)
        
    result = run_document_pipeline("quarterly_report.pdf")
    print(result) 