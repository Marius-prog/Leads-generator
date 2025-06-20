"""
Data models for the lead generation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import re
from pydantic import BaseModel, validator, Field
import phonenumbers

@dataclass
class Business:
    """Core business data model."""
    name: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    email: str = ""
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    
    def __post_init__(self):
        """Clean and validate data after initialization."""
        self.name = self._clean_text(self.name)
        self.address = self._clean_text(self.address)
        self.phone = self._clean_phone(self.phone)
        self.website = self._clean_url(self.website)
        self.email = self._clean_email(self.email)
        self.category = self._clean_text(self.category)
        
        # Parse address components
        if self.address and not (self.city or self.state):
            self._parse_address()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text fields."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        return text
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and validate phone numbers."""
        if not phone:
            return ""
        
        # Remove common formatting
        cleaned = re.sub(r'[^\d+\-\(\)\s]', '', phone)
        cleaned = cleaned.strip()
        
        # Try to parse with phonenumbers library
        try:
            parsed = phonenumbers.parse(cleaned, "US")  # Default to US
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except:
            pass
        
        return cleaned
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URLs."""
        if not url:
            return ""
        
        url = url.strip()
        
        # Add protocol if missing
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if url_pattern.match(url):
            return url
        
        return ""
    
    def _clean_email(self, email: str) -> str:
        """Clean and validate email addresses."""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if email_pattern.match(email):
            return email
        
        return ""
    
    def _parse_address(self):
        """Parse address components from full address."""
        if not self.address:
            return
        
        # Simple address parsing (can be enhanced)
        parts = [part.strip() for part in self.address.split(',')]
        
        if len(parts) >= 2:
            # Last part might be state + zip
            last_part = parts[-1].strip()
            state_zip_match = re.match(r'^([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$', last_part)
            
            if state_zip_match:
                self.state = state_zip_match.group(1)
                self.postal_code = state_zip_match.group(2)
                
                if len(parts) >= 3:
                    self.city = parts[-2].strip()
            else:
                # Assume last part is city
                self.city = last_part
                
                if len(parts) >= 3:
                    # Check if second to last has state info
                    state_part = parts[-2].strip()
                    if len(state_part) == 2 and state_part.isupper():
                        self.state = state_part

@dataclass
class ScrapingResult:
    """Results from a scraping operation."""
    businesses: List[Business] = field(default_factory=list)
    total_found: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    execution_time: float = 0.0
    search_query: str = ""
    search_location: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_found == 0:
            return 0.0
        return (self.successful_extractions / self.total_found) * 100


# Pydantic models for API validation
class BusinessRequest(BaseModel):
    """Request model for business search."""
    business_type: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    max_results: int = Field(default=25, ge=1, le=100)
    extract_emails: bool = Field(default=False)

class LeadGenerationRequest(BaseModel):
    """Request model for lead generation pipeline."""
    business_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    leads_count: int = Field(default=25, ge=1, le=100)
    campaign_name: Optional[str] = Field(None, max_length=100)
    from_email: Optional[str] = None
    include_research: bool = Field(default=True)
    include_personalization: bool = Field(default=True)
    
    @validator('from_email')
    def validate_email(cls, v):
        if v is not None:
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(v):
                raise ValueError('Invalid email format')
        return v

class PipelineStatus(BaseModel):
    """Pipeline execution status."""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int = Field(ge=0, le=100)
    current_step: Optional[str] = None
    total_leads: Optional[int] = None
    processed_leads: Optional[int] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ApiResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class ConfigStatus(BaseModel):
    """Configuration status model."""
    google_places_api: bool = False
    perplexity_api: bool = False
    anthropic_api: bool = False
    instantly_api: bool = False
    database: bool = False
    missing_configs: List[str] = Field(default_factory=list)
    
    @property
    def ready_for_scraping(self) -> bool:
        """Check if ready for basic scraping."""
        return self.google_places_api and self.database
    
    @property
    def ready_for_pipeline(self) -> bool:
        """Check if ready for full pipeline."""
        return (self.google_places_api and 
                self.perplexity_api and 
                self.anthropic_api and 
                self.database)
    
    @property
    def ready_for_campaigns(self) -> bool:
        """Check if ready for email campaigns."""
        return self.ready_for_pipeline and self.instantly_api


# Export all models
__all__ = [
    'Business',
    'ScrapingResult', 
    'BusinessRequest',
    'LeadGenerationRequest',
    'PipelineStatus',
    'ApiResponse',
    'ConfigStatus'
]
