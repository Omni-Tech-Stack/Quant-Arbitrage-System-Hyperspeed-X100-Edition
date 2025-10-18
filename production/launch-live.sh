#!/bin/bash

# Live Operations Launcher for Quant Arbitrage System: Hyperspeed X100 Edition
# This script launches the complete system in LIVE trading mode with UI/Dashboard

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=${BACKEND_PORT:-3001}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
LOG_DIR="./logs"
PID_DIR="./pids"

# Print banner
print_banner() {
    clear
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║  🚀 Quant Arbitrage System: Hyperspeed X100 Edition                   ║"
    echo "║     LIVE OPERATIONS LAUNCHER                                          ║"
    echo "║                                                                        ║"
    echo "║  ⚡ Real-Time Trading  |  📊 Live Dashboard  |  🎯 MEV Protection     ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print step
print_step() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

# Print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Print info
print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Create directories
create_directories() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command -v node >/dev/null 2>&1; then
        missing_deps+=("node")
    fi
    
    if ! command -v npm >/dev/null 2>&1; then
        missing_deps+=("npm")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  - Node.js: https://nodejs.org/"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Pre-flight checks
preflight_checks() {
    print_step "Running pre-flight checks..."
    
    # Check if backend exists
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found!"
        exit 1
    fi
    
    # Check if frontend exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found!"
        exit 1
    fi
    
    # Check if backend dependencies are installed
    if [ ! -d "backend/node_modules" ]; then
        print_warning "Backend dependencies not installed. Installing..."
        cd backend && npm install && cd ..
    fi
    
    # Check if frontend dependencies are installed
    if [ ! -d "frontend/node_modules" ]; then
        print_warning "Frontend dependencies not installed. Installing..."
        cd frontend && npm install && cd ..
    fi
    
    # Check if ports are available
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $BACKEND_PORT is already in use!"
        print_info "Stop the process using: kill \$(lsof -t -i:$BACKEND_PORT)"
        exit 1
    fi
    
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $FRONTEND_PORT is already in use!"
        print_info "Stop the process using: kill \$(lsof -t -i:$FRONTEND_PORT)"
        exit 1
    fi
    
    print_success "Pre-flight checks passed"
}

# Configuration check
check_configuration() {
    print_step "Checking configuration..."
    
    local warnings=0
    
    # Check for environment variables
    if [ -z "$ETHEREUM_RPC_URL" ] && [ -z "$POLYGON_RPC_URL" ]; then
        print_warning "No RPC endpoints configured (ETHEREUM_RPC_URL, POLYGON_RPC_URL)"
        print_info "System will run in DEMO MODE with simulated data"
        export DEMO_MODE=true
        warnings=$((warnings + 1))
    fi
    
    if [ -z "$PRIVATE_KEY" ] && [ -z "$WALLET_MNEMONIC" ]; then
        print_warning "No wallet credentials configured (PRIVATE_KEY, WALLET_MNEMONIC)"
        print_info "Wallet management will be in demo mode"
        warnings=$((warnings + 1))
    fi
    
    if [ $warnings -gt 0 ]; then
        echo ""
        print_warning "Configuration warnings detected. System will run in limited mode."
        echo ""
        echo "For full functionality, configure:"
        echo "  export ETHEREUM_RPC_URL='https://mainnet.infura.io/v3/YOUR_KEY'"
        echo "  export POLYGON_RPC_URL='https://polygon-rpc.com'"
        echo "  export PRIVATE_KEY='0x...'"
        echo ""
        read -p "Continue in demo mode? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Configuration validated"
    fi
}

# Start backend
start_backend() {
    print_step "Starting backend API server..."
    
    cd backend
    
    # Start backend in background
    PORT=$BACKEND_PORT node server.js > "../$LOG_DIR/backend.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/backend.pid"
    
    cd ..
    
    # Wait for backend to start
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$BACKEND_PORT/api/health >/dev/null 2>&1; then
            print_success "Backend API started (PID: $pid, Port: $BACKEND_PORT)"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend failed to start"
            cat "$LOG_DIR/backend.log"
            exit 1
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
}

# Start frontend
start_frontend() {
    print_step "Starting frontend dashboard..."
    
    cd frontend
    
    # Start frontend in background
    npm start > "../$LOG_DIR/frontend.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/frontend.pid"
    
    cd ..
    
    # Wait for frontend to start
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
            print_success "Frontend dashboard started (PID: $pid, Port: $FRONTEND_PORT)"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Frontend failed to start"
            cat "$LOG_DIR/frontend.log"
            exit 1
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
}

# Display system status
show_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}System Started Successfully!${NC}"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${CYAN}🌐 Access URLs:${NC}"
    echo "   📊 Dashboard:    http://localhost:$FRONTEND_PORT"
    echo "   🔌 Backend API:  http://localhost:$BACKEND_PORT"
    echo "   📋 API Health:   http://localhost:$BACKEND_PORT/api/health"
    echo "   📈 Statistics:   http://localhost:$BACKEND_PORT/api/stats"
    echo ""
    echo -e "${CYAN}📁 Log Files:${NC}"
    echo "   Backend:  $LOG_DIR/backend.log"
    echo "   Frontend: $LOG_DIR/frontend.log"
    echo ""
    echo -e "${CYAN}🔧 Process Management:${NC}"
    echo "   View logs:       tail -f $LOG_DIR/backend.log"
    echo "   Monitor status:  watch -n 1 'curl -s http://localhost:$BACKEND_PORT/api/stats'"
    echo "   Stop system:     ./stop-live.sh"
    echo ""
    
    if [ "$DEMO_MODE" = "true" ]; then
        echo -e "${YELLOW}⚠️  DEMO MODE ACTIVE${NC}"
        echo "   System is running with simulated data"
        echo "   Configure RPC endpoints for live trading"
        echo ""
    else
        echo -e "${GREEN}✅ LIVE MODE ACTIVE${NC}"
        echo "   System is ready for real trading operations"
        echo ""
    fi
    
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
}

