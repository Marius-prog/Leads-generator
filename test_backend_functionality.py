#!/usr/bin/env python3
"""
Backend functionality test with sample data.
Tests the complete pipeline with mock data instead of real APIs.
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_lead_validator():
    """Test lead validation functionality."""
    print("Testing lead validator...")
    
    try:
        from leads.lead_validator import LeadValidator
        
        # Create test leads
        test_leads = [
            {
                'name': 'Test Company 1',
                'email': 'contact@testcompany1.com',
                'phone': '+1 (555) 123-4567',
                'website': 'https://testcompany1.com'
            },
            {
                'name': 'Test Company 2',
                'email': 'invalid-email',
                'phone': '555-234-5678',
                'website': 'https://testcompany2.com'
            },
            {
                'name': 'Test Company 3',
                'email': 'info@testcompany3.com',
                'phone': '+1-555-345-6789',
                'website': 'invalid-url'
            }
        ]
        
        # Test synchronous validation
        validator = LeadValidator()
        
        print("Testing single lead validation...")
        validated_lead = validator.validate_single_lead(test_leads[0])
        
        if 'email_valid' in validated_lead and 'phone_valid' in validated_lead:
            print(f"✅ Single lead validation working: email_valid={validated_lead.get('email_valid')}")
        else:
            print("❌ Single lead validation failed")
            return False
        
        # Test batch validation (async)
        print("Testing batch lead validation...")
        try:
            validated_leads = asyncio.run(validator.validate_leads_batch(test_leads))
            
            if len(validated_leads) == len(test_leads):
                valid_emails = sum(1 for lead in validated_leads if lead.get('email_valid', False))
                print(f"✅ Batch validation working: {valid_emails}/{len(validated_leads)} valid emails")
                
                # Test validation summary
                summary = validator.get_validation_summary(validated_leads)
                if 'total_leads' in summary:
                    print(f"✅ Validation summary working: {summary['total_leads']} total leads")
                else:
                    print("❌ Validation summary failed")
                    return False
            else:
                print("❌ Batch validation failed")
                return False
        except Exception as e:
            print(f"❌ Batch validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Lead validator test failed: {e}")
        return False

def test_pipeline_orchestrator_mock():
    """Test pipeline orchestrator with mock data."""
    print("\nTesting pipeline orchestrator...")
    
    try:
        from leads.pipeline_orchestrator import PipelineOrchestrator
        from config import LeadPipelineConfig
        
        # Create config with mock settings
        config = LeadPipelineConfig()
        orchestrator = PipelineOrchestrator(config)
        
        # Test campaign creation (this should work without API keys)
        campaign_id = orchestrator._create_campaign(
            business_type="test restaurants",
            location="Test City, CA", 
            max_results=5,
            campaign_name="Test Campaign",
            from_email=None
        )
        
        if campaign_id:
            print(f"✅ Campaign creation working: {campaign_id}")
        else:
            print("❌ Campaign creation failed")
            return False
        
        # Test pipeline status
        status = orchestrator.get_pipeline_status(campaign_id)
        if status and 'campaign_id' in status:
            print(f"✅ Pipeline status working: {status['status']}")
        else:
            print("❌ Pipeline status failed")
            return False
        
        # Test campaign listing
        campaigns = orchestrator.list_campaigns(limit=10)
        if isinstance(campaigns, list):
            print(f"✅ Campaign listing working: {len(campaigns)} campaigns")
        else:
            print("❌ Campaign listing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline orchestrator test failed: {e}")
        return False

def test_data_exporter():
    """Test data export functionality."""
    print("\nTesting data exporter...")
    
    try:
        from exporter import DataExporter, LeadExporter
        from models import Business
        
        # Create test businesses
        test_businesses = [
            Business(
                name="Test Restaurant 1",
                address="123 Main St, Test City, CA 94102",
                phone="+1 (555) 123-4567",
                email="contact@testrestaurant1.com",
                website="https://testrestaurant1.com",
                category="Restaurant",
                rating=4.5,
                reviews_count=127
            ),
            Business(
                name="Test Restaurant 2", 
                address="456 Oak Ave, Test City, CA 94103",
                phone="+1 (555) 234-5678",
                email="info@testrestaurant2.com",
                website="https://testrestaurant2.com",
                category="Restaurant",
                rating=4.2,
                reviews_count=89
            )
        ]
        
        # Test business data export
        exporter = DataExporter("data")
        
        # Test CSV export
        csv_file = exporter.export_data(test_businesses, "test_businesses", "csv")
        if Path(csv_file).exists():
            print(f"✅ CSV export working: {csv_file}")
        else:
            print("❌ CSV export failed")
            return False
        
        # Test JSON export
        json_file = exporter.export_data(test_businesses, "test_businesses", "json")
        if Path(json_file).exists():
            print(f"✅ JSON export working: {json_file}")
        else:
            print("❌ JSON export failed")
            return False
        
        # Test lead data export
        lead_exporter = LeadExporter("data")
        
        test_leads = [
            {
                'name': 'Test Lead 1',
                'email': 'lead1@example.com',
                'phone': '+1 (555) 111-1111',
                'status': 'validated',
                'email_valid': True,
                'phone_valid': True
            },
            {
                'name': 'Test Lead 2',
                'email': 'lead2@example.com',
                'phone': '+1 (555) 222-2222',
                'status': 'new',
                'email_valid': False,
                'phone_valid': True
            }
        ]
        
        lead_csv = lead_exporter.export_leads(test_leads, "test_leads", "csv")
        if Path(lead_csv).exists():
            print(f"✅ Lead CSV export working: {lead_csv}")
        else:
            print("❌ Lead CSV export failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data exporter test failed: {e}")
        return False

def test_google_places_scraper_mock():
    """Test Google Places scraper structure (without real API calls)."""
    print("\nTesting Google Places scraper structure...")
    
    try:
        from google_places_scraper import GooglePlacesScraper
        from config import ScrapingConfig
        
        # Test scraper initialization (should fail without API key)
        try:
            config = ScrapingConfig()
            config.google_places_api_key = ""  # Empty key
            scraper = GooglePlacesScraper(config)
        except ValueError as e:
            if "API key is required" in str(e):
                print("✅ API key validation working")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test helper methods directly
        # This tests the data processing without API calls
        sample_place_data = {
            'place_id': 'test_place_123',
            'name': 'Test Restaurant',
            'formatted_address': '123 Main St, San Francisco, CA 94102, USA',
            'formatted_phone_number': '+1 555-123-4567',
            'website': 'https://testrestaurant.com',
            'rating': 4.5,
            'user_ratings_total': 127,
            'types': ['restaurant', 'food', 'establishment'],
            'geometry': {
                'location': {
                    'lat': 37.7749,
                    'lng': -122.4194
                }
            }
        }
        
        # Create a scraper with dummy API key for testing structure methods
        config = ScrapingConfig()
        config.google_places_api_key = "dummy_key_for_testing"
        scraper = GooglePlacesScraper(config)
        
        # Test data structuring method
        structured_data = scraper._structure_place_data(sample_place_data)
        
        if structured_data and 'name' in structured_data and 'address' in structured_data:
            print(f"✅ Data structuring working: {structured_data['name']}")
        else:
            print("❌ Data structuring failed")
            return False
        
        # Test address parsing
        city, state, postal_code, country = scraper._parse_address("123 Main St, San Francisco, CA 94102, USA")
        if city and state and postal_code:
            print(f"✅ Address parsing working: {city}, {state} {postal_code}")
        else:
            print("❌ Address parsing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Google Places scraper test failed: {e}")
        return False

def test_configuration_system():
    """Test configuration system."""
    print("\nTesting configuration system...")
    
    try:
        from config import ScrapingConfig, LeadPipelineConfig
        
        # Test scraping config
        scraping_config = ScrapingConfig()
        scraping_errors = scraping_config.validate()
        
        if isinstance(scraping_errors, list):
            print(f"✅ Scraping config validation working: {len(scraping_errors)} errors")
        else:
            print("❌ Scraping config validation failed")
            return False
        
        # Test pipeline config
        pipeline_config = LeadPipelineConfig()
        pipeline_errors = pipeline_config.validate()
        
        if isinstance(pipeline_errors, list):
            print(f"✅ Pipeline config validation working: {len(pipeline_errors)} errors")
        else:
            print("❌ Pipeline config validation failed")
            return False
        
        # Test API status
        api_status = pipeline_config.get_api_status()
        if isinstance(api_status, dict) and 'database' in api_status:
            print(f"✅ API status working: database={api_status['database']}")
        else:
            print("❌ API status failed")
            return False
        
        # Test missing configs
        missing = pipeline_config.get_missing_configs()
        if isinstance(missing, list):
            print(f"✅ Missing configs detection working: {len(missing)} missing")
        else:
            print("❌ Missing configs detection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        return False

def test_utilities():
    """Test utility functions."""
    print("\nTesting utility functions...")
    
    try:
        from utils import clean_text, clean_phone, clean_email, clean_url, format_duration
        
        # Test text cleaning
        cleaned = clean_text("  Test   Text\n\twith\r\nweird   spacing  ")
        if cleaned == "Test Text with weird spacing":
            print("✅ Text cleaning working")
        else:
            print(f"❌ Text cleaning failed: '{cleaned}'")
            return False
        
        # Test phone cleaning
        phone = clean_phone("(555) 123-4567")
        if phone:
            print(f"✅ Phone cleaning working: {phone}")
        else:
            print("❌ Phone cleaning failed")
            return False
        
        # Test email cleaning
        email = clean_email("Test@Example.COM")
        if email == "test@example.com":
            print("✅ Email cleaning working")
        else:
            print(f"❌ Email cleaning failed: {email}")
            return False
        
        # Test URL cleaning
        url = clean_url("example.com")
        if url == "https://example.com":
            print("✅ URL cleaning working")
        else:
            print(f"❌ URL cleaning failed: {url}")
            return False
        
        # Test duration formatting
        duration = format_duration(125.5)
        if duration == "2.1m":
            print("✅ Duration formatting working")
        else:
            print(f"❌ Duration formatting failed: {duration}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Utilities test failed: {e}")
        return False

def main():
    """Run all backend functionality tests."""
    print("🧪 Running Backend Functionality Tests with Sample Data")
    print("=" * 70)
    
    tests = [
        ("Configuration System", test_configuration_system),
        ("Utilities", test_utilities),
        ("Lead Validator", test_lead_validator),
        ("Data Exporter", test_data_exporter),
        ("Google Places Scraper Structure", test_google_places_scraper_mock),
        ("Pipeline Orchestrator", test_pipeline_orchestrator_mock)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"Backend Functionality Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All backend functionality tests passed!")
        print("\nSystem capabilities verified:")
        print("✅ Data validation and cleaning")
        print("✅ Database operations")
        print("✅ Lead processing pipeline")
        print("✅ Data export functionality")
        print("✅ Configuration management")
        print("✅ Error handling and validation")
        
        print("\nReady for:")
        print("1. Frontend integration testing")
        print("2. Full stack testing")
        print("3. Real API key integration")
        print("4. Production deployment")
        
        return True
    else:
        print("❌ Some backend functionality tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
