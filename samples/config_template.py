"""
Configuration Template for ADK Samples

This file shows how to properly import and use the centralized configuration 
from the project root in any sample.
"""

import sys
import os

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from the root config
from config import (
    GOOGLE_API_KEY, 
    DEFAULT_MODEL,
    DEFAULT_APP_NAME,
    DEFAULT_USER_ID,
    DEFAULT_SESSION_ID,
    MAX_RETRIES,
    RETRY_DELAY
)

import google.generativeai as genai

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)

# How to check if API key is available
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY is not set. Please set it in your .env file or environment variables.")
    sys.exit(1)

# Example of using other configuration values
print(f"Using model: {DEFAULT_MODEL}")
print(f"Application name: {DEFAULT_APP_NAME}")
print(f"User ID: {DEFAULT_USER_ID}")
print(f"Session ID: {DEFAULT_SESSION_ID}")
print(f"Max retries: {MAX_RETRIES}")
print(f"Retry delay: {RETRY_DELAY}") 