# Real-time monitoring
start_monitoring() {
    print_step "Starting real-time monitoring..."
    echo ""
    
    # Display initial stats
    print_info "Fetching initial statistics..."
    sleep 2
    
    if curl -s http://localhost:$BACKEND_PORT/api/stats >/dev/null 2>&1; then
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}                    LIVE SYSTEM MONITOR${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Show live stats
        local stats=$(curl -s http://localhost:$BACKEND_PORT/api/stats)
        echo -e "${GREEN}Current Statistics:${NC}"
        echo "$stats" | grep -E "(opportunities|trades|successRate)" | head -10 || echo "Statistics initializing..."
        echo ""
    fi
    
    print_info "System is now running. Press Ctrl+C to view shutdown options."
    echo ""
    
    # Trap Ctrl+C
    trap 'show_shutdown_menu' INT
    
    # Keep monitoring
    while true; do
        sleep 5
        # Check if processes are still running
        if [ -f "$PID_DIR/backend.pid" ]; then
            local backend_pid=$(cat "$PID_DIR/backend.pid")
            if ! ps -p $backend_pid > /dev/null 2>&1; then
                print_error "Backend process has stopped unexpectedly!"
                print_info "Check logs: $LOG_DIR/backend.log"
                cleanup_and_exit 1
            fi
        fi
        
        if [ -f "$PID_DIR/frontend.pid" ]; then
            local frontend_pid=$(cat "$PID_DIR/frontend.pid")
            if ! ps -p $frontend_pid > /dev/null 2>&1; then
                print_warning "Frontend process has stopped unexpectedly!"
                print_info "Check logs: $LOG_DIR/frontend.log"
            fi
        fi
    done
}

# Show shutdown menu
show_shutdown_menu() {
    echo ""
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}                    SHUTDOWN OPTIONS${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  1) Stop all services and exit"
    echo "  2) View backend logs"
    echo "  3) View frontend logs"
    echo "  4) View system statistics"
    echo "  5) Resume monitoring"
    echo ""
    read -p "Select option (1-5): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            cleanup_and_exit 0
            ;;
        2)
            tail -n 50 "$LOG_DIR/backend.log"
            show_shutdown_menu
            ;;
        3)
            tail -n 50 "$LOG_DIR/frontend.log"
            show_shutdown_menu
            ;;
        4)
            curl -s http://localhost:$BACKEND_PORT/api/stats | head -20
            show_shutdown_menu
            ;;
        5)
            print_info "Resuming monitoring... Press Ctrl+C for options."
            ;;
        *)
            print_warning "Invalid option"
            show_shutdown_menu
            ;;
    esac
}

# Cleanup and exit
cleanup_and_exit() {
    local exit_code=${1:-0}
    
    echo ""
    print_step "Shutting down system..."
    
    # Stop backend
    if [ -f "$PID_DIR/backend.pid" ]; then
        local pid=$(cat "$PID_DIR/backend.pid")
        if ps -p $pid > /dev/null 2>&1; then
            print_info "Stopping backend (PID: $pid)..."
            kill $pid 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null || true
            fi
            print_success "Backend stopped"
        fi
        rm "$PID_DIR/backend.pid"
    fi
    
    # Stop frontend
    if [ -f "$PID_DIR/frontend.pid" ]; then
        local pid=$(cat "$PID_DIR/frontend.pid")
        if ps -p $pid > /dev/null 2>&1; then
            print_info "Stopping frontend (PID: $pid)..."
            kill $pid 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null || true
            fi
            print_success "Frontend stopped"
        fi
        rm "$PID_DIR/frontend.pid"
    fi
    
    echo ""
    print_success "System shutdown complete"
    echo ""
    print_info "Logs preserved in: $LOG_DIR/"
    echo ""
    
    exit $exit_code
}

# Main launch flow
main() {
    print_banner
    
    # Check if we're in the right directory
    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Please run this script from the project root directory."
        exit 1
    fi
    
    create_directories
    check_prerequisites
    preflight_checks
    check_configuration
    start_backend
    start_frontend
    show_status
    start_monitoring
}

# Run main function
main "$@"
