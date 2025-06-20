#!/usr/bin/env python3
"""
Lead Generation System - Main CLI Interface
A comprehensive lead generation system with both backend Python pipeline and frontend React dashboard.
"""

import click
import asyncio
import sys
import os
from pathlib import Path
import json
import logging
from typing import Optional, List

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import ScrapingConfig, LeadPipelineConfig
from models import Business, ScrapingResult
from utils import setup_logging, clean_filename
from leads.pipeline_orchestrator import PipelineOrchestrator
from leads.sqlite_manager import SQLiteManager
from google_places_scraper import GooglePlacesScraper

# Setup logging
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Lead Generation System - Comprehensive business lead generation with AI-powered research and personalization."""
    pass

@cli.command()
@click.option('--check-dependencies', is_flag=True, help='Check if all dependencies are installed')
def install(check_dependencies):
    """Install required dependencies."""
    try:
        import subprocess
        
        if check_dependencies:
            click.echo("Checking dependencies...")
            # Check key dependencies
            try:
                import selenium, requests, pandas, click, pydantic
                import fastapi, uvicorn, anthropic
                click.echo("✅ All key dependencies are available")
                return
            except ImportError as e:
                click.echo(f"❌ Missing dependency: {e}")
                return
        
        click.echo("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        click.echo("✅ Dependencies installed successfully")
        
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to install dependencies")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--query', default='coffee shops', help='Search query for testing')
@click.option('--location', default='San Francisco, CA', help='Location for testing')
@click.option('--max-results', default=5, help='Maximum results for testing')
def test(query, location, max_results):
    """Quick functionality test with sample data."""
    click.echo(f"🧪 Testing lead generation system...")
    click.echo(f"Query: {query}")
    click.echo(f"Location: {location}")
    click.echo(f"Max results: {max_results}")
    
    try:
        # Test Google Places API integration
        click.echo("\n1. Testing Google Places API...")
        from google_places_scraper import GooglePlacesScraper
        scraper = GooglePlacesScraper()
        
        # Create a simple test
        results = scraper.search_businesses(query, location, max_results=max_results)
        
        if results:
            click.echo(f"✅ Found {len(results)} businesses")
            for i, business in enumerate(results[:3], 1):
                click.echo(f"   {i}. {business.get('name', 'N/A')} - {business.get('address', 'N/A')}")
        else:
            click.echo("⚠️  No businesses found - check API configuration")
        
        # Test database connectivity
        click.echo("\n2. Testing database connectivity...")
        db = SQLiteManager()
        click.echo("✅ Database connection successful")
        
        click.echo("\n✅ Basic functionality test completed")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

@cli.command()
@click.argument('business_type')
@click.option('--location', required=True, help='Location to search (e.g., "New York, NY")')
@click.option('--max-results', default=50, help='Maximum number of businesses to scrape')
@click.option('--format', 'output_format', default='csv', type=click.Choice(['csv', 'json', 'excel']), help='Output format')
@click.option('--extract-emails', is_flag=True, help='Extract emails from business websites')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def scrape(business_type, location, max_results, output_format, extract_emails, verbose):
    """Original Google Maps scraping functionality."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)
    
    click.echo(f"🔍 Scraping {business_type} in {location}")
    
    try:
        # Use Google Places API scraper
        scraper = GooglePlacesScraper()
        results = scraper.search_businesses(business_type, location, max_results=max_results)
        
        if not results:
            click.echo("❌ No businesses found")
            return
        
        # Convert to Business objects
        businesses = []
        for result in results:
            business = Business(
                name=result.get('name', ''),
                address=result.get('address', ''),
                phone=result.get('phone', ''),
                website=result.get('website', ''),
                rating=result.get('rating'),
                reviews_count=result.get('reviews_count'),
                category=result.get('category', ''),
                latitude=result.get('latitude'),
                longitude=result.get('longitude')
            )
            businesses.append(business)
        
        # Export results
        filename = clean_filename(f"{business_type}_{location}_{len(businesses)}_results")
        from exporter import DataExporter
        
        exporter = DataExporter()
        output_file = exporter.export_data(businesses, filename, output_format)
        
        click.echo(f"✅ Scraped {len(businesses)} businesses")
        click.echo(f"📄 Results saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Scraping failed: {e}")
        logger.error(f"Scraping error: {e}", exc_info=True)

