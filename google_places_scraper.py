"""
Google Places API scraper for reliable business data collection.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import requests
import time
from config import ScrapingConfig
from utils import clean_text, clean_phone, clean_url, ProgressTracker, RateLimiter

logger = logging.getLogger(__name__)

class GooglePlacesScraper:
    """Google Places API scraper for business data."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        """Initialize the scraper with configuration."""
        self.config = config or ScrapingConfig()
        self.api_key = self.config.google_places_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.rate_limiter = RateLimiter(calls_per_second=10)  # Google Places allows up to 10 QPS
        
        if not self.api_key:
            raise ValueError("Google Places API key is required")
    
    def search_businesses(self, query: str, location: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for businesses using Google Places API."""
        logger.info(f"Searching for '{query}' in '{location}' (max {max_results} results)")
        
        try:
            # Search for places
            places = self._search_places(query, location, max_results)
            
            if not places:
                logger.warning("No places found")
                return []
            
            # Get detailed information for each place
            detailed_places = self._get_place_details_batch(places)
            
            logger.info(f"Successfully retrieved {len(detailed_places)} business details")
            return detailed_places
            
        except Exception as e:
            logger.error(f"Error searching businesses: {e}")
            return []
    
    def _search_places(self, query: str, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search for places using text search."""
        places = []
        next_page_token = None
        
        while len(places) < max_results:
            # Prepare request parameters
            params = {
                'query': f"{query} in {location}",
                'key': self.api_key,
                'language': self.config.language,
                'region': self.config.region
            }
            
            if next_page_token:
                params['pagetoken'] = next_page_token
            
            # Make API request
            try:
                time.sleep(self.config.request_delay)  # Rate limiting
                
                response = requests.get(
                    f"{self.base_url}/textsearch/json",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') != 'OK':
                    logger.warning(f"API response status: {data.get('status')}")
                    if data.get('status') == 'ZERO_RESULTS':
                        break
                    continue
                
                # Add results
                results = data.get('results', [])
                places.extend(results)
                
                logger.info(f"Retrieved {len(results)} places, total: {len(places)}")
                
                # Check for next page
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
                
                # Wait for next page token to become valid
                if next_page_token:
                    time.sleep(2)  # Google requires short delay for next page
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        # Limit to max_results
        return places[:max_results]
    
    def _get_place_details_batch(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get detailed information for a batch of places."""
        detailed_places = []
        tracker = ProgressTracker(len(places), "Fetching place details")
        
        for place in places:
            place_id = place.get('place_id')
            if not place_id:
                tracker.update()
                continue
            
            try:
                details = self._get_place_details(place_id)
                if details:
                    # Merge basic info with detailed info
                    merged_data = self._merge_place_data(place, details)
                    detailed_places.append(merged_data)
                
                tracker.update()
                time.sleep(self.config.request_delay)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error getting details for place {place_id}: {e}")
                tracker.update()
                continue
        
        tracker.finish()
        return detailed_places
    
    def _get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific place."""
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': (
                'name,formatted_address,formatted_phone_number,website,'
                'rating,user_ratings_total,business_status,opening_hours,'
                'geometry,types,price_level,photos'
            ),
            'language': self.config.language
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/details/json",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('result')
            else:
                logger.warning(f"Place details API status: {data.get('status')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting place details: {e}")
            return None
    
    def _merge_place_data(self, basic_place: Dict[str, Any], detailed_place: Dict[str, Any]) -> Dict[str, Any]:
        """Merge basic place data with detailed place data."""
        # Start with detailed data as base
        merged = detailed_place.copy()
        
        # Add/override with basic data where needed
        merged.update({
            'place_id': basic_place.get('place_id'),
            'reference': basic_place.get('reference')
        })
        
        # Clean and structure the data
        return self._structure_place_data(merged)
    
    def _structure_place_data(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure place data into consistent format."""
        # Extract geometry
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        # Extract address components
        address = clean_text(place_data.get('formatted_address', ''))
        city, state, postal_code, country = self._parse_address(address)
        
        # Structure the data
        structured = {
            'place_id': place_data.get('place_id', ''),
            'name': clean_text(place_data.get('name', '')),
            'address': address,
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'country': country,
            'phone': clean_phone(place_data.get('formatted_phone_number', '')),
            'website': clean_url(place_data.get('website', '')),
            'rating': place_data.get('rating'),
            'reviews_count': place_data.get('user_ratings_total'),
            'latitude': location.get('lat'),
            'longitude': location.get('lng'),
            'category': self._extract_primary_category(place_data.get('types', [])),
            'business_status': place_data.get('business_status', ''),
            'price_level': place_data.get('price_level'),
            'opening_hours': self._extract_opening_hours(place_data.get('opening_hours', {})),
            'photos': len(place_data.get('photos', [])),
            'google_url': f"https://maps.google.com/maps/place/?q=place_id:{place_data.get('place_id', '')}"
        }
        
        return structured
    
    def _parse_address(self, address: str) -> tuple:
        """Parse address into components."""
        if not address:
            return '', '', '', ''
        
        # Simple address parsing
        parts = [part.strip() for part in address.split(',')]
        
        city = state = postal_code = country = ''
        
        if len(parts) >= 1:
            country = parts[-1].strip()
        
        if len(parts) >= 2:
            # Check if second to last part has state + zip pattern
            state_zip_part = parts[-2].strip()
            
            # Pattern for US addresses: "State ZIP"
            import re
            us_pattern = re.match(r'^([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', state_zip_part)
            if us_pattern:
                state = us_pattern.group(1)
                postal_code = us_pattern.group(2)
                
                if len(parts) >= 3:
                    city = parts[-3].strip()
            else:
                # Assume it's a city
                city = state_zip_part
        
        return city, state, postal_code, country
    
    def _extract_primary_category(self, types: List[str]) -> str:
        """Extract primary business category from types."""
        if not types:
            return ''
        
        # Filter out generic types
        generic_types = {'establishment', 'point_of_interest', 'premise', 'subpremise'}
        filtered_types = [t for t in types if t not in generic_types]
        
        if filtered_types:
            # Return first non-generic type, formatted nicely
            primary_type = filtered_types[0]
            return primary_type.replace('_', ' ').title()
        
        return types[0].replace('_', ' ').title() if types else ''
    
    def _extract_opening_hours(self, opening_hours: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and structure opening hours."""
        if not opening_hours:
            return None
        
        return {
            'open_now': opening_hours.get('open_now'),
            'weekday_text': opening_hours.get('weekday_text', [])
        }

# Standalone function for testing
def test_scraper(query: str = "restaurants", location: str = "New York, NY", max_results: int = 5):
    """Test the Google Places scraper."""
    import os
    from utils import setup_logging
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Check API key
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ GOOGLE_PLACES_API_KEY environment variable not set")
        return
    
    # Create scraper
    config = ScrapingConfig()
    config.google_places_api_key = api_key
    
    scraper = GooglePlacesScraper(config)
    
    # Test search
    print(f"🔍 Testing search: '{query}' in '{location}'")
    results = scraper.search_businesses(query, location, max_results)
    
    print(f"\n✅ Found {len(results)} businesses:")
    for i, business in enumerate(results, 1):
        print(f"{i}. {business.get('name', 'N/A')}")
        print(f"   Address: {business.get('address', 'N/A')}")
        print(f"   Phone: {business.get('phone', 'N/A')}")
        print(f"   Website: {business.get('website', 'N/A')}")
        print(f"   Rating: {business.get('rating', 'N/A')} ({business.get('reviews_count', 0)} reviews)")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        query = sys.argv[1]
        location = sys.argv[2]
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        test_scraper(query, location, max_results)
    else:
        print("Usage: python google_places_scraper.py <query> <location> [max_results]")
        print("Example: python google_places_scraper.py 'restaurants' 'New York, NY' 5")
