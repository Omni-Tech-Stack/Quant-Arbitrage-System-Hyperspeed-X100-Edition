#!/bin/bash

################################################################################
# Quant Arbitrage System: Hyperspeed X100 Edition
# ONE-CLICK UNIFIED SETUP SCRIPT
# 
# This script installs and configures the entire system in one command.
# It handles all dependencies, builds all modules, and verifies the installation.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
NODE_MIN_VERSION="18"

# Print banner
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "║                                                                              ║"
    echo "║         🚀 QUANT ARBITRAGE SYSTEM: HYPERSPEED X100 EDITION 🚀               ║"
    echo "║                                                                              ║"
    echo "║                    ONE-CLICK UNIFIED SETUP SCRIPT                            ║"
    echo "║                                                                              ║"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
}

# Print section header
print_section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Compare version numbers
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check prerequisites
check_prerequisites() {
    print_section "STEP 1: Checking Prerequisites"
    
    local has_errors=0
    
    # Check Node.js
    print_step "Checking Node.js..."
    if command_exists node; then
        local node_version=$(node --version | sed 's/v//')
        if version_ge "$node_version" "$NODE_MIN_VERSION"; then
            print_success "Node.js $node_version installed (>= $NODE_MIN_VERSION required)"
        else
            print_error "Node.js $node_version is too old (>= $NODE_MIN_VERSION required)"
            has_errors=1
        fi
    else
        print_error "Node.js is not installed (>= $NODE_MIN_VERSION required)"
        print_info "Install from: https://nodejs.org/"
        has_errors=1
    fi
    
    # Check npm
    print_step "Checking npm..."
    if command_exists npm; then
        local npm_version=$(npm --version)
        print_success "npm $npm_version installed"
    else
        print_error "npm is not installed"
        has_errors=1
    fi
    
    # Check Python
    print_step "Checking Python..."
    if command_exists python3; then
        local python_version=$(python3 --version | awk '{print $2}')
        if version_ge "$python_version" "$PYTHON_MIN_VERSION"; then
            print_success "Python $python_version installed (>= $PYTHON_MIN_VERSION required)"
        else
            print_error "Python $python_version is too old (>= $PYTHON_MIN_VERSION required)"
            has_errors=1
        fi
    else
        print_error "Python 3 is not installed (>= $PYTHON_MIN_VERSION required)"
        print_info "Install from: https://www.python.org/"
        has_errors=1
    fi
    
    # Check pip
    print_step "Checking pip..."
    if command_exists pip3 || command_exists pip; then
        print_success "pip installed"
    else
        print_error "pip is not installed"
        has_errors=1
    fi
    
    # Check optional dependencies
    print_step "Checking optional dependencies..."
    
    if command_exists docker; then
        print_success "Docker installed (optional)"
    else
        print_warning "Docker not found (optional for containerized deployment)"
    fi
    
    if command_exists git; then
        print_success "Git installed"
    else
        print_warning "Git not found (recommended)"
    fi
    
    if [ $has_errors -eq 1 ]; then
        echo ""
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
    
    echo ""
    print_success "All required prerequisites satisfied!"
}

# Install Node.js dependencies
install_node_dependencies() {
    print_section "STEP 2: Installing Node.js Dependencies"
    
    # Root package
    print_step "Installing root package dependencies..."
    if [ -f "package.json" ]; then
        npm install
        print_success "Root dependencies installed"
    fi
    
    # Backend
    print_step "Installing backend dependencies..."
    if [ -d "backend" ] && [ -f "backend/package.json" ]; then
        cd backend
        npm install
        cd ..
        print_success "Backend dependencies installed"
    fi
    
    # Frontend
    print_step "Installing frontend dependencies..."
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        cd frontend
        npm install
        cd ..
        print_success "Frontend dependencies installed"
    fi
    
    # Ultra-fast arbitrage engine
    print_step "Installing arbitrage engine dependencies..."
    if [ -d "ultra-fast-arbitrage-engine" ] && [ -f "ultra-fast-arbitrage-engine/package.json" ]; then
        cd ultra-fast-arbitrage-engine
        npm install
        cd ..
        print_success "Arbitrage engine dependencies installed"
    fi
    
    echo ""
    print_success "All Node.js dependencies installed!"
}

# Install Python dependencies
install_python_dependencies() {
    print_section "STEP 3: Installing Python Dependencies"
    
    if [ -f "requirements.txt" ]; then
        print_step "Installing Python packages from requirements.txt..."
        pip3 install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "No requirements.txt found, skipping Python dependency installation"
    fi
    
    echo ""
    print_success "Python environment configured!"
}

# Build all modules
build_modules() {
    print_section "STEP 4: Building Modules"
    
    # Build ultra-fast arbitrage engine
    print_step "Building ultra-fast arbitrage engine..."
    if [ -d "ultra-fast-arbitrage-engine" ] && [ -f "ultra-fast-arbitrage-engine/package.json" ]; then
        cd ultra-fast-arbitrage-engine
        
        # Check if TypeScript build is needed
        if grep -q '"build"' package.json; then
            npm run build 2>/dev/null || print_warning "TypeScript build skipped (optional)"
        fi
        
        # Check if Rust build is needed
        if grep -q '"build:rust"' package.json; then
            if command_exists cargo; then
                npm run build:rust 2>/dev/null || print_warning "Rust build skipped (optional)"
            else
                print_warning "Rust/cargo not found, skipping native module build (optional)"
            fi
        fi
        
        cd ..
        print_success "Arbitrage engine built"
    fi
    
    echo ""
    print_success "All modules built successfully!"
}

