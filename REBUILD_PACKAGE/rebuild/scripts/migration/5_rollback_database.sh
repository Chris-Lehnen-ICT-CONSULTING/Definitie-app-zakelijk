#!/bin/bash
#
# Emergency Database Rollback Script
#
# This script performs emergency rollback of database migration by restoring
# the backup and verifying integrity. Can be executed in < 5 minutes.
#
# Usage:
#   bash scripts/migration/5_rollback_database.sh --test
#   bash scripts/migration/5_rollback_database.sh --execute
#   bash scripts/migration/5_rollback_database.sh --backup /path/to/backup.db
#
# Example:
#   $ bash scripts/migration/5_rollback_database.sh --test
#   🔍 TEST MODE - No changes will be made
#   ✅ Backup file found
#   ✅ Backup is readable
#   ✅ Backup integrity check passed
#   ✅ Test complete - rollback procedure is ready
#
#   $ bash scripts/migration/5_rollback_database.sh --execute
#   🚨 ROLLBACK INITIATED
#   ✅ Application stopped
#   ✅ Backup restored
#   ✅ Integrity verified
#   ✅ Rollback complete (elapsed: 47 seconds)

set -euo pipefail

# Configuration
DB_PATH="${DB_PATH:-data/definities.db}"
BACKUP_PATTERN="${BACKUP_PATTERN:-data/definities.db.backup.*}"
LOG_DIR="logs/migration"
LOG_FILE="$LOG_DIR/rollback_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "$LOG_DIR"

# Logging functions
log_info() {
    echo -e "${GREEN}✅${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\n${GREEN}[$1]${NC} $2" | tee -a "$LOG_FILE"
}

# Find most recent backup
find_backup() {
    local latest_backup=$(ls -t $BACKUP_PATTERN 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup found matching pattern: $BACKUP_PATTERN"
        return 1
    fi

    echo "$latest_backup"
    return 0
}

# Test backup integrity
test_backup_integrity() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    if [ ! -r "$backup_file" ]; then
        log_error "Backup file not readable: $backup_file"
        return 1
    fi

    # Test SQLite integrity
    local integrity_result=$(sqlite3 "$backup_file" "PRAGMA integrity_check;" 2>&1)

    if [ "$integrity_result" != "ok" ]; then
        log_error "Backup integrity check failed: $integrity_result"
        return 1
    fi

    # Test record count
    local record_count=$(sqlite3 "$backup_file" "SELECT COUNT(*) FROM definities;" 2>&1)

    if [ $? -ne 0 ]; then
        log_error "Cannot query backup database: $record_count"
        return 1
    fi

    log_info "Backup integrity verified ($record_count definitions)"
    return 0
}

# Stop application
stop_application() {
    log_step "1/5" "Stopping application..."

    # Try to stop Streamlit
    pkill -f "streamlit run" 2>/dev/null || true

    # Wait for process to stop
    sleep 2

    # Verify stopped
    if pgrep -f "streamlit run" > /dev/null; then
        log_warning "Streamlit still running, forcing kill..."
        pkill -9 -f "streamlit run" 2>/dev/null || true
        sleep 1
    fi

    log_info "Application stopped"
}

# Create safety backup of current state
create_safety_backup() {
    log_step "2/5" "Creating safety backup of current state..."

    if [ -f "$DB_PATH" ]; then
        local safety_backup="${DB_PATH}.pre-rollback.$(date +%Y%m%d_%H%M%S)"
        cp "$DB_PATH" "$safety_backup"
        log_info "Safety backup created: $safety_backup"
    else
        log_warning "Current database not found, skipping safety backup"
    fi
}

# Restore backup
restore_backup() {
    local backup_file="$1"

    log_step "3/5" "Restoring backup..."

    cp "$backup_file" "$DB_PATH"

    log_info "Backup restored: $backup_file → $DB_PATH"
}

# Verify restored database
verify_restored() {
    log_step "4/5" "Verifying restored database..."

    # Check integrity
    local integrity_result=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")

    if [ "$integrity_result" != "ok" ]; then
        log_error "Restored database integrity check failed: $integrity_result"
        return 1
    fi

    # Check record count
    local record_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM definities;")
    log_info "Restored database verified ($record_count definitions)"

    # Check sample records
    local sample=$(sqlite3 "$DB_PATH" "SELECT begrip FROM definities LIMIT 1;")
    if [ -z "$sample" ]; then
        log_error "Cannot read from restored database"
        return 1
    fi

    log_info "Sample record: $sample"

    return 0
}

