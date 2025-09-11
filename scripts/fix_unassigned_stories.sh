#!/bin/bash

# Script om unassigned user stories aan de juiste EPICs toe te wijzen

echo "🔧 Fixing unassigned user stories..."

# US-032: Context Window Optimization -> EPIC-007 (Performance)
echo "Moving US-032 to EPIC-007..."
sed -i '' 's/^epic:.*/epic: EPIC-007/' "docs/backlog/UNASSIGNED/User Stories/US-032/US-032.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-032" "docs/backlog/EPIC-007/User Stories/" 2>/dev/null

# US-033: V1 to V2 Migration -> EPIC-007 (Performance)
echo "Moving US-033 to EPIC-007..."
sed -i '' 's/^epic:.*/epic: EPIC-007/' "docs/backlog/UNASSIGNED/User Stories/US-033/US-033.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-033" "docs/backlog/EPIC-007/User Stories/" 2>/dev/null

# US-034: Service Container Optimization -> EPIC-007 (Performance)
echo "Moving US-034 to EPIC-007..."
sed -i '' 's/^epic:.*/epic: EPIC-007/' "docs/backlog/UNASSIGNED/User Stories/US-034/US-034.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-034" "docs/backlog/EPIC-007/User Stories/" 2>/dev/null

# US-035: Multi-definition Batch Processing -> EPIC-009 (Advanced Features)
echo "Moving US-035 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-035/US-035.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-035" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-036: Version Control Integration -> EPIC-009 (Advanced Features)
echo "Moving US-036 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-036/US-036.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-036" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-037: Collaborative Editing -> EPIC-009 (Advanced Features)
echo "Moving US-037 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-037/US-037.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-037" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-038: FastAPI REST Endpoints -> EPIC-009 (Advanced Features)
echo "Moving US-038 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-038/US-038.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-038" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-039: PostgreSQL Migration -> EPIC-009 (Advanced Features)
echo "Moving US-039 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-039/US-039.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-039" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-040: Multi-tenant Architecture -> EPIC-009 (Advanced Features)
echo "Moving US-040 to EPIC-009..."
sed -i '' 's/^epic:.*/epic: EPIC-009/' "docs/backlog/UNASSIGNED/User Stories/US-040/US-040.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-040" "docs/backlog/EPIC-009/User Stories/" 2>/dev/null

# US-044: Context Type Validation -> EPIC-010 (Context Flow)
echo "Moving US-044 to EPIC-010..."
sed -i '' 's/^epic:.*/epic: EPIC-010/' "docs/backlog/UNASSIGNED/User Stories/US-044/US-044.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-044" "docs/backlog/EPIC-010/User Stories/" 2>/dev/null

# US-045: Context Traceability -> EPIC-010 (Context Flow)
echo "Moving US-045 to EPIC-010..."
sed -i '' 's/^epic:.*/epic: EPIC-010/' "docs/backlog/UNASSIGNED/User Stories/US-045/US-045.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-045" "docs/backlog/EPIC-010/User Stories/" 2>/dev/null

# US-046: E2E Context Tests -> EPIC-010 (Context Flow)
echo "Moving US-046 to EPIC-010..."
sed -i '' 's/^epic:.*/epic: EPIC-010/' "docs/backlog/UNASSIGNED/User Stories/US-046/US-046.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-046" "docs/backlog/EPIC-010/User Stories/" 2>/dev/null

# US-047: Context Caching -> EPIC-010 (Context Flow)
echo "Moving US-047 to EPIC-010..."
sed -i '' 's/^epic:.*/epic: EPIC-010/' "docs/backlog/UNASSIGNED/User Stories/US-047/US-047.md" 2>/dev/null
mv "docs/backlog/UNASSIGNED/User Stories/US-047" "docs/backlog/EPIC-010/User Stories/" 2>/dev/null

# Remove empty UNASSIGNED directory if empty
rmdir "docs/backlog/UNASSIGNED/User Stories" 2>/dev/null
rmdir "docs/backlog/UNASSIGNED" 2>/dev/null

echo "✅ All unassigned stories have been assigned to appropriate EPICs!"