# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive lead generation system with a Python FastAPI backend and React TypeScript frontend. The system scrapes business data from Google Places API, validates leads, enriches them with AI research, and manages email campaigns.

## Key Commands

### Development Setup
```bash
# Quick start (recommended) - starts both backend and frontend with port detection
./start_fullstack.sh

# Manual backend startup
python api_server.py

# Manual frontend startup  
cd frontend && npm run dev

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install
```

### Testing
```bash
# Run all test suites
python test_integration.py      # Backend integration tests
python test_backend_functionality.py  # Backend unit tests
python test_frontend.py         # Frontend tests
python test_fullstack.py        # Full stack integration

# Quick functionality test
python main.py test

# Validate system configuration
python main.py setup-pipeline --check-apis
```

### CLI Operations
```bash
# Complete lead generation pipeline
python main.py generate-leads "business_type" --location "City, State" --max-results 25

# Basic business scraping only
python main.py scrape "business_type" --location "City, State" --max-results 50

# Validate existing leads
python main.py validate-leads --input-file leads.csv
```

### Build and Lint
```bash
# Frontend
cd frontend
npm run build        # Build for production
npm run lint         # ESLint checking
npm run preview      # Preview production build

# Backend
python -m flake8     # Python linting
python -m black .    # Python formatting
```

## Architecture

### Core System Components
- **Backend (Python)**: FastAPI server with async background tasks
- **Frontend (React/TypeScript)**: Modern UI with shadcn/ui components and Tailwind CSS  
- **Database**: SQLite for campaigns, leads, and pipeline runs
- **Pipeline**: Modular stages for data collection → validation → enrichment → personalization

### Data Flow
```
Google Places API → SQLite → Lead Validation → LinkedIn Enrichment → AI Research → Message Personalization → Campaign Creation
```

### Key Backend Modules
- `main.py`: CLI interface with Click commands
- `api_server.py`: FastAPI server with CORS middleware
- `leads/pipeline_orchestrator.py`: Main pipeline coordination
- `leads/sqlite_manager.py`: Database operations and exports
- `leads/lead_validator.py`: Email/phone validation with async processing
- `config.py`: Configuration classes with validation
- `models.py`: Pydantic data models for API requests/responses

### Frontend Structure
- Built with Vite + React + TypeScript
- Uses shadcn/ui component library with Radix UI primitives
- Tailwind CSS for styling
- Real-time status updates via API polling every 2 seconds
- Components in `src/components/` with UI primitives in `src/components/ui/`

### Database Schema
- **campaigns**: Campaign metadata, query parameters, status tracking
- **leads**: Complete lead data with validation scores, LinkedIn profiles, AI research
- **pipeline_runs**: Execution history and performance metrics

## Configuration

### Required Environment Variables
Create `.env` file with:
- `GOOGLE_PLACES_API_KEY`: For business data scraping
- `PERPLEXITY_API_KEY`: For AI company research  
- `ANTHROPIC_API_KEY`: For message personalization
- `INSTANTLY_API_KEY` (optional): For email campaign automation
- `INSTANTLY_FROM_EMAIL` (optional): Sender email for campaigns

### API Integration Points
- Google Places API for business search
- Perplexity AI for company research
- Anthropic Claude for message personalization  
- Instantly API for email campaign management

## Development Notes

### Port Configuration
- Backend: Starts at port 8000, auto-increments if occupied
- Frontend: Starts at port 8080, auto-increments if occupied
- `start_fullstack.sh` handles automatic port detection and conflict resolution

### Async Processing
- Pipeline uses `asyncio` for concurrent API calls
- Background tasks managed via FastAPI BackgroundTasks
- Task status tracked in global `active_tasks` dictionary with thread locks

### Error Handling
- Graceful fallbacks when APIs are unavailable
- Comprehensive validation with detailed error messages
- Rate limiting and retry logic for external API calls

### Testing Strategy
- Integration tests verify API connectivity and data flow
- Frontend tests check component rendering and API integration
- Full stack tests validate end-to-end workflows
- Configuration validation ensures required environment variables

### Code Patterns
- Use Pydantic models for all data validation
- Async/await pattern for I/O operations
- Context managers for database connections
- Type hints throughout Python codebase
- React functional components with TypeScript interfaces