@cli.command('generate-leads')
@click.argument('business_type')
@click.option('--location', required=True, help='Location to search')
@click.option('--max-results', default=25, help='Maximum number of leads to generate')
@click.option('--campaign-name', help='Campaign name for email outreach')
@click.option('--from-email', help='From email for campaign')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def generate_leads(business_type, location, max_results, campaign_name, from_email, verbose):
    """Complete lead generation pipeline with AI research and personalization."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)
    
    click.echo(f"🚀 Starting lead generation pipeline...")
    click.echo(f"Business type: {business_type}")
    click.echo(f"Location: {location}")
    click.echo(f"Max results: {max_results}")
    
    try:
        # Initialize pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Run complete pipeline
        results = asyncio.run(
            orchestrator.run_complete_pipeline(
                business_type=business_type,
                location=location,
                max_results=max_results,
                campaign_name=campaign_name,
                from_email=from_email
            )
        )
        
        click.echo(f"\n✅ Pipeline completed successfully!")
        click.echo(f"📊 Campaign ID: {results.get('campaign_id')}")
        click.echo(f"📊 Total leads: {results.get('total_leads', 0)}")
        click.echo(f"📊 Validated leads: {results.get('validated_leads', 0)}")
        click.echo(f"📊 Enriched leads: {results.get('enriched_leads', 0)}")
        
        if results.get('csv_export'):
            click.echo(f"📄 Results exported to: {results['csv_export']}")
        
    except Exception as e:
        click.echo(f"❌ Pipeline failed: {e}")
        logger.error(f"Pipeline error: {e}", exc_info=True)

@cli.command('validate-leads')
@click.option('--input-file', required=True, help='CSV file with leads to validate')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def validate_leads(input_file, verbose):
    """Validate existing leads."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    
    try:
        import pandas as pd
        from leads.lead_validator import LeadValidator
        
        click.echo(f"🔍 Validating leads from {input_file}")
        
        # Load leads
        df = pd.read_csv(input_file)
        click.echo(f"📊 Loaded {len(df)} leads")
        
        # Validate
        validator = LeadValidator()
        validated_results = asyncio.run(validator.validate_leads_batch(df.to_dict('records')))
        
        # Save results
        output_file = input_file.replace('.csv', '_validated.csv')
        pd.DataFrame(validated_results).to_csv(output_file, index=False)
        
        click.echo(f"✅ Validation completed")
        click.echo(f"📄 Results saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        logger.error(f"Validation error: {e}", exc_info=True)

@cli.command('setup-pipeline')
@click.option('--check-apis', is_flag=True, help='Check API configurations')
def setup_pipeline(check_apis):
    """Setup pipeline configuration."""
    try:
        from leads.pipeline_orchestrator import PipelineOrchestrator
        
        if check_apis:
            click.echo("🔧 Checking API configurations...")
            
            # Check environment variables
            required_vars = [
                'GOOGLE_PLACES_API_KEY',
                'PERPLEXITY_API_KEY', 
                'ANTHROPIC_API_KEY'
            ]
            
            optional_vars = [
                'INSTANTLY_API_KEY',
                'INSTANTLY_FROM_EMAIL'
            ]
            
            for var in required_vars:
                if os.getenv(var):
                    click.echo(f"✅ {var} configured")
                else:
                    click.echo(f"❌ {var} missing (required)")
            
            for var in optional_vars:
                if os.getenv(var):
                    click.echo(f"✅ {var} configured")
                else:
                    click.echo(f"⚠️  {var} missing (optional for email campaigns)")
            
            click.echo("\n💡 Add missing variables to .env file or environment")
        else:
            click.echo("🔧 Pipeline setup completed")
            click.echo("💡 Use --check-apis to verify API configurations")
            
    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")

@cli.command()
def templates():
    """List available message templates."""
    try:
        from leads.message_personalizer import MessagePersonalizer
        
        personalizer = MessagePersonalizer()
        templates = personalizer.get_available_templates()
        
        click.echo("📝 Available message templates:")
        for template_name in templates:
            click.echo(f"   • {template_name}")
            
    except Exception as e:
        click.echo(f"❌ Failed to load templates: {e}")

if __name__ == '__main__':
    cli()
