#!/bin/bash

# Enhanced startup script for full stack lead generation system
# Automatically detects available ports and starts both backend and frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_START_PORT=8000
FRONTEND_START_PORT=8080
MAX_PORT_ATTEMPTS=20

# Function to find available port
find_free_port() {
    local start_port=$1
    local max_attempts=$2
    
    for ((port=start_port; port<start_port+max_attempts; port++)); do
        if ! nc -z localhost $port 2>/dev/null; then
            echo $port
            return 0
        fi
    done
    
    echo "ERROR: No free ports found starting from $start_port" >&2
    return 1
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend server (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend server (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

echo -e "${BLUE}🚀 Starting Lead Generation Full Stack System${NC}"
echo "=================================================="

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command_exists python && ! command_exists python3; then
    echo -e "${RED}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)
echo -e "${GREEN}✅ Python found: $PYTHON_CMD${NC}"

# Check Node.js and npm
if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm not found. Please install npm${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
echo -e "${GREEN}✅ npm found: $(npm --version)${NC}"

# Check for netcat (for port checking)
if ! command_exists nc; then
    echo -e "${YELLOW}⚠️  netcat not found. Port checking may not work properly${NC}"
fi

# Find available ports
echo -e "${YELLOW}Finding available ports...${NC}"

BACKEND_PORT=$(find_free_port $BACKEND_START_PORT $MAX_PORT_ATTEMPTS)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Could not find free port for backend${NC}"
    exit 1
fi

FRONTEND_PORT=$(find_free_port $FRONTEND_START_PORT $MAX_PORT_ATTEMPTS)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Could not find free port for frontend${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend port: $BACKEND_PORT${NC}"
echo -e "${GREEN}✅ Frontend port: $FRONTEND_PORT${NC}"

# Check if virtual environment exists
if [ -d "env" ] || [ -d "venv" ] || [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment detected${NC}"
    
    # Try to activate virtual environment
    if [ -f "env/bin/activate" ]; then
        source env/bin/activate
        echo -e "${GREEN}✅ Activated virtual environment: env${NC}"
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Activated virtual environment: venv${NC}"
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Activated virtual environment: .venv${NC}"
    fi
fi

# Install/check Python dependencies
echo -e "${YELLOW}Checking Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    $PYTHON_CMD -m pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found${NC}"
    exit 1
fi

cd frontend

# Install frontend dependencies
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

cd ..

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env template...${NC}"
    cat > .env << EOF
# Google Places API (Required)
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# AI APIs (Required for full pipeline)
PERPLEXITY_API_KEY=your_perplexity_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Campaign Management (Optional)
INSTANTLY_API_KEY=your_instantly_api_key_here
INSTANTLY_FROM_EMAIL=your@email.com

# LinkedIn (Optional - for profile enrichment)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
EOF
    echo -e "${GREEN}✅ Created .env template${NC}"
    echo -e "${YELLOW}⚠️  Please update .env file with your API keys${NC}"
fi

# Start backend server
echo -e "${YELLOW}Starting backend server...${NC}"
$PYTHON_CMD api_server.py $BACKEND_PORT &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend server started successfully${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend server failed to start${NC}"
        exit 1
    fi
    
    sleep 1
done

# Create frontend environment file
echo -e "${YELLOW}Configuring frontend...${NC}"
cat > frontend/.env.local << EOF
VITE_API_BASE_URL=http://localhost:$BACKEND_PORT
VITE_API_URL=http://localhost:$BACKEND_PORT/api
EOF

# Start frontend server
echo -e "${YELLOW}Starting frontend server...${NC}"
cd frontend
npm run dev -- --port $FRONTEND_PORT --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend server started successfully${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Frontend server failed to start${NC}"
        exit 1
    fi
    
    sleep 1
done

# Display access information
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Full Stack System Started Successfully!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Access Points:${NC}"
echo -e "🌐 Frontend Dashboard: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "🔧 Backend API:        ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "📚 API Documentation:  ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "❤️  Health Check:       ${GREEN}http://localhost:$BACKEND_PORT/health${NC}"
echo ""
echo -e "${BLUE}Process Information:${NC}"
echo -e "Backend PID:  $BACKEND_PID"
echo -e "Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "• Update .env file with your API keys for full functionality"
echo -e "• Check API configuration at: http://localhost:$BACKEND_PORT/api/config/check"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process died${NC}"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process died${NC}"
        break
    fi
    
    sleep 5
done

echo -e "${YELLOW}One or more services stopped. Exiting...${NC}"
