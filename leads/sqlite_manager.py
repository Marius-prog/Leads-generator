"""
SQLite database manager for lead generation system.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

class SQLiteManager:
    """SQLite database manager for leads."""
    
    def __init__(self, db_path: str = "leads.db"):
        """Initialize database manager."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Campaigns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    max_results INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    from_email TEXT NULL,
                    total_leads INTEGER DEFAULT 0,
                    validated_leads INTEGER DEFAULT 0,
                    enriched_leads INTEGER DEFAULT 0,
                    personalized_leads INTEGER DEFAULT 0,
                    campaign_created INTEGER DEFAULT 0,
                    error_message TEXT NULL
                )
            """)
            
            # Leads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT NOT NULL,
                    place_id TEXT NULL,
                    name TEXT NOT NULL,
                    address TEXT NULL,
                    city TEXT NULL,
                    state TEXT NULL,
                    postal_code TEXT NULL,
                    country TEXT NULL,
                    phone TEXT NULL,
                    email TEXT NULL,
                    website TEXT NULL,
                    category TEXT NULL,
                    rating REAL NULL,
                    reviews_count INTEGER NULL,
                    latitude REAL NULL,
                    longitude REAL NULL,
                    status TEXT DEFAULT 'new',
                    email_valid BOOLEAN DEFAULT 0,
                    phone_valid BOOLEAN DEFAULT 0,
                    company_valid BOOLEAN DEFAULT 0,
                    linkedin_profile JSON NULL,
                    research_data JSON NULL,
                    personalized_message JSON NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)
            
            # Pipeline runs table for tracking execution history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    duration_seconds REAL NULL,
                    processed_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_message TEXT NULL,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_campaign ON pipeline_runs(campaign_id)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign."""
        campaign_id = campaign_data.get('id') or f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO campaigns (
                    id, name, business_type, location, max_results, 
                    from_email, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                campaign_data.get('name', ''),
                campaign_data.get('business_type', ''),
                campaign_data.get('location', ''),
                campaign_data.get('max_results', 25),
                campaign_data.get('from_email'),
                'pending'
            ))
            conn.commit()
        
        logger.info(f"Created campaign: {campaign_id}")
        return campaign_id
    
    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]):
        """Update campaign with new data."""
        if not updates:
            return
        
        # Build dynamic update query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [campaign_id]
        
        # Always update timestamp
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE campaigns 
                SET {set_clause}
                WHERE id = ?
            """, values)
            conn.commit()
        
        logger.debug(f"Updated campaign {campaign_id} with: {updates}")
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def insert_leads(self, campaign_id: str, leads: List[Dict[str, Any]]):
        """Insert multiple leads for a campaign."""
        if not leads:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for lead in leads:
                conn.execute("""
                    INSERT INTO leads (
                        campaign_id, place_id, name, address, city, state, 
                        postal_code, country, phone, email, website, category,
                        rating, reviews_count, latitude, longitude, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign_id,
                    lead.get('place_id'),
                    lead.get('name', ''),
                    lead.get('address'),
                    lead.get('city'),
                    lead.get('state'),
                    lead.get('postal_code'),
                    lead.get('country'),
                    lead.get('phone'),
                    lead.get('email'),
                    lead.get('website'),
                    lead.get('category'),
                    lead.get('rating'),
                    lead.get('reviews_count'),
                    lead.get('latitude'),
                    lead.get('longitude'),
                    'new'
                ))
            conn.commit()
        
        logger.info(f"Inserted {len(leads)} leads for campaign {campaign_id}")
    
    def update_lead(self, lead_id: int, updates: Dict[str, Any]):
        """Update a specific lead."""
        if not updates:
            return
        
        # Handle JSON fields
        json_fields = ['linkedin_profile', 'research_data', 'personalized_message']
        processed_updates = {}
        
        for key, value in updates.items():
            if key in json_fields and value is not None:
                processed_updates[key] = json.dumps(value)
            else:
                processed_updates[key] = value
        
        # Build dynamic update query
        set_clause = ", ".join([f"{key} = ?" for key in processed_updates.keys()])
        values = list(processed_updates.values()) + [lead_id]
        
        # Always update timestamp
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE leads 
                SET {set_clause}
                WHERE id = ?
            """, values)
            conn.commit()
        
        logger.debug(f"Updated lead {lead_id}")
    
    def get_leads_by_campaign(self, campaign_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all leads for a campaign, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status:
                cursor = conn.execute(
                    "SELECT * FROM leads WHERE campaign_id = ? AND status = ? ORDER BY id",
                    (campaign_id, status)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM leads WHERE campaign_id = ? ORDER BY id",
                    (campaign_id,)
                )
            
            leads = []
            for row in cursor.fetchall():
                lead = dict(row)
                
                # Parse JSON fields
                json_fields = ['linkedin_profile', 'research_data', 'personalized_message']
                for field in json_fields:
                    if lead.get(field):
                        try:
                            lead[field] = json.loads(lead[field])
                        except json.JSONDecodeError:
                            lead[field] = None
                
                leads.append(lead)
            
            return leads
    
    def get_lead_by_id(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific lead by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            
            if row:
                lead = dict(row)
                
                # Parse JSON fields
                json_fields = ['linkedin_profile', 'research_data', 'personalized_message']
                for field in json_fields:
                    if lead.get(field):
                        try:
                            lead[field] = json.loads(lead[field])
                        except json.JSONDecodeError:
                            lead[field] = None
                
                return lead
            return None
    
    def update_leads_batch(self, campaign_id: str, updates: List[Dict[str, Any]]):
        """Batch update multiple leads."""
        if not updates:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for update in updates:
                lead_id = update.pop('id', None)
                if not lead_id:
                    continue
                
                # Handle JSON fields
                json_fields = ['linkedin_profile', 'research_data', 'personalized_message']
                processed_updates = {}
                
                for key, value in update.items():
                    if key in json_fields and value is not None:
                        processed_updates[key] = json.dumps(value)
                    else:
                        processed_updates[key] = value
                
                if processed_updates:
                    set_clause = ", ".join([f"{key} = ?" for key in processed_updates.keys()])
                    values = list(processed_updates.values()) + [lead_id]
                    set_clause += ", updated_at = CURRENT_TIMESTAMP"
                    
                    conn.execute(f"""
                        UPDATE leads 
                        SET {set_clause}
                        WHERE id = ? AND campaign_id = ?
                    """, values + [campaign_id])
            
            conn.commit()
        
        logger.info(f"Batch updated {len(updates)} leads")
    
    def record_pipeline_run(self, campaign_id: str, stage: str, status: str, 
                          duration: Optional[float] = None, processed: int = 0, 
                          success: int = 0, errors: int = 0, error_message: Optional[str] = None):
        """Record a pipeline run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO pipeline_runs (
                    campaign_id, stage, status, completed_at, duration_seconds,
                    processed_count, success_count, error_count, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id, stage, status,
                datetime.now() if status == 'completed' else None,
                duration, processed, success, errors, error_message
            ))
            conn.commit()
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a campaign."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Campaign info
            campaign = self.get_campaign(campaign_id)
            if not campaign:
                return {}
            
            # Lead statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_leads,
                    SUM(CASE WHEN email_valid = 1 THEN 1 ELSE 0 END) as valid_emails,
                    SUM(CASE WHEN phone_valid = 1 THEN 1 ELSE 0 END) as valid_phones,
                    SUM(CASE WHEN linkedin_profile IS NOT NULL THEN 1 ELSE 0 END) as enriched_leads,
                    SUM(CASE WHEN research_data IS NOT NULL THEN 1 ELSE 0 END) as researched_leads,
                    SUM(CASE WHEN personalized_message IS NOT NULL THEN 1 ELSE 0 END) as personalized_leads
                FROM leads 
                WHERE campaign_id = ?
            """, (campaign_id,))
            
            stats = dict(cursor.fetchone())
            
            # Pipeline runs
            cursor = conn.execute("""
                SELECT stage, status, COUNT(*) as count, AVG(duration_seconds) as avg_duration
                FROM pipeline_runs 
                WHERE campaign_id = ?
                GROUP BY stage, status
            """, (campaign_id,))
            
            pipeline_stats = []
            for row in cursor.fetchall():
                pipeline_stats.append(dict(row))
            
            return {
                'campaign': campaign,
                'leads': stats,
                'pipeline_runs': pipeline_stats
            }
    
    def export_to_csv(self, campaign_id: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """Export leads to CSV."""
        if campaign_id:
            leads = self.get_leads_by_campaign(campaign_id)
            filename = f"leads_{campaign_id}.csv"
        else:
            # Export all leads
            with sqlite3.connect(self.db_path) as conn:
                leads = pd.read_sql_query("SELECT * FROM leads", conn)
            filename = "all_leads.csv"
        
        if output_path:
            filepath = Path(output_path)
        else:
            filepath = Path("data") / filename
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to DataFrame and export
        if isinstance(leads, list):
            df = pd.DataFrame(leads)
        else:
            df = leads
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported leads to: {filepath}")
        return str(filepath)
    
    def cleanup_old_campaigns(self, days_old: int = 30):
        """Clean up campaigns older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete old pipeline runs first (foreign key constraint)
            conn.execute("""
                DELETE FROM pipeline_runs 
                WHERE campaign_id IN (
                    SELECT id FROM campaigns 
                    WHERE created_at < datetime('now', '-{} days')
                )
            """.format(days_old))
            
            # Delete old leads
            conn.execute("""
                DELETE FROM leads 
                WHERE campaign_id IN (
                    SELECT id FROM campaigns 
                    WHERE created_at < datetime('now', '-{} days')
                )
            """.format(days_old))
            
            # Delete old campaigns
            cursor = conn.execute("""
                DELETE FROM campaigns 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days_old))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old campaigns")
            return deleted_count
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Table counts
            campaigns_count = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
            leads_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            runs_count = conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0]
            
            # Recent activity
            recent_campaigns = conn.execute("""
                SELECT COUNT(*) FROM campaigns 
                WHERE created_at > datetime('now', '-7 days')
            """).fetchone()[0]
            
            return {
                'database_path': str(self.db_path),
                'database_size_mb': self.db_path.stat().st_size / 1024 / 1024,
                'campaigns_count': campaigns_count,
                'leads_count': leads_count,
                'pipeline_runs_count': runs_count,
                'recent_campaigns': recent_campaigns
            }

# Export the class
__all__ = ['SQLiteManager']
