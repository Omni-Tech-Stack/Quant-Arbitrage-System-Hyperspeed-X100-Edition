#!/bin/bash

################################################################################
# System Health Check and Verification Script
# Validates complete system integrity and readiness
################################################################################

# Don't exit on error - we want to complete all checks
set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "║                                                                              ║"
    echo "║              SYSTEM HEALTH CHECK & VERIFICATION                              ║"
    echo "║         Quant Arbitrage System: Hyperspeed X100 Edition                     ║"
    echo "║                                                                              ║"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((CHECKS_WARNING++))
}

check_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_runtime_environment() {
    print_section "1. Runtime Environment"
    
    # Node.js
    if command_exists node; then
        local node_version=$(node --version)
        check_pass "Node.js installed: $node_version"
    else
        check_fail "Node.js not installed"
    fi
    
    # npm
    if command_exists npm; then
        local npm_version=$(npm --version)
        check_pass "npm installed: v$npm_version"
    else
        check_fail "npm not installed"
    fi
    
    # Python
    if command_exists python; then
        local python_version=$(python --version)
        check_pass "Python installed: $python_version"
    else
        check_fail "Python 3 not installed"
    fi
    
    # pip
    if command_exists pip3 || command_exists pip; then
        local pip_version=$(pip3 --version 2>/dev/null || pip --version)
        check_pass "pip installed: $pip_version"
    else
        check_fail "pip not installed"
    fi
    
    # Optional tools
    if command_exists docker; then
        local docker_version=$(docker --version)
        check_pass "Docker installed: $docker_version"
    else
        check_warn "Docker not installed (optional)"
    fi
    
    if command_exists git; then
        local git_version=$(git --version)
        check_pass "Git installed: $git_version"
    else
        check_warn "Git not installed (recommended)"
    fi
}

check_directory_structure() {
    print_section "2. Directory Structure"
    
    # Core directories
    [ -d "backend" ] && check_pass "backend/ directory exists" || check_fail "backend/ directory missing"
    [ -d "frontend" ] && check_pass "frontend/ directory exists" || check_fail "frontend/ directory missing"
    [ -d "ultra-fast-arbitrage-engine" ] && check_pass "ultra-fast-arbitrage-engine/ directory exists" || check_fail "ultra-fast-arbitrage-engine/ directory missing"
    [ -d "config" ] && check_pass "config/ directory exists" || check_fail "config/ directory missing"
    [ -d "scripts" ] && check_pass "scripts/ directory exists" || check_fail "scripts/ directory missing"
    [ -d "models" ] && check_pass "models/ directory exists" || check_fail "models/ directory missing"
    [ -d "logs" ] && check_pass "logs/ directory exists" || check_warn "logs/ directory missing (will be created)"
    [ -d "tests" ] && check_pass "tests/ directory exists" || check_warn "tests/ directory missing"
    [ -d "docs" ] && check_pass "docs/ directory exists" || check_warn "docs/ directory missing"
}

check_core_files() {
    print_section "3. Core Files"
    
    # Root files
    [ -f "package.json" ] && check_pass "package.json exists" || check_fail "package.json missing"
    [ -f "requirements.txt" ] && check_pass "requirements.txt exists" || check_fail "requirements.txt missing"
    [ -f "docker-compose.yml" ] && check_pass "docker-compose.yml exists" || check_fail "docker-compose.yml missing"
    [ -f "setup.sh" ] && check_pass "setup.sh exists" || check_fail "setup.sh missing"
    [ -f "deploy.sh" ] && check_pass "deploy.sh exists" || check_fail "deploy.sh missing"
    [ -f "README.md" ] && check_pass "README.md exists" || check_fail "README.md missing"
    [ -f "INSTALL.md" ] && check_pass "INSTALL.md exists" || check_warn "INSTALL.md missing"
    
    # Backend files
    [ -f "backend/server.js" ] && check_pass "backend/server.js exists" || check_fail "backend/server.js missing"
    [ -f "backend/package.json" ] && check_pass "backend/package.json exists" || check_fail "backend/package.json missing"
    
    # Frontend files
    [ -f "frontend/index.html" ] && check_pass "frontend/index.html exists" || check_fail "frontend/index.html missing"
    [ -f "frontend/app.js" ] && check_pass "frontend/app.js exists" || check_fail "frontend/app.js missing"
    
    # Engine files
    [ -f "ultra-fast-arbitrage-engine/index.ts" ] && check_pass "ultra-fast-arbitrage-engine/index.ts exists" || check_fail "ultra-fast-arbitrage-engine/index.ts missing"
    [ -f "ultra-fast-arbitrage-engine/package.json" ] && check_pass "ultra-fast-arbitrage-engine/package.json exists" || check_fail "ultra-fast-arbitrage-engine/package.json missing"
}

