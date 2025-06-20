"""
Configuration management for the lead generation system.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

@dataclass
class ScrapingConfig:
    """Configuration for Google Maps scraping."""
    # Google Places API settings
    google_places_api_key: str = ""
    
    # Search settings
    max_results: int = 50
    search_radius: int = 50000  # 50km in meters
    language: str = "en"
    region: str = "us"
    
    # Browser settings (for fallback scraping)
    headless: bool = True
    implicit_wait: int = 10
    page_load_timeout: int = 30
    
    # Email extraction settings
    extract_emails: bool = False
    email_timeout: int = 5
    max_email_pages: int = 3
    
    # Output settings
    output_format: str = "csv"  # csv, json, excel
    output_directory: str = "data"
    include_coordinates: bool = True
    include_website_data: bool = False
    
    # Rate limiting
    request_delay: float = 0.1  # Seconds between requests
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "scraper.log"
    verbose: bool = False
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        # Override with environment variables if available
        self.google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY", self.google_places_api_key)
        
        # Create output directory if it doesn't exist
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_file(cls, config_file: str) -> 'ScrapingConfig':
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults")
            return cls()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            return cls()
    
    def to_file(self, config_file: str):
        """Save configuration to JSON file."""
        config_data = {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.google_places_api_key:
            errors.append("Google Places API key is required")
        
        if self.max_results < 1 or self.max_results > 1000:
            errors.append("max_results must be between 1 and 1000")
        
        if self.search_radius < 1000 or self.search_radius > 50000:
            errors.append("search_radius must be between 1000 and 50000 meters")
        
        if self.output_format not in ["csv", "json", "excel"]:
            errors.append("output_format must be csv, json, or excel")
        
        return errors

@dataclass
class LeadPipelineConfig:
    """Configuration for the complete lead generation pipeline."""
    # API Keys
    google_places_api_key: str = ""
    perplexity_api_key: str = ""
    anthropic_api_key: str = ""
    instantly_api_key: str = ""
    
    # LinkedIn settings (now inference-based)
    linkedin_email: str = ""
    linkedin_password: str = ""
    use_linkedin_inference: bool = True  # Use inference instead of scraping
    
    # Pipeline settings
    max_leads: int = 100
    enable_validation: bool = True
    enable_linkedin_enrichment: bool = True
    enable_research: bool = True
    enable_personalization: bool = True
    enable_campaign_creation: bool = False
    
    # Validation settings
    validate_emails: bool = True
    validate_phones: bool = True
    validate_companies: bool = True
    validation_timeout: int = 5
    validation_workers: int = 10
    
    # Research settings
    research_timeout: int = 30
    research_workers: int = 4
    include_competitor_analysis: bool = False
    include_financial_data: bool = False
    
    # Personalization settings
    personalization_timeout: int = 20
    personalization_workers: int = 3
    message_template: str = "professional"
    include_company_insights: bool = True
    
    # Campaign settings
    instantly_from_email: str = ""
    default_campaign_name: str = "Lead Generation Campaign"
    campaign_tags: List[str] = field(default_factory=list)
    
    # Database settings
    database_file: str = "leads.db"
    backup_database: bool = True
    
    # Rate limiting and performance
    google_places_delay: float = 0.1
    perplexity_delay: float = 1.0
    anthropic_delay: float = 1.0
    validation_delay: float = 0.1
    
    # Logging and monitoring
    log_level: str = "INFO"
    log_file: str = "pipeline.log"
    enable_progress_tracking: bool = True
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        # API Keys from environment
        self.google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY", self.google_places_api_key)
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", self.perplexity_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.instantly_api_key = os.getenv("INSTANTLY_API_KEY", self.instantly_api_key)
        
        # Email settings
        self.instantly_from_email = os.getenv("INSTANTLY_FROM_EMAIL", self.instantly_from_email)
        self.linkedin_email = os.getenv("LINKEDIN_EMAIL", self.linkedin_email)
        self.linkedin_password = os.getenv("LINKEDIN_PASSWORD", self.linkedin_password)
        
        # Enable campaign creation only if API key is available
        if self.instantly_api_key and self.instantly_from_email:
            self.enable_campaign_creation = True
    
    @classmethod
    def from_file(cls, config_file: str) -> 'LeadPipelineConfig':
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults")
            return cls()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            return cls()
    
    def to_file(self, config_file: str):
        """Save configuration to JSON file (excluding sensitive data)."""
        config_data = {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') and 'password' not in key.lower() and 'api_key' not in key.lower()
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Required API keys
        if not self.google_places_api_key:
            errors.append("Google Places API key is required")
        
        if self.enable_research and not self.perplexity_api_key:
            errors.append("Perplexity API key is required for research")
        
        if self.enable_personalization and not self.anthropic_api_key:
            errors.append("Anthropic API key is required for personalization")
        
        if self.enable_campaign_creation:
            if not self.instantly_api_key:
                errors.append("Instantly API key is required for campaign creation")
            if not self.instantly_from_email:
                errors.append("From email is required for campaign creation")
        
        # Validate settings ranges
        if self.max_leads < 1 or self.max_leads > 1000:
            errors.append("max_leads must be between 1 and 1000")
        
        if self.validation_workers < 1 or self.validation_workers > 20:
            errors.append("validation_workers must be between 1 and 20")
        
        if self.research_workers < 1 or self.research_workers > 10:
            errors.append("research_workers must be between 1 and 10")
        
        if self.personalization_workers < 1 or self.personalization_workers > 5:
            errors.append("personalization_workers must be between 1 and 5")
        
        return errors
    
    def get_api_status(self) -> Dict[str, bool]:
        """Get status of API configurations."""
        return {
            "google_places": bool(self.google_places_api_key),
            "perplexity": bool(self.perplexity_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "instantly": bool(self.instantly_api_key),
            "database": True,  # SQLite is always available
        }
    
    def get_missing_configs(self) -> List[str]:
        """Get list of missing required configurations."""
        missing = []
        
        if not self.google_places_api_key:
            missing.append("GOOGLE_PLACES_API_KEY")
        
        if self.enable_research and not self.perplexity_api_key:
            missing.append("PERPLEXITY_API_KEY")
        
        if self.enable_personalization and not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        
        if self.enable_campaign_creation and not self.instantly_api_key:
            missing.append("INSTANTLY_API_KEY")
        
        if self.enable_campaign_creation and not self.instantly_from_email:
            missing.append("INSTANTLY_FROM_EMAIL")
        
        return missing

# Default configurations
DEFAULT_SCRAPING_CONFIG = ScrapingConfig()
DEFAULT_PIPELINE_CONFIG = LeadPipelineConfig()

# Load from .env file if available
def load_env_file():
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed

# Load environment on import
load_env_file()
