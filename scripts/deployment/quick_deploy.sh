#!/bin/bash
#
# Quick Deploy Script - Simplified deployment interface
# Provides menu-driven deployment for tab consolidation
# Author: DevOps Team
# Date: 2025-09-29

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║      TAB CONSOLIDATION DEPLOYMENT TOOL       ║"
    echo "║           DevOps Quick Deploy v1.0           ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Menu
show_menu() {
    echo -e "${YELLOW}Please select an option:${NC}"
    echo ""
    echo -e "${GREEN}[1]${NC} 🚀 Setup Feature Flags (First time setup)"
    echo -e "${GREEN}[2]${NC} 📊 Check Current Status"
    echo -e "${GREEN}[3]${NC} 🔄 Run Zero-Downtime Migration"
    echo -e "${GREEN}[4]${NC} 📈 Start Monitoring Dashboard"
    echo -e "${GREEN}[5]${NC} ⚠️  Execute Rollback"
    echo -e "${GREEN}[6]${NC} 🧪 Test Deployment (Dry run)"
    echo -e "${GREEN}[7]${NC} 📋 View Deployment Plan"
    echo -e "${GREEN}[8]${NC} 🗑️  Cleanup Legacy Components"
    echo -e "${GREEN}[9]${NC} 📖 View Logs"
    echo -e "${RED}[0]${NC} Exit"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"

    # Python
    if command -v python3 &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Python 3 installed"
    else
        echo -e "  ${RED}✗${NC} Python 3 not found"
        return 1
    fi

    # Streamlit
    if python3 -c "import streamlit" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Streamlit installed"
    else
        echo -e "  ${YELLOW}⚠${NC} Streamlit not found (app may not be running)"
    fi

    # Required directories
    for dir in src/ui/components config data logs backups; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            echo -e "  ${GREEN}✓${NC} Directory $dir exists"
        else
            echo -e "  ${YELLOW}⚠${NC} Creating directory $dir"
            mkdir -p "$PROJECT_ROOT/$dir"
        fi
    done

    echo ""
    return 0
}

# Setup feature flags
setup_flags() {
    echo -e "${CYAN}Setting up feature flags...${NC}"

    if [ -f "$SCRIPT_DIR/setup_feature_flags.sh" ]; then
        bash "$SCRIPT_DIR/setup_feature_flags.sh"
    else
        echo -e "${RED}Setup script not found${NC}"
        return 1
    fi
}

# Check status
check_status() {
    echo -e "${CYAN}Checking deployment status...${NC}"
    echo ""

    # Feature flags status
    if [ -f "$PROJECT_ROOT/config/deployment_flags.yaml" ]; then
        echo -e "${GREEN}Feature Flags:${NC}"
        python3 <<EOF
import yaml
with open('$PROJECT_ROOT/config/deployment_flags.yaml', 'r') as f:
    config = yaml.safe_load(f)
    tc = config['deployment']['tab_consolidation']
    print(f"  Enabled: {tc['enabled']}")
    print(f"  Phase: {tc['phase']}")
    print(f"  Rollout: {tc.get('features', {}).get('unified_tab', {}).get('rollout_percentage', 0)}%")
EOF
    else
        echo -e "${YELLOW}Feature flags not configured${NC}"
    fi

    echo ""

    # Application status
    echo -e "${GREEN}Application:${NC}"
    if pgrep -f "streamlit run" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} Streamlit running"
    else
        echo -e "  ${RED}✗${NC} Streamlit not running"
    fi

    # Check for unified tab
    if [ -f "$PROJECT_ROOT/src/ui/components/unified_data_management_tab.py" ]; then
        echo -e "  ${GREEN}✓${NC} Unified tab deployed"
    else
        echo -e "  ${YELLOW}○${NC} Unified tab not deployed"
    fi

    # Recent errors
    if [ -f "$PROJECT_ROOT/logs/deployment_errors.json" ]; then
        ERROR_COUNT=$(python3 -c "import json; print(len(json.load(open('$PROJECT_ROOT/logs/deployment_errors.json'))))" 2>/dev/null || echo "0")
        echo -e "  Errors: $ERROR_COUNT"
    fi

    echo ""
}