check_python_modules() {
    print_section "4. Python Modules"
    
    # Core Python modules
    [ -f "main_quant_hybrid_orchestrator.py" ] && check_pass "main_quant_hybrid_orchestrator.py exists" || check_fail "main_quant_hybrid_orchestrator.py missing"
    [ -f "orchestrator_tvl_hyperspeed.py" ] && check_pass "orchestrator_tvl_hyperspeed.py exists" || check_fail "orchestrator_tvl_hyperspeed.py missing"
    [ -f "pool_registry_integrator.py" ] && check_pass "pool_registry_integrator.py exists" || check_fail "pool_registry_integrator.py missing"
    [ -f "advanced_opportunity_detection_Version1.py" ] && check_pass "advanced_opportunity_detection_Version1.py exists" || check_fail "advanced_opportunity_detection_Version1.py missing"
    [ -f "defi_analytics_ml.py" ] && check_pass "defi_analytics_ml.py exists" || check_fail "defi_analytics_ml.py missing"
    [ -f "dual_ai_ml_engine.py" ] && check_pass "dual_ai_ml_engine.py exists" || check_fail "dual_ai_ml_engine.py missing"
    [ -f "arb_request_encoder.py" ] && check_pass "arb_request_encoder.py exists" || check_fail "arb_request_encoder.py missing"
    
    # Check if Python modules can be imported
    check_info "Checking Python module imports..."
    python -c "import sys; sys.path.insert(0, '.'); import config.config" 2>/dev/null && check_pass "config module importable" || check_warn "config module cannot be imported - verify config/config.py exists and has no syntax errors"
}

check_javascript_modules() {
    print_section "5. JavaScript Modules"
    
    # Core JS modules
    [ -f "dex_pool_fetcher.js" ] && check_pass "dex_pool_fetcher.js exists" || check_fail "dex_pool_fetcher.js missing"
    [ -f "sdk_pool_loader.js" ] && check_pass "sdk_pool_loader.js exists" || check_fail "sdk_pool_loader.js missing"
    [ -f "verify-all-modules.js" ] && check_pass "verify-all-modules.js exists" || check_fail "verify-all-modules.js missing"
}

check_dependencies() {
    print_section "6. Dependencies Installation"
    
    # Root node_modules
    if [ -d "node_modules" ]; then
        check_pass "Root node_modules installed"
    else
        check_warn "Root node_modules not found - run: npm install"
    fi
    
    # Backend node_modules
    if [ -d "backend/node_modules" ]; then
        check_pass "Backend node_modules installed"
    else
        check_warn "Backend node_modules not found - run: cd backend && npm install"
    fi
    
    # Frontend node_modules
    if [ -d "frontend/node_modules" ]; then
        check_pass "Frontend node_modules installed"
    else
        check_warn "Frontend node_modules not found - run: cd frontend && npm install"
    fi
    
    # Engine node_modules
    if [ -d "ultra-fast-arbitrage-engine/node_modules" ]; then
        check_pass "Engine node_modules installed"
    else
        check_warn "Engine node_modules not found - run: cd ultra-fast-arbitrage-engine && npm install"
    fi
    
    # Check Python packages
    check_info "Checking Python packages..."
    python -c "import pandas" 2>/dev/null && check_pass "pandas installed" || check_warn "pandas not installed - run: pip3 install -r requirements.txt"
    python -c "import numpy" 2>/dev/null && check_pass "numpy installed" || check_warn "numpy not installed - run: pip3 install -r requirements.txt"
    python -c "import sklearn" 2>/dev/null && check_pass "scikit-learn installed" || check_warn "scikit-learn not installed - run: pip3 install -r requirements.txt"
}

