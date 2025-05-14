"""
Example of Tool Safety Checks in Google's ADK.

This example demonstrates how to implement validation and safety checks for tools.
"""

import sys
import os
import re
import logging

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Example of a tool with built-in safety checks
def send_email(to: str, subject: str, body: str) -> dict:
    """Sends an email to the specified recipient.
    
    Args:
        to: Email address of the recipient.
        subject: Subject line of the email.
        body: Body text of the email.
        
    Returns:
        A dictionary with status information.
    """
    # Safety check: Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", to):
        logging.warning(f"Invalid email format detected: {to}")
        return {"status": "error", "message": "Invalid email format"}
    
    # Safety check: Check allowed domains
    allowed_domains = ["mycompany.com", "partner.org"]
    if not any(to.endswith(f"@{domain}") for domain in allowed_domains):
        logging.warning(f"Attempt to send to non-allowed domain: {to}")
        return {
            "status": "error", 
            "message": f"Can only send to these domains: {', '.join(allowed_domains)}"
        }
    
    # Safety check: Check for sensitive content
    sensitive_terms = ["password", "ssn", "secret", "confidential"]
    for term in sensitive_terms:
        if term in body.lower():
            logging.warning(f"Sensitive term detected in email body: {term}")
            return {
                "status": "error", 
                "message": f"Cannot send emails containing sensitive terms: {term}"
            }
    
    # In a real implementation, this would actually send the email
    # For this example, we'll just simulate it
    logging.info(f"Email sent to {to} with subject: {subject}")
    
    return {
        "status": "success", 
        "message": "Email sent successfully",
        "to": to,
        "subject": subject,
        "body_preview": body[:30] + "..." if len(body) > 30 else body
    }

# Create the agent with the secure tool
email_agent = LlmAgent(
    name="email_agent",
    model=DEFAULT_MODEL,
    tools=[send_email],
    description="An agent that can send emails with safety checks"
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
    agent=email_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Run the agent with safety checks
def run_email_agent(query):
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
        
    print("\n=== TESTING EMAIL AGENT WITH SAFETY CHECKS ===\n")
    
    # Test case 1: Valid request to allowed domain
    print("Test 1: Valid email to allowed domain")
    response = run_email_agent(
        "Send an email to user@mycompany.com with subject 'Meeting Today' and body 'Let's discuss the project progress.'"
    )
    print(f"Response: {response}\n")
    
    # Test case 2: Invalid email format
    print("Test 2: Invalid email format")
    response = run_email_agent(
        "Send an email to invalid-email with subject 'Hello' and body 'Test message.'"
    )
    print(f"Response: {response}\n")
    
    # Test case 3: Non-allowed domain
    print("Test 3: Non-allowed domain")
    response = run_email_agent(
        "Send an email to user@external.com with subject 'Hello' and body 'Test message.'"
    )
    print(f"Response: {response}\n")
    
    # Test case 4: Sensitive content
    print("Test 4: Sensitive content")
    response = run_email_agent(
        "Send an email to user@mycompany.com with subject 'Login Info' and body 'Your password is Admin123.'"
    )
    print(f"Response: {response}\n") 