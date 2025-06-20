"""
Lead validation system for email, phone, and company validation.
"""

import asyncio
import logging
import re
import socket
from typing import List, Dict, Any, Optional, Tuple
import requests
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)

class LeadValidator:
    """Comprehensive lead validation system."""
    
    def __init__(self, timeout: int = 5, max_workers: int = 10):
        """Initialize validator with configuration."""
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Configure session with reasonable defaults
        self.session.headers.update({
            'User-Agent': 'Lead Validator 1.0 (Business Data Verification)'
        })
    
    async def validate_leads_batch(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of leads asynchronously."""
        if not leads:
            return []
        
        logger.info(f"Starting validation of {len(leads)} leads")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_workers)
        
        # Create validation tasks
        tasks = []
        for lead in leads:
            task = self._validate_single_lead_async(semaphore, lead)
            tasks.append(task)
        
        # Execute all validations
        validated_leads = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        results = []
        for i, result in enumerate(validated_leads):
            if isinstance(result, Exception):
                logger.error(f"Validation failed for lead {i}: {result}")
                # Return original lead with validation flags set to False
                lead = leads[i].copy()
                lead.update({
                    'email_valid': False,
                    'phone_valid': False,
                    'company_valid': False,
                    'validation_error': str(result)
                })
                results.append(lead)
            else:
                results.append(result)
        
        # Log summary
        total_leads = len(results)
        valid_emails = sum(1 for lead in results if lead.get('email_valid', False))
        valid_phones = sum(1 for lead in results if lead.get('phone_valid', False))
        valid_companies = sum(1 for lead in results if lead.get('company_valid', False))
        
        logger.info(f"Validation completed: {valid_emails}/{total_leads} valid emails, "
                   f"{valid_phones}/{total_leads} valid phones, "
                   f"{valid_companies}/{total_leads} valid companies")
        
        return results
    
    async def _validate_single_lead_async(self, semaphore: asyncio.Semaphore, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single lead asynchronously."""
        async with semaphore:
            # Add small delay to avoid overwhelming services
            await asyncio.sleep(0.1)
            
            # Create a copy to avoid modifying original
            validated_lead = lead.copy()
            
            # Validate email
            email_valid, email_details = self._validate_email(lead.get('email', ''))
            validated_lead['email_valid'] = email_valid
            if email_details:
                validated_lead['email_validation_details'] = email_details
            
            # Validate phone
            phone_valid, phone_details = self._validate_phone(lead.get('phone', ''), lead.get('country', 'US'))
            validated_lead['phone_valid'] = phone_valid
            if phone_details:
                validated_lead['phone_validation_details'] = phone_details
            
            # Validate company/website
            company_valid, company_details = await self._validate_company_async(
                lead.get('website', ''), 
                lead.get('name', '')
            )
            validated_lead['company_valid'] = company_valid
            if company_details:
                validated_lead['company_validation_details'] = company_details
            
            # Set overall validation status
            validated_lead['is_validated'] = True
            validated_lead['validation_score'] = sum([email_valid, phone_valid, company_valid])
            
            return validated_lead
    
    def _validate_email(self, email: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate email address."""
        if not email or not isinstance(email, str):
            return False, None
        
        email = email.strip().lower()
        
        # Basic format check first
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return False, {'error': 'Invalid email format'}
        
        try:
            # Use email-validator library for comprehensive validation
            validation_result = validate_email(email)
            
            # Extract details
            details = {
                'normalized_email': validation_result.email,
                'local_part': validation_result.local,
                'domain': validation_result.domain,
                'ascii_email': validation_result.ascii_email,
                'ascii_local': validation_result.ascii_local,
                'ascii_domain': validation_result.ascii_domain
            }
            
            # Additional domain checks
            domain_valid = self._check_domain_exists(validation_result.domain)
            details['domain_exists'] = domain_valid
            
            return True, details
            
        except EmailNotValidError as e:
            return False, {'error': str(e)}
        except Exception as e:
            logger.warning(f"Email validation error for {email}: {e}")
            return False, {'error': 'Validation service error'}
    
    def _validate_phone(self, phone: str, country_code: str = 'US') -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate phone number."""
        if not phone or not isinstance(phone, str):
            return False, None
        
        phone = phone.strip()
        
        try:
            # Parse phone number with phonenumbers library
            parsed_number = phonenumbers.parse(phone, country_code)
            
            # Check if number is valid
            is_valid = phonenumbers.is_valid_number(parsed_number)
            is_possible = phonenumbers.is_possible_number(parsed_number)
            
            if is_valid:
                details = {
                    'international_format': phonenumbers.format_number(
                        parsed_number, 
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    ),
                    'national_format': phonenumbers.format_number(
                        parsed_number, 
                        phonenumbers.PhoneNumberFormat.NATIONAL
                    ),
                    'e164_format': phonenumbers.format_number(
                        parsed_number, 
                        phonenumbers.PhoneNumberFormat.E164
                    ),
                    'country_code': parsed_number.country_code,
                    'national_number': parsed_number.national_number,
                    'number_type': self._get_phone_type(parsed_number),
                    'is_possible': is_possible
                }
                return True, details
            else:
                return False, {
                    'error': 'Invalid phone number',
                    'is_possible': is_possible
                }
                
        except NumberParseException as e:
            return False, {'error': f'Parse error: {e}'}
        except Exception as e:
            logger.warning(f"Phone validation error for {phone}: {e}")
            return False, {'error': 'Validation service error'}
    
    def _get_phone_type(self, parsed_number) -> str:
        """Get phone number type description."""
        number_type = phonenumbers.number_type(parsed_number)
        
        type_mapping = {
            phonenumbers.PhoneNumberType.FIXED_LINE: 'Fixed Line',
            phonenumbers.PhoneNumberType.MOBILE: 'Mobile',
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: 'Fixed Line or Mobile',
            phonenumbers.PhoneNumberType.TOLL_FREE: 'Toll Free',
            phonenumbers.PhoneNumberType.PREMIUM_RATE: 'Premium Rate',
            phonenumbers.PhoneNumberType.SHARED_COST: 'Shared Cost',
            phonenumbers.PhoneNumberType.VOIP: 'VoIP',
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: 'Personal Number',
            phonenumbers.PhoneNumberType.PAGER: 'Pager',
            phonenumbers.PhoneNumberType.UAN: 'UAN',
            phonenumbers.PhoneNumberType.VOICEMAIL: 'Voicemail',
        }
        
        return type_mapping.get(number_type, 'Unknown')
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if domain exists via DNS lookup."""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
        except Exception:
            return False
    
    async def _validate_company_async(self, website: str, company_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate company by checking website accessibility."""
        if not website and not company_name:
            return False, None
        
        details = {}
        
        # Website validation
        if website:
            website_valid, website_details = await self._check_website_async(website)
            details.update(website_details or {})
            
            if website_valid:
                return True, details
        
        # If no website or website invalid, company is considered partially valid if it has a name
        if company_name and len(company_name.strip()) > 2:
            details['has_company_name'] = True
            details['company_name_length'] = len(company_name.strip())
            return True, details
        
        return False, details
    
    async def _check_website_async(self, website: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if website is accessible."""
        if not website:
            return False, None
        
        # Clean and normalize URL
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            # Use asyncio to run the blocking request in a thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.get(website, timeout=self.timeout, allow_redirects=True)
            )
            
            details = {
                'status_code': response.status_code,
                'final_url': response.url,
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', ''),
                'response_time': response.elapsed.total_seconds()
            }
            
            # Consider successful if status is 200-299 or 300-399 (redirects)
            is_valid = 200 <= response.status_code < 400
            
            if is_valid:
                # Try to extract some basic info
                try:
                    content = response.text[:1000]  # Only check first 1KB
                    if '<title>' in content.lower():
                        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                        if title_match:
                            details['page_title'] = title_match.group(1).strip()[:100]
                except:
                    pass  # Don't fail validation if we can't parse title
            
            return is_valid, details
            
        except requests.exceptions.Timeout:
            return False, {'error': 'Website timeout'}
        except requests.exceptions.ConnectionError:
            return False, {'error': 'Connection failed'}
        except requests.exceptions.RequestException as e:
            return False, {'error': f'Request error: {str(e)[:100]}'}
        except Exception as e:
            logger.warning(f"Website validation error for {website}: {e}")
            return False, {'error': 'Validation service error'}
    
    def validate_single_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous validation for a single lead."""
        # Run async validation in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            semaphore = asyncio.Semaphore(1)
            result = loop.run_until_complete(self._validate_single_lead_async(semaphore, lead))
            return result
        finally:
            loop.close()
    
    def get_validation_summary(self, validated_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get validation summary statistics."""
        if not validated_leads:
            return {}
        
        total = len(validated_leads)
        
        email_stats = {
            'total_with_email': sum(1 for lead in validated_leads if lead.get('email')),
            'valid_emails': sum(1 for lead in validated_leads if lead.get('email_valid', False)),
            'invalid_emails': sum(1 for lead in validated_leads if lead.get('email') and not lead.get('email_valid', False))
        }
        
        phone_stats = {
            'total_with_phone': sum(1 for lead in validated_leads if lead.get('phone')),
            'valid_phones': sum(1 for lead in validated_leads if lead.get('phone_valid', False)),
            'invalid_phones': sum(1 for lead in validated_leads if lead.get('phone') and not lead.get('phone_valid', False))
        }
        
        company_stats = {
            'total_with_website': sum(1 for lead in validated_leads if lead.get('website')),
            'valid_companies': sum(1 for lead in validated_leads if lead.get('company_valid', False)),
            'invalid_companies': sum(1 for lead in validated_leads if not lead.get('company_valid', False))
        }
        
        # Overall quality score
        total_validations = sum(lead.get('validation_score', 0) for lead in validated_leads)
        max_possible = total * 3  # 3 validation types per lead
        quality_score = (total_validations / max_possible * 100) if max_possible > 0 else 0
        
        return {
            'total_leads': total,
            'email_validation': email_stats,
            'phone_validation': phone_stats,
            'company_validation': company_stats,
            'overall_quality_score': round(quality_score, 2)
        }

# Export the class
__all__ = ['LeadValidator']