# Run migration
run_migration() {
    echo -e "${CYAN}Starting zero-downtime migration...${NC}"

    read -p "This will deploy the unified tab. Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled"
        return
    fi

    if [ -f "$SCRIPT_DIR/zero_downtime_migration.sh" ]; then
        bash "$SCRIPT_DIR/zero_downtime_migration.sh"
    else
        echo -e "${RED}Migration script not found${NC}"
        return 1
    fi
}

# Start monitoring
start_monitoring() {
    echo -e "${CYAN}Starting monitoring dashboard...${NC}"

    # Ask for options
    read -p "Enable auto-rollback on errors? (y/n): " -n 1 -r
    echo
    AUTO_ROLLBACK=""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        AUTO_ROLLBACK="--auto-rollback"
    fi

    if [ -f "$SCRIPT_DIR/monitor_deployment.py" ]; then
        python3 "$SCRIPT_DIR/monitor_deployment.py" --interval 10 $AUTO_ROLLBACK
    else
        echo -e "${RED}Monitoring script not found${NC}"
        return 1
    fi
}

# Execute rollback
execute_rollback() {
    echo -e "${YELLOW}⚠️  WARNING: This will revert to previous configuration${NC}"

    read -p "Are you sure you want to rollback? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Rollback cancelled"
        return
    fi

    if [ -f "$SCRIPT_DIR/rollback.sh" ]; then
        bash "$SCRIPT_DIR/rollback.sh"
    else
        echo -e "${RED}Rollback script not found${NC}"
        return 1
    fi
}

# Test deployment
test_deployment() {
    echo -e "${CYAN}Running deployment test (dry run)...${NC}"
    echo ""

    # Check all scripts exist
    SCRIPTS=(
        "setup_feature_flags.sh"
        "zero_downtime_migration.sh"
        "rollback.sh"
        "monitor_deployment.py"
    )

    ALL_FOUND=true
    for script in "${SCRIPTS[@]}"; do
        if [ -f "$SCRIPT_DIR/$script" ]; then
            echo -e "  ${GREEN}✓${NC} $script found"
        else
            echo -e "  ${RED}✗${NC} $script missing"
            ALL_FOUND=false
        fi
    done

    echo ""

    if $ALL_FOUND; then
        echo -e "${GREEN}All deployment scripts are ready${NC}"

        # Test Python imports
        echo -e "\n${BLUE}Testing Python environment...${NC}"
        python3 <<EOF
import sys
sys.path.append('$PROJECT_ROOT/src')

try:
    from ui.components.export_tab import ExportTab
    print("  ✓ Export tab importable")
except:
    print("  ✗ Export tab import failed")

try:
    from ui.components.management_tab import ManagementTab
    print("  ✓ Management tab importable")
except:
    print("  ✗ Management tab import failed")

try:
    import yaml
    print("  ✓ PyYAML available")
except:
    print("  ✗ PyYAML not installed")
EOF

    else
        echo -e "${RED}Some deployment scripts are missing${NC}"
    fi

    echo ""
}

# View deployment plan
view_plan() {
    PLAN_FILE="$PROJECT_ROOT/docs/deployment/TAB_CONSOLIDATION_DEPLOYMENT_PLAN.md"

    if [ -f "$PLAN_FILE" ]; then
        # Use less if available, otherwise cat
        if command -v less &> /dev/null; then
            less "$PLAN_FILE"
        else
            cat "$PLAN_FILE"
        fi
    else
        echo -e "${YELLOW}Deployment plan not found${NC}"
    fi
}

