"""
Configuration file for ADK samples.

This file demonstrates how to manage configuration settings for ADK applications.
In a real application, you would likely load these from environment variables
using something like python-dotenv.

Example:
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Then get values like this:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in cwd

GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY")
DEFAULT_MODEL     = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
DEFAULT_APP_NAME  = os.getenv("DEFAULT_APP_NAME", "my_adk_app")
DEFAULT_USER_ID   = os.getenv("DEFAULT_USER_ID", "default_user")
DEFAULT_SESSION_ID= os.getenv("DEFAULT_SESSION_ID", "default_session")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))

# HOW TO USE THIS CONFIG:
# 
# 1. Replace "your_api_key_here" with your actual Google AI API key
# 
# 2. In your sample scripts, import and use the config like this:
#
#    from samples.config import GOOGLE_API_KEY
#    import google.generativeai as genai
#    
#    # Configure the Google AI client
#    genai.configure(api_key=GOOGLE_API_KEY)
#
# 3. Then you can use the configured genai client in your code 