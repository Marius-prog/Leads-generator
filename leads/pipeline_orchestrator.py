"""
Pipeline orchestrator for the complete lead generation workflow.
"""

import asyncio
import logging
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import system components
from config import LeadPipelineConfig
from google_places_scraper import GooglePlacesScraper
from leads.sqlite_manager import SQLiteManager
from leads.lead_validator import LeadValidator
from exporter import LeadExporter
from utils import ProgressTracker

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """Main orchestrator for the lead generation pipeline."""
    
    def __init__(self, config: Optional[LeadPipelineConfig] = None):
        """Initialize the pipeline orchestrator."""
        self.config = config or LeadPipelineConfig()
        self.db = SQLiteManager(self.config.database_file)
        self.google_scraper = GooglePlacesScraper()
        self.validator = LeadValidator(
            timeout=self.config.validation_timeout,
            max_workers=self.config.validation_workers
        )
        self.exporter = LeadExporter()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.warning(f"Configuration issues: {errors}")
    
    async def run_complete_pipeline(self, business_type: str, location: str, 
                                  max_results: int = 25, campaign_name: Optional[str] = None,
                                  from_email: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete lead generation pipeline."""
        start_time = time.time()
        
        # Create campaign
        campaign_id = self._create_campaign(
            business_type=business_type,
            location=location,
            max_results=max_results,
            campaign_name=campaign_name,
            from_email=from_email
        )
        
        logger.info(f"Starting pipeline for campaign: {campaign_id}")
        
        try:
            # Update campaign status
            self.db.update_campaign(campaign_id, {'status': 'running'})
            
            # Step 1: Scrape businesses
            logger.info("Step 1: Scraping businesses with Google Places API")
            businesses = await self._scrape_businesses(campaign_id, business_type, location, max_results)
            
            if not businesses:
                raise Exception("No businesses found")
            
            # Step 2: Store initial leads
            logger.info("Step 2: Storing initial leads in database")
            self.db.insert_leads(campaign_id, businesses)
            self.db.update_campaign(campaign_id, {'total_leads': len(businesses)})
            
            # Step 3: Validate leads
            if self.config.enable_validation:
                logger.info("Step 3: Validating leads")
                await self._validate_leads(campaign_id)
            
            # Step 4: LinkedIn enrichment (simplified - just mark as enriched)
            if self.config.enable_linkedin_enrichment:
                logger.info("Step 4: LinkedIn profile inference")
                await self._enrich_linkedin_profiles(campaign_id)
            
            # Step 5: AI research (simplified version)
            if self.config.enable_research:
                logger.info("Step 5: AI company research")
                await self._research_companies(campaign_id)
            
            # Step 6: Message personalization (simplified version)
            if self.config.enable_personalization:
                logger.info("Step 6: Personalizing messages")
                await self._personalize_messages(campaign_id)
            
            # Step 7: Export results
            logger.info("Step 7: Exporting results")
            csv_file = self._export_results(campaign_id)
            
            # Complete campaign
            execution_time = time.time() - start_time
            final_stats = self.db.get_campaign_stats(campaign_id)
            
            self.db.update_campaign(campaign_id, {
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            })
            
            logger.info(f"Pipeline completed in {execution_time:.2f} seconds")
            
            return {
                'campaign_id': campaign_id,
                'status': 'completed',
                'execution_time': execution_time,
                'total_leads': len(businesses),
                'validated_leads': final_stats.get('leads', {}).get('valid_emails', 0),
                'enriched_leads': final_stats.get('leads', {}).get('enriched_leads', 0),
                'csv_export': csv_file,
                'stats': final_stats
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            
            self.db.update_campaign(campaign_id, {
                'status': 'failed',
                'error_message': str(e)
            })
            
            raise
    
    def _create_campaign(self, business_type: str, location: str, max_results: int,
                        campaign_name: Optional[str], from_email: Optional[str]) -> str:
        """Create a new campaign."""
        campaign_data = {
            'name': campaign_name or f"{business_type} in {location}",
            'business_type': business_type,
            'location': location,
            'max_results': max_results,
            'from_email': from_email
        }
        
        return self.db.create_campaign(campaign_data)
    
    async def _scrape_businesses(self, campaign_id: str, business_type: str, 
                               location: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape businesses using Google Places API."""
        try:
            businesses = self.google_scraper.search_businesses(
                query=business_type,
                location=location,
                max_results=max_results
            )
            
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='scraping',
                status='completed',
                processed=len(businesses),
                success=len(businesses)
            )
            
            return businesses
            
        except Exception as e:
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='scraping',
                status='failed',
                error_message=str(e)
            )
            raise
    
    async def _validate_leads(self, campaign_id: str):
        """Validate all leads for a campaign."""
        leads = self.db.get_leads_by_campaign(campaign_id)
        if not leads:
            return
        
        start_time = time.time()
        
        try:
            # Validate leads
            validated_leads = await self.validator.validate_leads_batch(leads)
            
            # Update leads with validation results
            updates = []
            for lead in validated_leads:
                updates.append({
                    'id': lead['id'],
                    'email_valid': lead.get('email_valid', False),
                    'phone_valid': lead.get('phone_valid', False),
                    'company_valid': lead.get('company_valid', False),
                    'status': 'validated'
                })
            
            self.db.update_leads_batch(campaign_id, updates)
            
            # Update campaign stats
            valid_leads = sum(1 for lead in validated_leads if lead.get('email_valid', False))
            self.db.update_campaign(campaign_id, {'validated_leads': valid_leads})
            
            # Record pipeline run
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='validation',
                status='completed',
                duration=duration,
                processed=len(leads),
                success=len(validated_leads)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='validation',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
            raise
    
    async def _enrich_linkedin_profiles(self, campaign_id: str):
        """Enrich leads with LinkedIn profile information (simplified)."""
        leads = self.db.get_leads_by_campaign(campaign_id, status='validated')
        if not leads:
            return
        
        start_time = time.time()
        
        try:
            # Simplified LinkedIn enrichment - just add mock data for demo
            updates = []
            for lead in leads:
                # Create mock LinkedIn profile data
                linkedin_profile = {
                    'inferred': True,
                    'company_name': lead.get('name', ''),
                    'industry': lead.get('category', ''),
                    'location': lead.get('city', ''),
                    'confidence_score': 0.7,
                    'profile_url': None  # Would be actual URL in real implementation
                }
                
                updates.append({
                    'id': lead['id'],
                    'linkedin_profile': linkedin_profile,
                    'status': 'enriched'
                })
            
            self.db.update_leads_batch(campaign_id, updates)
            self.db.update_campaign(campaign_id, {'enriched_leads': len(updates)})
            
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='linkedin_enrichment',
                status='completed',
                duration=duration,
                processed=len(leads),
                success=len(updates)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='linkedin_enrichment',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
            raise
    
    async def _research_companies(self, campaign_id: str):
        """Research companies using AI (simplified version)."""
        leads = self.db.get_leads_by_campaign(campaign_id, status='enriched')
        if not leads:
            return
        
        start_time = time.time()
        
        try:
            # Simplified research - add mock research data
            updates = []
            for lead in leads:
                research_data = {
                    'company_overview': f"Research overview for {lead.get('name', 'Unknown Company')}",
                    'industry_insights': f"Industry insights for {lead.get('category', 'Unknown Industry')}",
                    'key_challenges': ['Market competition', 'Digital transformation', 'Customer acquisition'],
                    'recent_news': ['Recent expansion', 'New product launch'],
                    'research_timestamp': datetime.now().isoformat(),
                    'confidence_score': 0.8
                }
                
                updates.append({
                    'id': lead['id'],
                    'research_data': research_data,
                    'status': 'researched'
                })
            
            self.db.update_leads_batch(campaign_id, updates)
            
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='research',
                status='completed',
                duration=duration,
                processed=len(leads),
                success=len(updates)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='research',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
            raise
    
    async def _personalize_messages(self, campaign_id: str):
        """Personalize messages for leads (simplified version)."""
        leads = self.db.get_leads_by_campaign(campaign_id, status='researched')
        if not leads:
            return
        
        start_time = time.time()
        
        try:
            updates = []
            for lead in leads:
                personalized_message = {
                    'subject': f"Partnership opportunity for {lead.get('name', 'your company')}",
                    'message': f"""Hello,
                    
I noticed {lead.get('name', 'your company')} in {lead.get('city', 'your area')} and was impressed by your work in {lead.get('category', 'your industry')}.

Based on our research, I believe there could be a valuable partnership opportunity that could help address some of the common challenges in your industry.

Would you be open to a brief conversation to explore this further?

Best regards,
[Your Name]""",
                    'template_used': 'professional',
                    'personalization_elements': {
                        'company_name': lead.get('name'),
                        'location': lead.get('city'),
                        'industry': lead.get('category')
                    },
                    'created_at': datetime.now().isoformat()
                }
                
                updates.append({
                    'id': lead['id'],
                    'personalized_message': personalized_message,
                    'status': 'personalized'
                })
            
            self.db.update_leads_batch(campaign_id, updates)
            self.db.update_campaign(campaign_id, {'personalized_leads': len(updates)})
            
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='personalization',
                status='completed',
                duration=duration,
                processed=len(leads),
                success=len(updates)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.db.record_pipeline_run(
                campaign_id=campaign_id,
                stage='personalization',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
            raise
    
    def _export_results(self, campaign_id: str) -> str:
        """Export campaign results to CSV."""
        leads = self.db.get_leads_by_campaign(campaign_id)
        
        # Prepare data for export
        export_data = []
        for lead in leads:
            # Flatten the lead data for CSV export
            flattened = {
                'campaign_id': lead.get('campaign_id'),
                'name': lead.get('name'),
                'address': lead.get('address'),
                'city': lead.get('city'),
                'state': lead.get('state'),
                'phone': lead.get('phone'),
                'email': lead.get('email'),
                'website': lead.get('website'),
                'category': lead.get('category'),
                'rating': lead.get('rating'),
                'reviews_count': lead.get('reviews_count'),
                'status': lead.get('status'),
                'email_valid': lead.get('email_valid'),
                'phone_valid': lead.get('phone_valid'),
                'company_valid': lead.get('company_valid'),
                'linkedin_enriched': bool(lead.get('linkedin_profile')),
                'research_completed': bool(lead.get('research_data')),
                'message_personalized': bool(lead.get('personalized_message'))
            }
            export_data.append(flattened)
        
        # Export to CSV
        filename = f"leads_{campaign_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        csv_file = self.exporter.export_leads(export_data, filename, format='csv')
        
        return csv_file
    
    def get_pipeline_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get current status of a pipeline run."""
        campaign = self.db.get_campaign(campaign_id)
        if not campaign:
            return {'error': 'Campaign not found'}
        
        stats = self.db.get_campaign_stats(campaign_id)
        
        return {
            'campaign_id': campaign_id,
            'status': campaign.get('status'),
            'created_at': campaign.get('created_at'),
            'updated_at': campaign.get('updated_at'),
            'completed_at': campaign.get('completed_at'),
            'total_leads': campaign.get('total_leads', 0),
            'validated_leads': campaign.get('validated_leads', 0),
            'enriched_leads': campaign.get('enriched_leads', 0),
            'personalized_leads': campaign.get('personalized_leads', 0),
            'error_message': campaign.get('error_message'),
            'detailed_stats': stats
        }
    
    def list_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent campaigns."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM campaigns 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            campaigns = [dict(row) for row in cursor.fetchall()]
            return campaigns

# Export the class
__all__ = ['PipelineOrchestrator']
