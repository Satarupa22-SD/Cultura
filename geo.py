import requests
from typing import Dict, Optional

class LocationAPI:
    """Simple location API using free Nominatim service"""
    
    def __init__(self):
        self.base_url = 'https://nominatim.openstreetmap.org/search'
        
    def get_user_location_polygon(self, location_query: str) -> Optional[Dict]:
        """Get location data using free Nominatim service"""
        if not location_query or location_query.lower() == 'unknown':
            return None
            
        try:
            params = {
                'q': location_query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'FashionApp/1.0 (your-email@example.com)'  # Replace with your email
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    return {
                        'display_name': result.get('display_name', ''),
                        'source': 'nominatim',
                        'latitude': float(result.get('lat', 0)),
                        'longitude': float(result.get('lon', 0)),
                        'bbox': result.get('boundingbox', []),
                        'address': result.get('address', {}),
                        'place_id': result.get('place_id', ''),
                        'importance': result.get('importance', 0)
                    }
                    
        except Exception as e:
            print(f"Location API error: {e}")
            
        return None
    
    def get_location_info(self, location: str) -> Dict:
        """Get structured location information"""
        data = self.get_user_location_polygon(location)
        
        if not data:
            return {'city': None, 'country': None, 'found': False}
        
        address = data.get('address', {})
        
        return {
            'city': address.get('city') or address.get('town') or address.get('village'),
            'state': address.get('state'),
            'country': address.get('country'),
            'display_name': data.get('display_name'),
            'found': True
        }