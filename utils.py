"""
Utility functions for the lead generation system.
"""

import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from functools import wraps

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Unicode normalization
    text = unicodedata.normalize('NFKD', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    return text

def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage."""
    if not filename:
        return "output"
    
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('._')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename or "output"

def clean_phone(phone: str) -> str:
    """Clean and format phone numbers."""
    if not phone:
        return ""
    
    # Remove all non-digit characters except + and parentheses
    cleaned = re.sub(r'[^\d+\(\)\-\s]', '', phone)
    
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned.strip())
    
    return cleaned

def clean_email(email: str) -> str:
    """Clean and validate email addresses."""
    if not email:
        return ""
    
    email = email.strip().lower()
    
    # Basic email pattern
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if email_pattern.match(email):
        return email
    
    return ""

def clean_url(url: str) -> str:
    """Clean and validate URLs."""
    if not url:
        return ""
    
    url = url.strip()
    
    # Remove common prefixes that might be concatenated
    url = re.sub(r'^(tel:|mailto:|javascript:)', '', url, flags=re.IGNORECASE)
    
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

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return ""
    
    # Clean URL first
    url = clean_url(url)
    if not url:
        return ""
    
    # Extract domain
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if domain_match:
        return domain_match.group(1)
    
    return ""

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support."""
    if not isinstance(data, dict):
        return default
    
    # Support nested keys like "location.lat"
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current

def batch_process(items: List[Any], batch_size: int = 10):
    """Generator to process items in batches."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    time.sleep(delay)
            
            # Re-raise the last exception
            raise last_exception
        
        return wrapper
    return decorator

async def async_retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Async decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    await asyncio.sleep(delay)
            
            # Re-raise the last exception
            raise last_exception
        
        return wrapper
    return decorator

class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self.current = min(self.current, self.total)  # Don't exceed total
        
        if self.current % 10 == 0 or self.current == self.total:
            self._log_progress()
    
    def _log_progress(self):
        """Log current progress."""
        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        if self.current > 0:
            estimated_total = elapsed * (self.total / self.current)
            remaining = estimated_total - elapsed
            
            self.logger.info(
                f"{self.description}: {self.current}/{self.total} "
                f"({percentage:.1f}%) - "
                f"Elapsed: {format_duration(elapsed)}, "
                f"ETA: {format_duration(remaining)}"
            )
        else:
            self.logger.info(f"{self.description}: Starting...")
    
    def finish(self):
        """Mark as finished."""
        self.current = self.total
        elapsed = time.time() - self.start_time
        self.logger.info(
            f"{self.description}: Completed {self.total} items "
            f"in {format_duration(elapsed)}"
        )

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.last_call = 0.0
    
    async def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_call
        
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_call = time.time()

def validate_config_dict(config: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """Validate configuration dictionary has required keys."""
    errors = []
    
    for key in required_keys:
        if key not in config or not config[key]:
            errors.append(f"Missing required configuration: {key}")
    
    return errors

def sanitize_for_csv(text: str) -> str:
    """Sanitize text for CSV export."""
    if not text:
        return ""
    
    # Remove or escape problematic characters for CSV
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Escape quotes
    if '"' in text:
        text = text.replace('"', '""')
    
    return text

def create_unique_filename(base_path: str, extension: str = ".csv") -> str:
    """Create unique filename by adding timestamp if file exists."""
    base_path = Path(base_path)
    
    if not base_path.suffix:
        base_path = base_path.with_suffix(extension)
    
    if not base_path.exists():
        return str(base_path)
    
    # Add timestamp to make unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    
    unique_path = parent / f"{stem}_{timestamp}{suffix}"
    return str(unique_path)

# Export utility functions
__all__ = [
    'setup_logging',
    'clean_text',
    'clean_filename', 
    'clean_phone',
    'clean_email',
    'clean_url',
    'extract_domain',
    'format_duration',
    'format_timestamp',
    'safe_get',
    'batch_process',
    'retry_with_backoff',
    'async_retry_with_backoff',
    'ProgressTracker',
    'RateLimiter',
    'validate_config_dict',
    'sanitize_for_csv',
    'create_unique_filename'
]
