from dotenv import load_dotenv
load_dotenv()
import os
import google.generativeai as genai
import re
import random

# Import enhanced config
from config import get_gemini_config
# Import your location API
from geo import LocationAPI

# Simple task-to-model mapping
def get_model_for_task(task_complexity):
    if task_complexity == 'simple':
        return 'models/gemini-1.5-flash'
    elif task_complexity == 'medium':
        return 'models/gemini-2.0-flash'
    else:
        return 'models/gemini-2.5-flash'

# Configure Gemini API
try:
    gemini_config = get_gemini_config()  # No args now
    genai.configure(api_key=gemini_config['api_key'])
    print(f"Using model: {gemini_config['model']}")
except Exception as e:
    print(f"Configuration error: {e}")
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# User preference storage (in production, use a database)
user_preferences = {}

# Initialize location API
location_api = LocationAPI()

def _llm_chat(prompt, task_complexity='medium', use_random_model=True):
    """Enhanced LLM chat with model selection"""
    try:
        if use_random_model:
            model_name = random.choice(get_gemini_config()['available_models'])
        else:
            model_name = get_model_for_task(task_complexity)
        
        print(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error with {model_name}: {str(e)}")
        try:
            fallback_model = 'models/gemini-1.5-flash'
            if model_name == fallback_model:
                fallback_model = 'models/gemini-2.0-flash'
            print(f"Trying fallback model: {fallback_model}")
            model = genai.GenerativeModel(fallback_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as fallback_error:
            print(f"Fallback model also failed: {fallback_error}")
            return "I'm having trouble generating a response right now. Please try again."

def classify_intent(message):
    """Classify the intent of the user's message"""
    prompt = f"""
    You are an AI assistant specialized in fashion and lifestyle. Analyze the user's message and classify their intent into one of these categories:

    - skincare
    - event_dressing
    - travel
    - music
    - general_recommendation

    Message: "{message}"
    Respond with only the category name.
    """
    return _llm_chat(prompt, task_complexity='simple', use_random_model=False)

def get_enhanced_location_info(location_string):
    """Get enhanced location information using polygon API"""
    if not location_string or location_string.lower() == 'unknown':
        return None
    try:
        polygon_data = location_api.get_user_location_polygon(location_string)
        if polygon_data:
            return {
                'original_query': location_string,
                'display_name': polygon_data.get('display_name', ''),
                'source': polygon_data.get('source', ''),
                'bbox': polygon_data.get('bbox', []),
                'polygon_available': True
            }
    except Exception as e:
        print(f"Location API error: {e}")
    return {
        'original_query': location_string,
        'polygon_available': False
    }

def extract_user_info(message, user_id):
    """Extract and store user preferences"""
    prompt = f"""
    Extract user information from this message. Look for:
    - Location
    - Body Type
    - Style Preferences
    - Budget

    Message: "{message}"
    Respond in the format:
    Location: ...
    Body Type: ...
    Style Preferences: ...
    Budget: ...
    """
    extracted = _llm_chat(prompt, task_complexity='medium')
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    lines = extracted.strip().split('\n')
    for line in lines:
        if 'Location:' in line:
            location = line.split('Location:')[1].strip()
            if location != "unknown":
                user_preferences[user_id]['location'] = location
                enhanced_location = get_enhanced_location_info(location)
                if enhanced_location:
                    user_preferences[user_id]['enhanced_location'] = enhanced_location
        elif 'Body Type:' in line:
            body_type = line.split('Body Type:')[1].strip()
            if body_type != "unknown":
                user_preferences[user_id]['body_type'] = body_type
        elif 'Style Preferences:' in line:
            style = line.split('Style Preferences:')[1].strip()
            if style != "unknown":
                user_preferences[user_id]['style_preferences'] = style
        elif 'Budget:' in line:
            budget = line.split('Budget:')[1].strip()
            if budget != "unknown":
                user_preferences[user_id]['budget'] = budget
    return user_preferences[user_id]

def generate_fashion_response(message, intent_category, user_id):
    """Generate a fashion/lifestyle recommendation"""
    user_info = user_preferences.get(user_id, {})
    location = user_info.get('location', 'unknown')
    enhanced_location = user_info.get('enhanced_location', {})
    body_type = user_info.get('body_type', 'unknown')
    style_preferences = user_info.get('style_preferences', 'unknown')
    budget = user_info.get('budget', 'unknown')

    location_context = ""
    if enhanced_location and enhanced_location.get('polygon_available'):
        location_context = f"""
        Enhanced Location Information:
        - User mentioned: {location}
        - Full location: {enhanced_location.get('display_name', '')}
        """
    elif location != 'unknown':
        location_context = f"User Location: {location}"

    prompt = f"""
    You are Cultura, an expert fashion and lifestyle assistant. 
    You are a helpful assistant who can help the user with their fashion and lifestyle needs.

    Instructions:
    1. Provide recommendations as a numbered list (1., 2., 3., etc.).
    2. Do not use bold text, markdown, or special formatting.
    3. Keep the tone casual, friendly, and concise.
    4. Include specific product names, brands, and styling tips where possible.
    5. Ensure suggestions are relevant to the user's location, body type, style preferences, and budget.
    6. Keep the entire response under 300 words.
    7. If more details are needed (location, body type, budget), ask politely at the end.
    8. Do not use bold text, markdown, or special formatting.

    Example:
    1. Linen maxi dress from Mango — breathable and perfect for hot weather.
    2. Tailored blazer from Zara — works for both office and evening events.
    3. Leather sandals from Clarks — stylish yet comfortable for walking.

    {location_context}

    User Information:
    - Body Type: {body_type}
    - Style Preferences: {style_preferences}
    - Budget: {budget}
    - Intent Category: {intent_category}

    User Message: "{message}"
    """
    return _llm_chat(prompt, task_complexity='complex')

# Model performance tracking
model_performance = {model: {'success': 0, 'failures': 0} for model in get_gemini_config()['available_models']}

def track_model_performance(model_name, success=True):
    if success:
        model_performance[model_name]['success'] += 1
    else:
        model_performance[model_name]['failures'] += 1

def get_best_performing_model():
    best_model = None
    best_ratio = 0
    for model, stats in model_performance.items():
        total = stats['success'] + stats['failures']
        if total > 0:
            ratio = stats['success'] / total
            if ratio > best_ratio:
                best_ratio = ratio
                best_model = model
    return best_model or get_gemini_config()['available_models'][0]

def process_user_message(message, user_id):
    extract_user_info(message, user_id)
    greetings = ["hey", "hi", "hello", "hola", "yo", "greetings"]
    if message.strip().lower() in greetings:
        return "Hey! I am Cultura, your personal stylist. How can I help you today?"
    if (len(message.strip().split()) == 1 and message.strip().lower() not in greetings):
        if re.fullmatch(r"[a-zA-Z0-9]+", message.strip()):
            return "Hey, I didn't understand you. Could you please elaborate?"
    intent = classify_intent(message)
    if intent not in ['skincare', 'event_dressing', 'travel', 'music', 'general_recommendation']:
        return "Hey, I didn't understand you. Could you please elaborate?"
    return generate_fashion_response(message, intent, user_id)

def handle_telegram_message(message_text, user_id):
    try:
        response = process_user_message(message_text, user_id)
        return response.replace('\\n', '\n')
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}. Please try again! 😊"
