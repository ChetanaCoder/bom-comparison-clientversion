#!/bin/bash

echo "🚀 Starting Enhanced Autonomous BOM Platform with QA Classification..."
echo "=" * 60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "start.sh" ]; then
    print_error "Please run this script from the autonomous_bom_platform_qa_enhanced directory"
    exit 1
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

print_info "Starting backend and frontend services..."

# Configure environment
if [ ! -f "backend/.env" ]; then
    print_info "Setting up backend environment..."
    cp backend/.env.example backend/.env
    print_warning "Please configure your GEMINI_API_KEY in backend/.env for full AI functionality"
fi

if [ ! -f "frontend/.env.local" ]; then
    print_info "Setting up frontend environment..."
    echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env.local
fi

# Function to kill background processes on exit
cleanup() {
    print_info "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start backend
print_info "Setting up Python virtual environment..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Start backend server
print_status "Starting backend server on http://localhost:8000"
python main.py &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend
cd ../frontend
print_info "Installing Node.js dependencies..."
npm install

print_status "Starting frontend development server on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

# Display startup information
echo ""
print_status "Enhanced Autonomous BOM Platform is starting up!"
echo "=================================="
print_info "Backend: http://localhost:8000"
print_info "Frontend: http://localhost:3000"  
print_info "API Docs: http://localhost:8000/docs"
print_info "Health Check: http://localhost:8000/health"
echo ""
print_status "🤖 Autonomous Agents with QA Classification Enabled!"
print_info "   - Translation Agent: Document processing"
print_info "   - Extraction Agent: QA classification (13 categories)"  
print_info "   - Supplier BOM Agent: Excel/CSV processing"
print_info "   - Comparison Agent: Intelligent matching"
echo ""
print_status "📋 Test Documents Available:"
print_info "   - frontend/test-documents/japanese-qa-document.txt"
print_info "   - frontend/test-documents/supplier-bom.csv"
echo ""
print_warning "Configure GEMINI_API_KEY in backend/.env for full AI functionality"
print_info "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