# Restart application
restart_application() {
    log_step "5/5" "Restarting application..."

    # Start application in background
    bash scripts/run_app.sh > /dev/null 2>&1 &

    # Wait for startup
    sleep 5

    # Verify started
    if pgrep -f "streamlit run" > /dev/null; then
        log_info "Application restarted successfully"
    else
        log_warning "Application did not start automatically"
        log_warning "Start manually: bash scripts/run_app.sh"
    fi
}

# Test mode - verify rollback readiness
test_rollback() {
    local backup_file="$1"

    echo "="*60
    echo "🔍 TEST MODE - No changes will be made"
    echo "="*60

    log_info "Testing rollback procedure..."

    # Test 1: Backup exists
    if [ -f "$backup_file" ]; then
        log_info "Backup file found: $backup_file"
    else
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    # Test 2: Backup readable
    if [ -r "$backup_file" ]; then
        log_info "Backup file is readable"
    else
        log_error "Backup file is not readable"
        return 1
    fi

    # Test 3: Backup integrity
    if test_backup_integrity "$backup_file"; then
        log_info "Backup integrity check passed"
    else
        log_error "Backup integrity check failed"
        return 1
    fi

    # Test 4: Estimate time
    local start_time=$(date +%s)
    cp "$backup_file" "/tmp/rollback_test.db" 2>/dev/null
    sqlite3 "/tmp/rollback_test.db" "PRAGMA integrity_check;" > /dev/null 2>&1
    rm "/tmp/rollback_test.db" 2>/dev/null
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))

    log_info "Estimated rollback time: ~${elapsed} seconds"

    if [ $elapsed -gt 300 ]; then
        log_warning "Rollback may exceed 5-minute target"
    fi

    echo "="*60
    log_info "Test complete - rollback procedure is ready"
    echo "="*60

    return 0
}

# Execute rollback
execute_rollback() {
    local backup_file="$1"
    local start_time=$(date +%s)

    echo "="*60
    echo "🚨 ROLLBACK INITIATED"
    echo "="*60
    echo "Backup: $backup_file"
    echo "Target: $DB_PATH"
    echo "Started: $(date)"
    echo "="*60

    # Execute rollback steps
    stop_application
    create_safety_backup
    restore_backup "$backup_file"

    if ! verify_restored; then
        log_error "ROLLBACK FAILED - Verification failed"
        return 1
    fi

    restart_application

    # Calculate elapsed time
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))

    echo "="*60
    log_info "ROLLBACK COMPLETE"
    echo "="*60
    echo "Elapsed time: ${elapsed} seconds"
    echo "Log file: $LOG_FILE"

    if [ $elapsed -gt 300 ]; then
        log_warning "Rollback exceeded 5-minute target (${elapsed}s)"
    fi

    return 0
}

# Main script
main() {
    local mode=""
    local backup_file=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test)
                mode="test"
                shift
                ;;
            --execute)
                mode="execute"
                shift
                ;;
            --backup)
                backup_file="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--test|--execute] [--backup /path/to/backup.db]"
                exit 1
                ;;
        esac
    done

    # Validate mode
    if [ -z "$mode" ]; then
        log_error "Must specify --test or --execute"
        echo "Usage: $0 [--test|--execute] [--backup /path/to/backup.db]"
        exit 1
    fi

    # Find backup if not specified
    if [ -z "$backup_file" ]; then
        backup_file=$(find_backup)
        if [ $? -ne 0 ]; then
            exit 1
        fi
    fi

    # Execute mode
    if [ "$mode" = "test" ]; then
        test_rollback "$backup_file"
        exit $?
    elif [ "$mode" = "execute" ]; then
        # Confirm execution
        echo "⚠️  WARNING: This will restore the database backup"
        echo "Backup: $backup_file"
        echo "Target: $DB_PATH"
        read -p "Continue? (yes/no): " confirm

        if [ "$confirm" != "yes" ]; then
            log_info "Rollback cancelled"
            exit 0
        fi

        execute_rollback "$backup_file"
        exit $?
    fi
}

# Run main
main "$@"
