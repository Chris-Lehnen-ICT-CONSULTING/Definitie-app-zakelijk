#!/bin/bash
# BMAD Agent Review Command
# Voor gebruik binnen BMAD agents zoals *qa of *dev

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
MAX_ITERATIONS="${MAX_ITERATIONS:-5}"
REVIEW_MODE="${1:-check}"  # check or fix

# Create .bmad directory if needed
mkdir -p "$PROJECT_ROOT/.bmad"

echo -e "${BLUE}🤖 BMAD Agent Code Review${NC}"
echo "Mode: $REVIEW_MODE"
echo "Max iterations: $MAX_ITERATIONS"

# Function to run Python AI reviewer
run_python_review() {
    local iteration=$1
    echo -e "\n${BLUE}📍 Iteration $iteration/$MAX_ITERATIONS${NC}"
    
    # Run the Python AI code reviewer
    python scripts/ai_code_reviewer.py \
        --max-iterations 1 \
        --project-root "$PROJECT_ROOT" \
        --ai-agent "${BMAD_AGENT_NAME:-bmad-agent}" \
        > "$PROJECT_ROOT/.bmad/review-output.txt" 2>&1
    
    return $?
}

# Function to parse review results
parse_review_results() {
    local output_file="$PROJECT_ROOT/.bmad/review-output.txt"
    local instructions_file="$PROJECT_ROOT/.bmad/agent-fix-instructions.md"
    
    # Extract issues from review output
    echo "# 🔧 Code Fix Instructions for BMAD Agent" > "$instructions_file"
    echo "" >> "$instructions_file"
    echo "## Issues Found:" >> "$instructions_file"
    echo "" >> "$instructions_file"
    
    # Parse BLOCKING issues
    if grep -q "BLOCKING" "$output_file"; then
        echo "### 🔴 BLOCKING Issues (Must Fix)" >> "$instructions_file"
        grep -A 5 "BLOCKING" "$output_file" >> "$instructions_file"
        echo "" >> "$instructions_file"
    fi
    
    # Parse IMPORTANT issues
    if grep -q "IMPORTANT" "$output_file"; then
        echo "### 🟡 IMPORTANT Issues (Should Fix)" >> "$instructions_file"
        grep -A 3 "IMPORTANT" "$output_file" | head -20 >> "$instructions_file"
        echo "" >> "$instructions_file"
    fi
    
    # Add specific fix instructions
    echo "## Fix Instructions:" >> "$instructions_file"
    echo "" >> "$instructions_file"
    
    # SQL Injection fixes
    if grep -q "SQL injection" "$output_file"; then
        echo "### SQL Injection Fixes:" >> "$instructions_file"
        echo '```python' >> "$instructions_file"
        echo '# Replace f-strings in SQL:' >> "$instructions_file"
        echo '# BAD:  query = f"SELECT * FROM table WHERE id = {user_id}"' >> "$instructions_file"
        echo '# GOOD: cursor.execute("SELECT * FROM table WHERE id = ?", (user_id,))' >> "$instructions_file"
        echo '```' >> "$instructions_file"
        echo "" >> "$instructions_file"
    fi
    
    # Import fixes
    if grep -q "F401" "$output_file"; then
        echo "### Unused Import Fixes:" >> "$instructions_file"
        echo "Remove the following unused imports:" >> "$instructions_file"
        grep "F401" "$output_file" | awk '{print "- " $NF}' >> "$instructions_file"
        echo "" >> "$instructions_file"
    fi
    
    # Type error fixes
    if grep -q "mypy" "$output_file"; then
        echo "### Type Error Fixes:" >> "$instructions_file"
        echo "Add type hints to the following functions:" >> "$instructions_file"
        grep -A 2 "Type error" "$output_file" >> "$instructions_file"
        echo "" >> "$instructions_file"
    fi
}

# Main review loop
iteration=0
all_passed=false

while [ $iteration -lt $MAX_ITERATIONS ]; do
    iteration=$((iteration + 1))
    
    # Run review
    if run_python_review $iteration; then
        echo -e "${GREEN}✅ All checks passed!${NC}"
        all_passed=true
        break
    else
        echo -e "${YELLOW}⚠️  Issues found${NC}"
        
        # Parse results and create fix instructions
        parse_review_results
        
        if [ "$REVIEW_MODE" = "check" ]; then
            echo -e "${YELLOW}📝 Fix instructions written to: .bmad/agent-fix-instructions.md${NC}"
            break
        else
            # In fix mode, wait for agent to apply fixes
            echo -e "${BLUE}🔧 Applying fixes...${NC}"
            
            # For BMAD agents: They will read the instructions and fix
            # For now, we just continue to next iteration
            sleep 2
        fi
    fi
done

# Generate final report
if [ "$all_passed" = true ]; then
    echo -e "\n${GREEN}✅ Code Review PASSED${NC}"
    echo "All quality checks passed after $iteration iteration(s)"
    exit 0
else
    echo -e "\n${RED}❌ Code Review FAILED${NC}"
    echo "Issues remain after $iteration iteration(s)"
    echo "See .bmad/agent-fix-instructions.md for details"
    exit 1
fi