"""
FastAPI server for lead generation system.
Provides REST endpoints for frontend integration.
"""

import asyncio
import logging
import os
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import threading
import time

# Import system components
from config import LeadPipelineConfig
from models import LeadGenerationRequest, PipelineStatus, ApiResponse, ConfigStatus
from leads.pipeline_orchestrator import PipelineOrchestrator
from leads.sqlite_manager import SQLiteManager
from utils import setup_logging

# Setup logging
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Global variables for task tracking
active_tasks: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()

# Initialize FastAPI app
app = FastAPI(
    title="Lead Generation API",
    description="API for the comprehensive lead generation system",
    version="2.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = LeadPipelineConfig()
orchestrator = PipelineOrchestrator(config)
db = SQLiteManager()

class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    total_leads: Optional[int] = None
    processed_leads: Optional[int] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

def find_free_port(start_port: int = 8000) -> int:
    """Find a free port starting from the given port."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports available")

async def run_pipeline_task(task_id: str, request: LeadGenerationRequest):
    """Run pipeline task in background."""
    try:
        # Update task status
        with task_lock:
            active_tasks[task_id].update({
                'status': 'running',
                'progress': 0,
                'current_step': 'Starting pipeline',
                'started_at': datetime.now().isoformat()
            })
        
        logger.info(f"Starting pipeline task {task_id}")
        
        # Run the complete pipeline
        results = await orchestrator.run_complete_pipeline(
            business_type=request.business_name,
            location=request.location,
            max_results=request.leads_count,
            campaign_name=f"API Campaign {task_id}",
            from_email=request.from_email
        )
        
        # Update task with results
        with task_lock:
            active_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'current_step': 'Completed',
                'results': results,
                'completed_at': datetime.now().isoformat()
            })
        
        logger.info(f"Pipeline task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline task {task_id} failed: {e}")
        
        # Update task with error
        with task_lock:
            active_tasks[task_id].update({
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now().isoformat()
            })

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint."""
    return ApiResponse(
        success=True,
        message="Lead Generation API is running",
        data={
            'version': '2.0.0',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    )

@app.get("/api/config/check", response_model=ConfigStatus)
async def check_config():
    """Check API configuration status."""
    try:
        api_status = config.get_api_status()
        missing_configs = config.get_missing_configs()
        
        config_status = ConfigStatus(
            google_places_api=api_status.get('google_places', False),
            perplexity_api=api_status.get('perplexity', False),
            anthropic_api=api_status.get('anthropic', False),
            instantly_api=api_status.get('instantly', False),
            database=api_status.get('database', False),
            missing_configs=missing_configs
        )
        
        return config_status
        
    except Exception as e:
        logger.error(f"Config check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leads/generate", response_model=TaskResponse)
async def generate_leads(request: LeadGenerationRequest, background_tasks: BackgroundTasks):
    """Start lead generation pipeline."""
    try:
        # Validate configuration
        errors = config.validate()
        if errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Configuration errors: {', '.join(errors)}"
            )
        
        # Create task ID
        task_id = f"task_{int(time.time())}_{len(active_tasks)}"
        
        # Initialize task tracking
        with task_lock:
            active_tasks[task_id] = {
                'task_id': task_id,
                'status': 'pending',
                'progress': 0,
                'current_step': 'Initializing',
                'request': request.dict(),
                'created_at': datetime.now().isoformat()
            }
        
        # Start background task
        background_tasks.add_task(run_pipeline_task, task_id, request)
        
        return TaskResponse(
            task_id=task_id,
            status='pending',
            message='Lead generation pipeline started'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of a specific task."""
    with task_lock:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_data = active_tasks[task_id].copy()
    
    return TaskStatusResponse(**task_data)

@app.get("/api/leads/tasks", response_model=List[TaskStatusResponse])
async def list_tasks():
    """List all tasks."""
    with task_lock:
        tasks = [TaskStatusResponse(**task_data) for task_data in active_tasks.values()]
    
    return tasks

@app.delete("/api/leads/tasks/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: str):
    """Delete a specific task."""
    with task_lock:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        del active_tasks[task_id]
    
    return ApiResponse(
        success=True,
        message=f"Task {task_id} deleted"
    )

@app.get("/api/campaigns", response_model=ApiResponse)
async def list_campaigns(limit: int = 50):
    """List recent campaigns."""
    try:
        campaigns = orchestrator.list_campaigns(limit)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(campaigns)} campaigns",
            data={
                'campaigns': campaigns,
                'total': len(campaigns)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}", response_model=ApiResponse)
async def get_campaign(campaign_id: str):
    """Get specific campaign details."""
    try:
        status = orchestrator.get_pipeline_status(campaign_id)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return ApiResponse(
            success=True,
            message="Campaign retrieved",
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}/leads", response_model=ApiResponse)
async def get_campaign_leads(campaign_id: str):
    """Get leads for a specific campaign."""
    try:
        leads = db.get_leads_by_campaign(campaign_id)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(leads)} leads for campaign {campaign_id}",
            data={
                'campaign_id': campaign_id,
                'leads': leads,
                'count': len(leads)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get leads for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/info", response_model=ApiResponse)
async def get_database_info():
    """Get database information."""
    try:
        info = db.get_database_info()
        
        return ApiResponse(
            success=True,
            message="Database info retrieved",
            data=info
        )
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc)
        }
    )

def start_server(host: str = "0.0.0.0", port: Optional[int] = None):
    """Start the API server with automatic port detection."""
    if port is None:
        port = find_free_port(8000)
    
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    logger.info(f"Health check: http://{host}:{port}/health")
    
    try:
        uvicorn.run(
            "api_server:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    port = None
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning("Invalid port number, using auto-detection")
    
    start_server(port=port)
