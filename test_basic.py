#!/usr/bin/env python3
"""
Basic functionality test for the lead generation system.
Tests core components that don't require external APIs.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if we can import our core modules."""
    print("Testing imports...")
    
    try:
        # Test core Python modules
        import json
        import sqlite3
        import logging
        from datetime import datetime
        print("✅ Core Python modules imported successfully")
        
        # Test our local modules
        sys.path.append(str(Path(__file__).parent))
        
        from models import Business, ScrapingResult
        print("✅ Models imported successfully")
        
        from config import ScrapingConfig, LeadPipelineConfig
        print("✅ Config imported successfully")
        
        from utils import clean_text, setup_logging
        print("✅ Utils imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models():
    """Test data models."""
    print("\nTesting models...")
    
    try:
        from models import Business
        
        # Test business model
        business = Business(
            name="Test Company",
            address="123 Main St, San Francisco, CA 94102",
            phone="(555) 123-4567",
            email="test@example.com",
            website="https://example.com"
        )
        
        print(f"✅ Business model created: {business.name}")
        print(f"   Cleaned phone: {business.phone}")
        print(f"   Cleaned email: {business.email}")
        print(f"   Cleaned website: {business.website}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_database():
    """Test SQLite database functionality."""
    print("\nTesting database...")
    
    try:
        from leads.sqlite_manager import SQLiteManager
        
        # Create test database
        db = SQLiteManager("test_leads.db")
        print("✅ Database manager created")
        
        # Test database info
        info = db.get_database_info()
        print(f"✅ Database info: {info['campaigns_count']} campaigns, {info['leads_count']} leads")
        
        # Cleanup test database
        os.remove("test_leads.db")
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_config():
    """Test configuration system."""
    print("\nTesting configuration...")
    
    try:
        from config import ScrapingConfig, LeadPipelineConfig
        
        # Test basic config
        scraping_config = ScrapingConfig()
        print(f"✅ Scraping config created: {scraping_config.max_results} max results")
        
        pipeline_config = LeadPipelineConfig()
        print(f"✅ Pipeline config created: {pipeline_config.max_leads} max leads")
        
        # Test validation
        errors = pipeline_config.validate()
        print(f"✅ Config validation: {len(errors)} errors found")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running basic functionality tests for Lead Generation System")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_models,
        test_config,
        test_database
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All basic tests passed! The system structure is working correctly.")
        print("\nNext steps:")
        print("1. Add your API keys to .env file (copy from .env.template)")
        print("2. Install remaining dependencies: uv pip install -r requirements.txt")
        print("3. Run: python main.py test")
        print("4. Start full stack: ./start_fullstack.sh")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
