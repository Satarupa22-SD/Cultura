# Enhanced location-based fashion recommendations with LLM classification
from typing import Dict, List, Optional
import json
import re
from geo import LocationAPI

class LocationBasedFashionAssistant:
    """Enhanced fashion assistant with LLM-powered location classification"""
    
    def __init__(self, llm_chat_function):
        self.location_api = LocationAPI() 
        self.location_cache = {}  # Cache location data to avoid repeated API calls
        self.classification_cache = {}  # Cache LLM classifications
        self.llm_chat = llm_chat_function  # Your _llm_chat function
        
    def get_enhanced_location_info(self, location: str) -> Optional[Dict]:
        """Get detailed location information with LLM-powered classification"""
        if location in self.location_cache:
            return self.location_cache[location]
            
        polygon_data = self.location_api.get_user_location_polygon(location)
        
        if polygon_data:
            # Extract basic info from polygon data
            display_name = polygon_data.get('display_name', '')
            address_details = polygon_data.get('address_details', {})
            
            # Get basic location components
            location_info = {
                'original': location,
                'display_name': display_name,
                'city': address_details.get('city') or address_details.get('town') or address_details.get('village'),
                'state': address_details.get('state'),
                'country': address_details.get('country'),
                'latitude': polygon_data.get('latitude', 0),
                'longitude': polygon_data.get('longitude', 0),
                'source': polygon_data.get('source', 'nominatim')
            }
            
            # Use LLM to classify location and get fashion market data
            llm_classification = self._get_llm_location_classification(location_info)
            location_info.update(llm_classification)
            
            self.location_cache[location] = location_info
            return location_info
            
        return None
    
    def _get_llm_location_classification(self, location_info: Dict) -> Dict:
        """Use LLM to classify location and get comprehensive fashion market data"""
        
        location_key = f"{location_info.get('city', '')}-{location_info.get('country', '')}"
        
        # Check cache first
        if location_key in self.classification_cache:
            return self.classification_cache[location_key]
        
        display_name = location_info.get('display_name', '')
        city = location_info.get('city', 'Unknown')
        country = location_info.get('country', 'Unknown')
        
        prompt = f"""
        You are a global fashion market expert. Analyze this location and provide comprehensive fashion market information:
        
        Location: {display_name}
        City: {city}
        Country: {country}
        
        Provide information in this exact JSON format:
        {{
            "region": "geographical region (e.g., south_asia, europe, north_america, southeast_asia, middle_east, africa, oceania)",
            "climate_zone": "climate type (tropical, subtropical, temperate, arid, continental, oceanic, mountain)",
            "fashion_market": "market classification (indian, american, european, british, japanese, etc.)",
            "local_brands": ["list of 6-8 popular local fashion brands actually available in this location"],
            "available_stores": ["list of 6-8 popular stores/retailers in this location"],
            "online_platforms": ["list of popular online shopping platforms for this region"],
            "cultural_considerations": ["list of 3-5 cultural factors affecting fashion choices"],
            "seasonal_info": "brief description of seasonal fashion needs and weather patterns",
            "price_range_info": "typical price ranges and currency information",
            "popular_styles": ["list of 4-6 popular fashion styles in this region"],
            "climate_recommendations": {{
                "fabrics": ["recommended fabric types for this climate"],
                "colors": ["suitable color palettes"],
                "styles": ["appropriate clothing styles"],
                "essentials": ["weather-essential items"]
            }}
        }}
        
        Be accurate and specific. Only include brands/stores that are actually available in this location.
        Consider the local climate, culture, economy, and fashion preferences.
        """
        
        try:
            response = self.llm_chat(prompt, task_complexity='complex')
            
            # Parse JSON response
            classification = self._parse_llm_classification_response(response)
            
            # Cache the result
            self.classification_cache[location_key] = classification
            
            return classification
            
        except Exception as e:
            print(f"LLM location classification error: {e}")
            return self._get_basic_fallback_classification(location_info)
    
    def _parse_llm_classification_response(self, response: str) -> Dict:
        """Parse LLM response into classification data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                classification = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['region', 'climate_zone', 'fashion_market']
                for field in required_fields:
                    if field not in classification:
                        classification[field] = 'unknown'
                
                # Ensure lists exist
                list_fields = ['local_brands', 'available_stores', 'online_platforms', 'cultural_considerations', 'popular_styles']
                for field in list_fields:
                    if field not in classification or not isinstance(classification[field], list):
                        classification[field] = []
                
                # Ensure climate_recommendations exists
                if 'climate_recommendations' not in classification:
                    classification['climate_recommendations'] = {
                        'fabrics': [], 'colors': [], 'styles': [], 'essentials': []
                    }
                
                return classification
            else:
                # Try to parse as text if JSON extraction fails
                return self._parse_text_classification_response(response)
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return self._parse_text_classification_response(response)
    
    def _parse_text_classification_response(self, response: str) -> Dict:
        """Parse non-JSON LLM response as fallback"""
        classification = {
            'region': 'unknown',
            'climate_zone': 'temperate',
            'fashion_market': 'international',
            'local_brands': [],
            'available_stores': [],
            'online_platforms': [],
            'cultural_considerations': [],
            'seasonal_info': 'Varies by season',
            'price_range_info': 'Varies',
            'popular_styles': [],
            'climate_recommendations': {
                'fabrics': [], 'colors': [], 'styles': [], 'essentials': []
            }
        }
        
        # Basic parsing logic for text responses
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('-'):
                parts = line.split(':', 1)
                key = parts[0].strip().lower().replace(' ', '_').replace('-', '_')
                value = parts[1].strip()
                
                if key in ['region', 'climate_zone', 'fashion_market', 'seasonal_info', 'price_range_info']:
                    classification[key] = value.strip('"')
                elif key in ['local_brands', 'available_stores', 'online_platforms', 'cultural_considerations', 'popular_styles']:
                    # Parse list values
                    if '[' in value and ']' in value:
                        items = re.findall(r'"([^"]+)"', value)
                        if not items:
                            items = [item.strip() for item in value.replace('[', '').replace(']', '').split(',')]
                        classification[key] = [item.strip('"').strip() for item in items if item.strip()]
        
        return classification
    
    def _get_basic_fallback_classification(self, location_info: Dict) -> Dict:
        """Basic fallback classification if LLM fails completely"""
        country = location_info.get('country', '').lower()
        
        # Simple country-based fallbacks
        fallback_data = {
            'region': 'unknown',
            'climate_zone': 'temperate',
            'fashion_market': 'international',
            'local_brands': ['Zara', 'H&M', 'Uniqlo'],
            'available_stores': ['Local malls', 'Online retailers'],
            'online_platforms': ['Amazon', 'Local e-commerce'],
            'cultural_considerations': ['Weather appropriate', 'Occasion suitable'],
            'seasonal_info': 'Four seasons with varying temperatures',
            'price_range_info': 'Mid-range pricing',
            'popular_styles': ['Casual', 'Smart casual', 'Formal'],
            'climate_recommendations': {
                'fabrics': ['Cotton', 'Polyester blends'],
                'colors': ['Neutral tones', 'Seasonal colors'],
                'styles': ['Layerable pieces', 'Versatile basics'],
                'essentials': ['Jacket', 'Comfortable shoes']
            }
        }
        
        # Basic region detection
        if any(term in country for term in ['india', 'pakistan', 'bangladesh', 'sri lanka']):
            fallback_data['region'] = 'south_asia'
            fallback_data['climate_zone'] = 'tropical'
        elif any(term in country for term in ['united states', 'usa', 'canada']):
            fallback_data['region'] = 'north_america'
        elif any(term in country for term in ['united kingdom', 'france', 'germany', 'spain', 'italy']):
            fallback_data['region'] = 'europe'
        
        return fallback_data
    
    def get_climate_appropriate_recommendations(self, location_info: Dict, season: str = None) -> Dict:
        """Get clothing recommendations based on LLM-analyzed climate data"""
        climate_recs = location_info.get('climate_recommendations', {})
        
        # If LLM provided recommendations, use them
        if climate_recs and any(climate_recs.values()):
            return climate_recs
        
        # Fallback to basic climate-based recommendations
        climate_zone = location_info.get('climate_zone', 'temperate')
        
        fallback_recs = {
            'tropical': {
                'fabrics': ['cotton', 'linen', 'breathable synthetics', 'modal'],
                'colors': ['light colors', 'pastels', 'whites', 'bright colors'],
                'styles': ['loose fitting', 'sleeveless', 'midi dresses', 'palazzo pants'],
                'essentials': ['sun hat', 'sunglasses', 'light scarf', 'comfortable sandals']
            },
            'arid': {
                'fabrics': ['cotton', 'linen', 'lightweight wool'],
                'colors': ['earth tones', 'light colors', 'avoid dark colors'],
                'styles': ['full coverage', 'loose fitting', 'long sleeves'],
                'essentials': ['wide-brimmed hat', 'sunglasses', 'scarf', 'closed shoes']
            },
            'temperate': {
                'fabrics': ['cotton', 'wool blends', 'denim', 'knits'],
                'colors': ['versatile neutrals', 'seasonal colors'],
                'styles': ['layerable pieces', 'versatile basics'],
                'essentials': ['light jacket', 'comfortable shoes', 'scarf']
            }
        }
        
        return fallback_recs.get(climate_zone, fallback_recs['temperate'])
    
    def generate_location_enhanced_prompt(self, user_message: str, location_info: Dict) -> str:
        """Generate enhanced prompt with LLM-analyzed location information"""
        
        climate_recs = self.get_climate_appropriate_recommendations(location_info)
        
        enhanced_prompt = f"""
        You are Cultura, a location-aware fashion expert with access to comprehensive location data:
        
        LOCATION DETAILS:
        - City: {location_info.get('city', 'Unknown')}
        - State/Region: {location_info.get('state', 'Unknown')}
        - Country: {location_info.get('country', 'Unknown')}
        - Region: {location_info.get('region', 'unknown')}
        - Climate Zone: {location_info.get('climate_zone', 'temperate')}
        - Fashion Market: {location_info.get('fashion_market', 'international')}
        
        LOCAL FASHION ECOSYSTEM:
        - Available Local Brands: {', '.join(location_info.get('local_brands', []))}
        - Popular Stores: {', '.join(location_info.get('available_stores', []))}
        - Online Platforms: {', '.join(location_info.get('online_platforms', []))}
        - Price Range: {location_info.get('price_range_info', 'Varies')}
        
        CULTURAL & CLIMATE CONTEXT:
        - Cultural Considerations: {', '.join(location_info.get('cultural_considerations', []))}
        - Popular Local Styles: {', '.join(location_info.get('popular_styles', []))}
        - Seasonal Info: {location_info.get('seasonal_info', 'Varies by season')}
        
        CLIMATE-APPROPRIATE RECOMMENDATIONS:
        - Recommended Fabrics: {', '.join(climate_recs.get('fabrics', []))}
        - Suitable Colors: {', '.join(climate_recs.get('colors', []))}
        - Style Suggestions: {', '.join(climate_recs.get('styles', []))}
        - Weather Essentials: {', '.join(climate_recs.get('essentials', []))}
        
        USER MESSAGE: "{user_message}"
        
        INSTRUCTIONS:
        1. Provide fashion advice using SPECIFIC brands and stores from the local ecosystem above
        2. Consider the climate zone and cultural factors for appropriateness
        3. Include specific product recommendations with styling tips
        4. Mention where they can shop (specific stores/online platforms)
        5. Consider the local price range and popular styles
        6. Give 3-5 concrete, actionable recommendations
        
        Keep response under 300 words. Be enthusiastic and specific. Use occasional emojis. No markdown formatting.
        """
        
        return enhanced_prompt

# Integration functions
def enhanced_location_extract(message: str, user_id: str, llm_chat_function) -> Optional[Dict]:
    """Enhanced location extraction with LLM classification"""
    assistant = LocationBasedFashionAssistant(llm_chat_function)
    
    # Look for location patterns in the message
    location_patterns = [
        r"(?:from|in|at|live in|based in|located in)\s+([A-Z][a-zA-Z\s,]+)",
        r"([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)",  # City, Country
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b(?=\s+(?:city|area|region))",
        r"I'm in ([A-Z][a-zA-Z\s,]+)"
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        for match in matches:
            location = match.strip()
            if len(location) > 2 and location.lower() not in ['the', 'and', 'for', 'with']:
                location_info = assistant.get_enhanced_location_info(location)
                if location_info:
                    return location_info
    
    return None

def generate_enhanced_fashion_response(message: str, intent_category: str, user_id: str, llm_chat_function) -> str:
    """Enhanced fashion response with LLM-powered location analysis"""
    
    # Get enhanced location information
    location_info = enhanced_location_extract(message, user_id, llm_chat_function)
    
    if location_info:
        assistant = LocationBasedFashionAssistant(llm_chat_function)
        enhanced_prompt = assistant.generate_location_enhanced_prompt(message, location_info)
        
        # Use the LLM function to generate response
        response = llm_chat_function(enhanced_prompt, task_complexity='complex')
        return response.strip()
    else:
        # Fallback if no location detected
        return "I'd love to give you location-specific advice! Could you let me know which city/country you're in?"

# Test function
def test_llm_location_enhanced_fashion(llm_chat_function):
    """Test the LLM-enhanced location-based fashion recommendations"""
    test_cases = [
        "I'm from Mumbai and need summer office wear",
        "Looking for winter coats in New York", 
        "Need ethnic wear suggestions for wedding in Delhi",
        "What to wear in London for a casual dinner?",
        "Concert outfit for Tokyo nightlife"
    ]
    
    for message in test_cases:
        print(f"\n--- Testing: {message} ---")
        response = generate_enhanced_fashion_response(message, "general_recommendation", "test_user", llm_chat_function)
        print(response)
        print("-" * 50)

if __name__ == "__main__":
    # Mock LLM function for testing
    def mock_llm_chat(prompt, task_complexity='medium'):
        return '{"region": "south_asia", "climate_zone": "tropical", "local_brands": ["Fabindia", "Myntra", "Ajio"], "fashion_market": "indian"}'
    
    test_llm_location_enhanced_fashion(mock_llm_chat)