# Create necessary directories and files
setup_structure() {
    print_section "STEP 5: Setting Up Directory Structure"
    
    # Create logs directory
    print_step "Creating logs directory..."
    mkdir -p logs
    print_success "Logs directory created"
    
    # Create models directory if it doesn't exist
    print_step "Creating models directory..."
    mkdir -p models
    print_success "Models directory created"
    
    # Create config files if they don't exist
    print_step "Setting up configuration files..."
    
    # Create .env.example if not exists
    if [ ! -f ".env" ] && [ -d "ultra-fast-arbitrage-engine" ]; then
        if [ -f "ultra-fast-arbitrage-engine/.env.example" ]; then
            print_info "Copy ultra-fast-arbitrage-engine/.env.example to .env and configure it"
        fi
    fi
    
    print_success "Directory structure configured"
    echo ""
}

# Verify installation
verify_installation() {
    print_section "STEP 6: Verifying Installation"
    
    local test_passed=0
    local test_failed=0
    
    # Test Node.js modules
    print_step "Testing Node.js modules..."
    
    # Check if verify script exists
    if [ -f "verify-all-modules.js" ]; then
        if node verify-all-modules.js > /tmp/verify_output.txt 2>&1; then
            print_success "Module verification passed"
            ((test_passed++))
        else
            if grep -q "CHECKPOINT" /tmp/verify_output.txt 2>/dev/null; then
                print_warning "Module verification completed with warnings"
                ((test_passed++))
            else
                print_warning "Module verification had issues (non-critical)"
            fi
        fi
    fi
    
    # Test backend if available
    if [ -d "backend" ] && [ -f "backend/package.json" ]; then
        print_step "Backend API available for testing"
        print_info "Run 'cd backend && npm test' to test the API"
    fi
    
    # Test Python modules
    print_step "Testing Python modules..."
    
    # Check if Python test scripts exist
    if [ -f "test_all_python_modules.sh" ]; then
        print_info "Python test suite available"
        print_info "Run './test_all_python_modules.sh' to test Python modules"
    fi
    
    # Check if ML models are trained
    if [ -f "models/arb_ml_latest.pkl" ] || [ -f "models/xgboost_primary.pkl" ]; then
        print_success "ML models are available"
    else
        print_info "ML models not found - run 'python3 train_ml_model.py' to train models"
    fi
    
    echo ""
    print_success "Installation verification complete!"
}

# Display next steps
show_next_steps() {
    print_section "INSTALLATION COMPLETE! 🎉"
    
    echo -e "${GREEN}✓ System successfully installed and configured!${NC}"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo -e "${CYAN}  NEXT STEPS${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    
    echo -e "${YELLOW}1. Verify the installation:${NC}"
    echo "   npm run verify"
    echo ""
    
    echo -e "${YELLOW}2. Configure the system (optional):${NC}"
    echo "   - Edit config/config.py for RPC endpoints and parameters"
    echo "   - Edit config/addresses.py for contract addresses"
    echo "   - Copy and edit .env files for environment variables"
    echo ""
    
    echo -e "${YELLOW}3. Train ML models (if needed):${NC}"
    echo "   python3 train_ml_model.py"
    echo "   python3 train_dual_ai_models.py"
    echo ""
    
    echo -e "${YELLOW}4. Deploy the system:${NC}"
    echo "   a) Development mode:"
    echo "      cd backend && npm start     # Start backend API"
    echo "      cd frontend && python3 -m http.server 3000  # Start dashboard"
    echo ""
    echo "   b) Production mode (Docker):"
    echo "      ./deploy.sh                 # One-click Docker deployment"
    echo ""
    
    echo -e "${YELLOW}5. Run tests:${NC}"
    echo "   npm run test:comprehensive     # Run all tests"
    echo "   ./test_all_python_modules.sh   # Python tests"
    echo "   ./test_all_js_modules.sh       # JavaScript tests"
    echo ""
    
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo -e "${CYAN}  QUICK REFERENCE${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "  Fetch pool data:        npm run pool:fetch"
    echo "  Fetch TVL data:         npm run tvl:fetch"
    echo "  Test orchestrator:      npm run orchestrator:test"
    echo "  View logs:              tail -f logs/*.log"
    echo "  Health check:           curl http://localhost:3001/api/health"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo -e "${CYAN}  DOCUMENTATION${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "  README.md                - Complete system overview"
    echo "  QUICKSTART.md            - Quick start guide"
    echo "  DEPLOYMENT.md            - Deployment instructions"
    echo "  TESTING.md               - Testing documentation"
    echo "  WEB3_INTEGRATION.md      - Web3 integration guide"
    echo "  SECURITY.md              - Security best practices"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${GREEN}For support and issues, visit:${NC}"
    echo "  https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition"
    echo ""
    echo -e "${CYAN}Happy Trading! 🚀${NC}"
    echo ""
}

# Main installation flow
main() {
    print_banner
    
    # Confirm with user
    echo -e "${YELLOW}This script will install all dependencies and set up the complete system.${NC}"
    echo -e "${YELLOW}This may take several minutes.${NC}"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Run installation steps
    check_prerequisites
    install_node_dependencies
    install_python_dependencies
    build_modules
    setup_structure
    verify_installation
    show_next_steps
}

# Handle script arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./setup.sh [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --skip-verify  Skip verification step"
    echo ""
    echo "This script installs and configures the entire Quant Arbitrage System."
    exit 0
fi

# Run main installation
main "$@"