check_configuration() {
    print_section "7. Configuration Files"
    
    # Config directory
    [ -f "config/config.py" ] && check_pass "config/config.py exists" || check_fail "config/config.py missing"
    [ -f "config/addresses.py" ] && check_pass "config/addresses.py exists" || check_fail "config/addresses.py missing"
    [ -f "config/abis.py" ] && check_pass "config/abis.py exists" || check_warn "config/abis.py missing"
    
    # Check for .env files
    if [ -f "ultra-fast-arbitrage-engine/.env" ]; then
        check_pass "Engine .env file exists"
    else
        check_warn "Engine .env file not found (copy from .env.example if needed)"
    fi
}

check_documentation() {
    print_section "8. Documentation"
    
    [ -f "README.md" ] && check_pass "README.md exists" || check_fail "README.md missing"
    [ -f "INSTALL.md" ] && check_pass "INSTALL.md exists" || check_warn "INSTALL.md missing"
    [ -f "QUICKSTART.md" ] && check_pass "QUICKSTART.md exists" || check_warn "QUICKSTART.md missing"
    [ -f "DEPLOYMENT.md" ] && check_pass "DEPLOYMENT.md exists" || check_warn "DEPLOYMENT.md missing"
    [ -f "TESTING.md" ] && check_pass "TESTING.md exists" || check_warn "TESTING.md missing"
    [ -f "SECURITY.md" ] && check_pass "SECURITY.md exists" || check_warn "SECURITY.md missing"
    [ -f "docs/README.md" ] && check_pass "docs/README.md exists" || check_warn "docs/README.md missing"
}

show_summary() {
    print_section "VERIFICATION SUMMARY"
    
    local total_checks=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))
    
    echo ""
    echo -e "${GREEN}Passed:  $CHECKS_PASSED${NC}"
    echo -e "${YELLOW}Warnings: $CHECKS_WARNING${NC}"
    echo -e "${RED}Failed:  $CHECKS_FAILED${NC}"
    echo -e "${CYAN}Total:   $total_checks${NC}"
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✓ SYSTEM VERIFICATION PASSED!${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        
        if [ $CHECKS_WARNING -gt 0 ]; then
            echo -e "${YELLOW}Note: There are $CHECKS_WARNING warnings. These are non-critical but should be addressed.${NC}"
            echo ""
        fi
        
        echo -e "${CYAN}Your system is ready to use!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Configure: Edit config/config.py and config/addresses.py"
        echo "  2. Test: npm run test:comprehensive"
        echo "  3. Deploy: ./deploy.sh"
        echo ""
        
        return 0
    else
        echo -e "${RED}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}✗ SYSTEM VERIFICATION FAILED!${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${YELLOW}Please fix the failed checks and try again.${NC}"
        echo ""
        echo "Common fixes:"
        echo "  - Missing dependencies: ./setup.sh"
        echo "  - Missing files: Check git repository integrity"
        echo "  - Import errors: pip3 install -r requirements.txt"
        echo ""
        
        return 1
    fi
}

# Main execution
main() {
    print_banner
    
    check_runtime_environment
    check_directory_structure
    check_core_files
    check_python_modules
    check_javascript_modules
    check_dependencies
    check_configuration
    check_documentation
    
    show_summary
}

main "$@"
