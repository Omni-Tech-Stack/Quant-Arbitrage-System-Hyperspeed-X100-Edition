#!/bin/bash

# One-Click Deployment Script for Quant Arbitrage System: Hyperspeed X100 Edition
# This script deploys the full system: Frontend + Backend + Dashboard

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🚀 Quant Arbitrage System: Hyperspeed X100 Edition          ║"
    echo "║     One-Click Deployment Script                               ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        missing_deps+=("docker-compose")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Stop and remove existing containers
cleanup_existing() {
    print_step "Cleaning up existing containers..."
    
    # Use docker compose or docker-compose depending on what's available
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    if $DOCKER_COMPOSE ps -q 2>/dev/null | grep -q .; then
        $DOCKER_COMPOSE down 2>/dev/null || true
        print_success "Cleaned up existing containers"
    else
        print_success "No existing containers to clean up"
    fi
}

# Build and start services
deploy_services() {
    print_step "Building Docker images..."
    
    # Determine Docker Compose command
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    # Build images
    $DOCKER_COMPOSE build --no-cache
    print_success "Docker images built successfully"
    
    print_step "Starting services..."
    $DOCKER_COMPOSE up -d
    print_success "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    # Wait for backend
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then
            print_success "Backend API is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend API failed to start"
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    # Wait for frontend
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            print_success "Frontend dashboard is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Frontend dashboard failed to start"
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
}

# Display service status
show_status() {
    print_step "Service status:"
    echo ""
    
    # Determine Docker Compose command
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    $DOCKER_COMPOSE ps
    
    echo ""
    print_success "Deployment completed successfully!"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${GREEN}System Access URLs:${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "  📊 Dashboard:    ${BLUE}http://localhost:3000${NC}"
    echo -e "  🔌 Backend API:  ${BLUE}http://localhost:3001${NC}"
    echo -e "  📋 API Health:   ${BLUE}http://localhost:3001/api/health${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo "  View logs:       $DOCKER_COMPOSE logs -f"
    echo "  Stop system:     $DOCKER_COMPOSE down"
    echo "  Restart system:  $DOCKER_COMPOSE restart"
    echo "  View status:     $DOCKER_COMPOSE ps"
    echo ""
}

# Main deployment flow
main() {
    print_banner
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Please run this script from the project root directory."
        exit 1
    fi
    
    check_prerequisites
    cleanup_existing
    deploy_services
    wait_for_services
    show_status
}

# Run main function
main "$@"
