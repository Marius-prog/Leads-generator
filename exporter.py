"""
Data export functionality for the lead generation system.
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from models import Business, ScrapingResult
from utils import clean_filename, create_unique_filename, sanitize_for_csv

logger = logging.getLogger(__name__)

class DataExporter:
    """Export business data to various formats."""
    
    def __init__(self, output_directory: str = "data"):
        """Initialize exporter with output directory."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def export_data(self, businesses: List[Business], filename: str, format: str = "csv") -> str:
        """Export business data to specified format."""
        if not businesses:
            logger.warning("No businesses to export")
            return ""
        
        # Clean filename
        clean_name = clean_filename(filename)
        
        try:
            if format.lower() == "csv":
                return self._export_csv(businesses, clean_name)
            elif format.lower() == "json":
                return self._export_json(businesses, clean_name)
            elif format.lower() == "excel":
                return self._export_excel(businesses, clean_name)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def _export_csv(self, businesses: List[Business], filename: str) -> str:
        """Export businesses to CSV format."""
        output_path = self.output_directory / f"{filename}.csv"
        output_path = create_unique_filename(str(output_path), ".csv")
        
        fieldnames = [
            'name', 'address', 'city', 'state', 'postal_code', 'country',
            'phone', 'email', 'website', 'category', 'rating', 'reviews_count',
            'latitude', 'longitude'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for business in businesses:
                row = {
                    'name': sanitize_for_csv(business.name),
                    'address': sanitize_for_csv(business.address),
                    'city': sanitize_for_csv(business.city),
                    'state': sanitize_for_csv(business.state),
                    'postal_code': sanitize_for_csv(business.postal_code),
                    'country': sanitize_for_csv(business.country),
                    'phone': sanitize_for_csv(business.phone),
                    'email': sanitize_for_csv(business.email),
                    'website': sanitize_for_csv(business.website),
                    'category': sanitize_for_csv(business.category),
                    'rating': business.rating,
                    'reviews_count': business.reviews_count,
                    'latitude': business.latitude,
                    'longitude': business.longitude
                }
                writer.writerow(row)
        
        logger.info(f"Exported {len(businesses)} businesses to CSV: {output_path}")
        return str(output_path)
    
    def _export_json(self, businesses: List[Business], filename: str) -> str:
        """Export businesses to JSON format."""
        output_path = self.output_directory / f"{filename}.json"
        output_path = create_unique_filename(str(output_path), ".json")
        
        # Convert businesses to dictionaries
        business_data = []
        for business in businesses:
            business_dict = {
                'name': business.name,
                'address': business.address,
                'city': business.city,
                'state': business.state,
                'postal_code': business.postal_code,
                'country': business.country,
                'phone': business.phone,
                'email': business.email,
                'website': business.website,
                'category': business.category,
                'rating': business.rating,
                'reviews_count': business.reviews_count,
                'latitude': business.latitude,
                'longitude': business.longitude
            }
            business_data.append(business_dict)
        
        # Create export data with metadata
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_businesses': len(businesses),
                'format_version': '1.0'
            },
            'businesses': business_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(businesses)} businesses to JSON: {output_path}")
        return str(output_path)
    
    def _export_excel(self, businesses: List[Business], filename: str) -> str:
        """Export businesses to Excel format with analytics."""
        output_path = self.output_directory / f"{filename}.xlsx"
        output_path = create_unique_filename(str(output_path), ".xlsx")
        
        # Convert businesses to DataFrame
        business_data = []
        for business in businesses:
            business_data.append({
                'Name': business.name,
                'Address': business.address,
                'City': business.city,
                'State': business.state,
                'Postal Code': business.postal_code,
                'Country': business.country,
                'Phone': business.phone,
                'Email': business.email,
                'Website': business.website,
                'Category': business.category,
                'Rating': business.rating,
                'Reviews Count': business.reviews_count,
                'Latitude': business.latitude,
                'Longitude': business.longitude
            })
        
        df = pd.DataFrame(business_data)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Businesses', index=False)
            
            # Analytics sheet
            self._create_analytics_sheet(writer, df)
            
            # Summary sheet
            self._create_summary_sheet(writer, df)
        
        logger.info(f"Exported {len(businesses)} businesses to Excel: {output_path}")
        return str(output_path)
    
    def _create_analytics_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create analytics sheet for Excel export."""
        analytics_data = []
        
        # Basic statistics
        analytics_data.append(['Total Businesses', len(df)])
        analytics_data.append(['Businesses with Phone', df['Phone'].notna().sum()])
        analytics_data.append(['Businesses with Email', df['Email'].notna().sum()])
        analytics_data.append(['Businesses with Website', df['Website'].notna().sum()])
        analytics_data.append(['Businesses with Rating', df['Rating'].notna().sum()])
        
        if df['Rating'].notna().any():
            analytics_data.append(['Average Rating', df['Rating'].mean()])
            analytics_data.append(['Highest Rating', df['Rating'].max()])
            analytics_data.append(['Lowest Rating', df['Rating'].min()])
        
        if df['Reviews Count'].notna().any():
            analytics_data.append(['Total Reviews', df['Reviews Count'].sum()])
            analytics_data.append(['Average Reviews per Business', df['Reviews Count'].mean()])
        
        # Category distribution
        if df['Category'].notna().any():
            analytics_data.append(['', ''])  # Empty row
            analytics_data.append(['Category Distribution', ''])
            
            category_counts = df['Category'].value_counts()
            for category, count in category_counts.items():
                analytics_data.append([category, count])
        
        # State distribution
        if df['State'].notna().any():
            analytics_data.append(['', ''])  # Empty row
            analytics_data.append(['State Distribution', ''])
            
            state_counts = df['State'].value_counts()
            for state, count in state_counts.head(10).items():  # Top 10 states
                analytics_data.append([state, count])
        
        # Create analytics DataFrame
        analytics_df = pd.DataFrame(analytics_data, columns=['Metric', 'Value'])
        analytics_df.to_excel(writer, sheet_name='Analytics', index=False)
    
    def _create_summary_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create summary sheet for Excel export."""
        summary_data = []
        
        # Export information
        summary_data.append(['Export Information', ''])
        summary_data.append(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        summary_data.append(['Total Records', len(df)])
        summary_data.append(['Format Version', '1.0'])
        summary_data.append(['', ''])
        
        # Data quality metrics
        summary_data.append(['Data Quality', ''])
        total_records = len(df)
        
        if total_records > 0:
            phone_coverage = (df['Phone'].notna().sum() / total_records) * 100
            email_coverage = (df['Email'].notna().sum() / total_records) * 100
            website_coverage = (df['Website'].notna().sum() / total_records) * 100
            
            summary_data.append(['Phone Coverage', f"{phone_coverage:.1f}%"])
            summary_data.append(['Email Coverage', f"{email_coverage:.1f}%"])
            summary_data.append(['Website Coverage', f"{website_coverage:.1f}%"])
        
        summary_data.append(['', ''])
        
        # Top performing businesses (by reviews)
        if df['Reviews Count'].notna().any():
            summary_data.append(['Top Businesses by Reviews', ''])
            top_businesses = df.nlargest(5, 'Reviews Count')
            
            for _, business in top_businesses.iterrows():
                name = business['Name'][:30] + "..." if len(business['Name']) > 30 else business['Name']
                reviews = business['Reviews Count']
                rating = business['Rating'] if pd.notna(business['Rating']) else 'N/A'
                summary_data.append([name, f"{reviews} reviews (Rating: {rating})"])
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_data, columns=['Item', 'Details'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

class LeadExporter:
    """Export lead data with enhanced functionality."""
    
    def __init__(self, output_directory: str = "data"):
        """Initialize lead exporter."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def export_leads(self, leads: List[Dict[str, Any]], filename: str, format: str = "csv") -> str:
        """Export lead data to specified format."""
        if not leads:
            logger.warning("No leads to export")
            return ""
        
        clean_name = clean_filename(filename)
        
        try:
            if format.lower() == "csv":
                return self._export_leads_csv(leads, clean_name)
            elif format.lower() == "json":
                return self._export_leads_json(leads, clean_name)
            elif format.lower() == "excel":
                return self._export_leads_excel(leads, clean_name)
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting leads: {e}")
            raise
    
    def _export_leads_csv(self, leads: List[Dict[str, Any]], filename: str) -> str:
        """Export leads to CSV format."""
        output_path = self.output_directory / f"{filename}.csv"
        output_path = create_unique_filename(str(output_path), ".csv")
        
        if not leads:
            return str(output_path)
        
        # Get all possible fieldnames from all leads
        fieldnames = set()
        for lead in leads:
            fieldnames.update(lead.keys())
        
        # Sort fieldnames for consistent output
        fieldnames = sorted(list(fieldnames))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lead in leads:
                # Sanitize all values
                sanitized_lead = {}
                for key, value in lead.items():
                    if isinstance(value, (dict, list)):
                        sanitized_lead[key] = json.dumps(value)
                    else:
                        sanitized_lead[key] = sanitize_for_csv(str(value) if value is not None else "")
                
                writer.writerow(sanitized_lead)
        
        logger.info(f"Exported {len(leads)} leads to CSV: {output_path}")
        return str(output_path)
    
    def _export_leads_json(self, leads: List[Dict[str, Any]], filename: str) -> str:
        """Export leads to JSON format."""
        output_path = self.output_directory / f"{filename}.json"
        output_path = create_unique_filename(str(output_path), ".json")
        
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_leads': len(leads),
                'format_version': '1.0'
            },
            'leads': leads
        }
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported {len(leads)} leads to JSON: {output_path}")
        return str(output_path)
    
    def _export_leads_excel(self, leads: List[Dict[str, Any]], filename: str) -> str:
        """Export leads to Excel format."""
        output_path = self.output_directory / f"{filename}.xlsx"
        output_path = create_unique_filename(str(output_path), ".xlsx")
        
        # Flatten complex fields for Excel
        flattened_leads = []
        for lead in leads:
            flattened = {}
            for key, value in lead.items():
                if isinstance(value, (dict, list)):
                    flattened[key] = json.dumps(value)
                else:
                    flattened[key] = value
            flattened_leads.append(flattened)
        
        df = pd.DataFrame(flattened_leads)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Leads', index=False)
            
            # Add lead analytics if we have data
            if len(leads) > 0:
                self._create_lead_analytics_sheet(writer, df, leads)
        
        logger.info(f"Exported {len(leads)} leads to Excel: {output_path}")
        return str(output_path)
    
    def _create_lead_analytics_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame, leads: List[Dict[str, Any]]):
        """Create analytics sheet for lead export."""
        analytics_data = []
        
        # Basic statistics
        analytics_data.append(['Total Leads', len(leads)])
        
        # Status distribution if available
        if 'status' in df.columns:
            analytics_data.append(['', ''])
            analytics_data.append(['Status Distribution', ''])
            status_counts = df['status'].value_counts()
            for status, count in status_counts.items():
                analytics_data.append([status, count])
        
        # Validation statistics
        validation_fields = ['email_valid', 'phone_valid', 'company_valid']
        for field in validation_fields:
            if field in df.columns:
                valid_count = df[field].sum() if df[field].dtype == 'bool' else 0
                analytics_data.append([f'{field.replace("_", " ").title()}', valid_count])
        
        # Create analytics DataFrame
        analytics_df = pd.DataFrame(analytics_data, columns=['Metric', 'Value'])
        analytics_df.to_excel(writer, sheet_name='Analytics', index=False)

# Export classes
__all__ = ['DataExporter', 'LeadExporter']
