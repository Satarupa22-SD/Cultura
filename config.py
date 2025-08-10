import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of FREE Gemini models (no paid pro models)
GEMINI_MODELS = [
    'models/gemini-1.5-flash',           # Gemini 1.5 Flash (recommended for free tier)
    'models/gemini-1.5-flash-8b',        # Gemini 1.5 Flash 8B (faster, smaller)  
    'models/gemini-2.0-flash',           # Gemini 2.0 Flash (default)
    'models/gemini-2.5-flash',          # Gemini 2.5 Flash
        # Vision/multimodal (not used for text-only)
]     
# Environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', GEMINI_MODELS[0])  # Default to 1.5-flash

def get_gemini_config():
    """
    Returns Gemini API configuration as a dictionary.
    Raises an error if the API key is missing.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    return {
        'api_key': GEMINI_API_KEY,
        'model': GEMINI_MODEL,
        'available_models': GEMINI_MODELS
    }