# Cleanup legacy
cleanup_legacy() {
    echo -e "${YELLOW}⚠️  This will remove legacy tab files${NC}"
    echo "Only do this after confirming the unified tab works correctly!"
    echo ""

    read -p "Remove legacy tabs? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        return
    fi

    # Archive legacy files
    ARCHIVE_DIR="$PROJECT_ROOT/backups/legacy_archive_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$ARCHIVE_DIR"

    for file in export_tab.py management_tab.py; do
        if [ -f "$PROJECT_ROOT/src/ui/components/$file" ]; then
            mv "$PROJECT_ROOT/src/ui/components/$file" "$ARCHIVE_DIR/"
            echo "  Archived $file"
        fi
    done

    echo -e "${GREEN}Legacy files archived to: $ARCHIVE_DIR${NC}"
}

# View logs
view_logs() {
    echo -e "${CYAN}Available logs:${NC}"
    echo ""
    echo "[1] Migration logs"
    echo "[2] Rollback logs"
    echo "[3] Deployment metrics"
    echo "[4] Deployment errors"
    echo "[5] Deployment alerts"
    echo "[0] Back to main menu"
    echo ""

    read -p "Select log to view: " log_choice

    case $log_choice in
        1)
            LATEST_LOG=$(ls -t "$PROJECT_ROOT"/logs/migration_*.log 2>/dev/null | head -1)
            if [ -n "$LATEST_LOG" ]; then
                less "$LATEST_LOG"
            else
                echo "No migration logs found"
            fi
            ;;
        2)
            LATEST_LOG=$(ls -t "$PROJECT_ROOT"/logs/rollback_*.log 2>/dev/null | head -1)
            if [ -n "$LATEST_LOG" ]; then
                less "$LATEST_LOG"
            else
                echo "No rollback logs found"
            fi
            ;;
        3)
            if [ -f "$PROJECT_ROOT/logs/deployment_metrics.json" ]; then
                python3 -m json.tool "$PROJECT_ROOT/logs/deployment_metrics.json" | less
            else
                echo "No metrics found"
            fi
            ;;
        4)
            if [ -f "$PROJECT_ROOT/logs/deployment_errors.json" ]; then
                python3 -m json.tool "$PROJECT_ROOT/logs/deployment_errors.json" | less
            else
                echo "No errors logged"
            fi
            ;;
        5)
            if [ -f "$PROJECT_ROOT/logs/deployment_alerts.json" ]; then
                python3 -m json.tool "$PROJECT_ROOT/logs/deployment_alerts.json" | less
            else
                echo "No alerts logged"
            fi
            ;;
        0)
            return
            ;;
        *)
            echo "Invalid selection"
            ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
main() {
    cd "$PROJECT_ROOT"

    while true; do
        show_banner

        # Quick status at top
        if [ -f "$PROJECT_ROOT/config/deployment_flags.yaml" ]; then
            STATUS=$(python3 -c "
import yaml
with open('$PROJECT_ROOT/config/deployment_flags.yaml', 'r') as f:
    config = yaml.safe_load(f)
    tc = config['deployment']['tab_consolidation']
    if tc['enabled']:
        print('🟢 UNIFIED TAB ACTIVE')
    else:
        print('🔴 LEGACY TABS ACTIVE')
" 2>/dev/null || echo "⚪ STATUS UNKNOWN")

            echo -e "${MAGENTA}Current Status: $STATUS${NC}"
            echo ""
        fi

        show_menu

        read -p "Enter your choice: " choice

        case $choice in
            1)
                setup_flags
                ;;
            2)
                check_status
                ;;
            3)
                run_migration
                ;;
            4)
                start_monitoring
                ;;
            5)
                execute_rollback
                ;;
            6)
                test_deployment
                ;;
            7)
                view_plan
                ;;
            8)
                cleanup_legacy
                ;;
            9)
                view_logs
                ;;
            0)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check prerequisites on start
if ! check_prerequisites; then
    echo -e "${RED}Prerequisites check failed${NC}"
    exit 1
fi

# Run main loop
main