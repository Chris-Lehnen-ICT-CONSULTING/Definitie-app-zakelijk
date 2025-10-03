#!/bin/bash
set -euo pipefail

# ==============================================
# MVP Validation Test Script
# ==============================================
# Tests basic functionality and critical paths
# for the DefinitieAgent MVP
# ==============================================

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
readonly HEALTH_CHECK_TIMEOUT=60
readonly STREAMLIT_PORT=8501

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

test_passed() {
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
    log_success "$1"
}

test_failed() {
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
    log_error "$1"
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local timeout=$3
    local elapsed=0

    log_info "Waiting for $service_name to be ready..."

    while [ $elapsed -lt $timeout ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        sleep 2
        ((elapsed+=2))
    done

    log_error "$service_name failed to start within ${timeout}s"
    return 1
}

# ==============================================================================
# Test Functions
# ==============================================================================

test_docker_available() {
    print_header "Test: Docker Availability"

    if command -v docker &> /dev/null; then
        test_passed "Docker is installed"
    else
        test_failed "Docker is not installed"
        return 1
    fi

    if docker info &> /dev/null; then
        test_passed "Docker daemon is running"
    else
        test_failed "Docker daemon is not running"
        return 1
    fi
}

test_docker_compose_available() {
    print_header "Test: Docker Compose Availability"

    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        test_passed "Docker Compose is installed"
    else
        test_failed "Docker Compose is not installed"
        return 1
    fi
}

test_docker_compose_config() {
    print_header "Test: Docker Compose Configuration"

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        test_failed "docker-compose.yml not found"
        return 1
    fi

    if docker-compose -f "$DOCKER_COMPOSE_FILE" config &> /dev/null; then
        test_passed "docker-compose.yml is valid"
    else
        test_failed "docker-compose.yml is invalid"
        return 1
    fi
}

test_environment_file() {
    print_header "Test: Environment Configuration"

    if [ -f "${PROJECT_ROOT}/.env" ]; then
        test_passed ".env file exists"

        # Check for required variables
        if grep -q "OPENAI_API_KEY" "${PROJECT_ROOT}/.env"; then
            test_passed "OPENAI_API_KEY is configured"
        else
            test_failed "OPENAI_API_KEY is not configured"
        fi
    else
        test_failed ".env file not found"
        log_warning "Copy .env.example to .env and configure"
        return 1
    fi
}

start_services() {
    print_header "Starting Services"

    cd "$PROJECT_ROOT"

    log_info "Starting Docker containers..."
    if docker-compose up -d; then
        test_passed "Services started successfully"
    else
        test_failed "Failed to start services"
        return 1
    fi

    # Wait for services to be ready
    if wait_for_service "http://localhost:${STREAMLIT_PORT}/_stcore/health" "Streamlit" "$HEALTH_CHECK_TIMEOUT"; then
        test_passed "Streamlit health check passed"
    else
        test_failed "Streamlit health check failed"
        docker-compose logs streamlit
        return 1
    fi
}

test_streamlit_ui() {
    print_header "Test: Streamlit UI"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${STREAMLIT_PORT}")

    if [ "$response" = "200" ]; then
        test_passed "Streamlit UI is accessible (HTTP $response)"
    else
        test_failed "Streamlit UI returned HTTP $response"
        return 1
    fi
}

test_redis_connectivity() {
    print_header "Test: Redis Connectivity"

    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        test_passed "Redis is responding"
    else
        test_failed "Redis is not responding"
        return 1
    fi
}

test_database_exists() {
    print_header "Test: Database File"

    if [ -f "${PROJECT_ROOT}/data/definities.db" ]; then
        test_passed "Database file exists"
    else
        log_warning "Database file not found (will be created on first use)"
    fi
}

test_logs_directory() {
    print_header "Test: Logs Directory"

    if [ -d "${PROJECT_ROOT}/logs" ]; then
        test_passed "Logs directory exists"
    else
        log_warning "Logs directory not found (will be created on first use)"
    fi
}

stop_services() {
    print_header "Stopping Services"

    cd "$PROJECT_ROOT"

    log_info "Stopping Docker containers..."
    if docker-compose down; then
        test_passed "Services stopped successfully"
    else
        test_failed "Failed to stop services"
        return 1
    fi
}

# ==============================================================================
# Test Execution
# ==============================================================================

run_smoke_tests() {
    print_header "MVP VALIDATION - SMOKE TESTS"

    # Pre-flight checks
    test_docker_available || exit 1
    test_docker_compose_available || exit 1
    test_docker_compose_config || exit 1
    test_environment_file || exit 1

    # Service tests
    test_database_exists
    test_logs_directory

    # Start and test services
    start_services || exit 1
    test_streamlit_ui
    test_redis_connectivity

    # Cleanup
    stop_services
}

print_summary() {
    print_header "TEST SUMMARY"

    echo "Tests Run:    $TESTS_RUN"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        log_success "All tests passed! MVP is ready."
        echo ""
        return 0
    else
        echo ""
        log_error "Some tests failed. Please review the output above."
        echo ""
        return 1
    fi
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    # Parse arguments
    local cleanup_on_exit=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cleanup)
                cleanup_on_exit=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --no-cleanup    Don't stop services after tests"
                echo "  --help          Show this help message"
                echo ""
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run tests
    run_smoke_tests

    # Print summary and exit
    if print_summary; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
