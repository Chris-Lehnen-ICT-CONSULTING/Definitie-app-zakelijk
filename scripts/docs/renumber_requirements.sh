#!/bin/bash

# Script om REQ bestanden te hernummeren naar oplopende volgorde
# REQ-000.md (template) blijft ongewijzigd

cd docs/requirements/

# Functie om het ID in het bestand ook bij te werken
update_file_id() {
    local old_id=$1
    local new_id=$2
    local file=$3

    # Update de id in de frontmatter
    sed -i '' "s/id: REQ-${old_id}/id: REQ-${new_id}/g" "$file"
    # Update de title regel
    sed -i '' "s/Requirement REQ-${old_id}:/Requirement REQ-${new_id}:/g" "$file"
}

echo "Starting renumbering process..."

# Eerst alle bestanden hernoemen naar temp namen om conflicten te voorkomen
echo "Step 1: Moving to temporary names..."
mv REQ-051.md REQ-TEMP-008.md 2>/dev/null && echo "REQ-051 → TEMP-008"
mv REQ-052.md REQ-TEMP-009.md 2>/dev/null && echo "REQ-052 → TEMP-009"
mv REQ-053.md REQ-TEMP-010.md 2>/dev/null && echo "REQ-053 → TEMP-010"
mv REQ-054.md REQ-TEMP-011.md 2>/dev/null && echo "REQ-054 → TEMP-011"
mv REQ-055.md REQ-TEMP-012.md 2>/dev/null && echo "REQ-055 → TEMP-012"
mv REQ-151.md REQ-TEMP-013.md 2>/dev/null && echo "REQ-151 → TEMP-013"
mv REQ-152.md REQ-TEMP-014.md 2>/dev/null && echo "REQ-152 → TEMP-014"
mv REQ-153.md REQ-TEMP-015.md 2>/dev/null && echo "REQ-153 → TEMP-015"
mv REQ-154.md REQ-TEMP-016.md 2>/dev/null && echo "REQ-154 → TEMP-016"
mv REQ-155.md REQ-TEMP-017.md 2>/dev/null && echo "REQ-155 → TEMP-017"
mv REQ-201.md REQ-TEMP-018.md 2>/dev/null && echo "REQ-201 → TEMP-018"
mv REQ-202.md REQ-TEMP-019.md 2>/dev/null && echo "REQ-202 → TEMP-019"
mv REQ-203.md REQ-TEMP-020.md 2>/dev/null && echo "REQ-203 → TEMP-020"
mv REQ-204.md REQ-TEMP-021.md 2>/dev/null && echo "REQ-204 → TEMP-021"
mv REQ-205.md REQ-TEMP-022.md 2>/dev/null && echo "REQ-205 → TEMP-022"

echo "Step 2: Renaming to final names and updating content..."

# Nu hernoemen naar definitieve namen EN update de content
if [ -f REQ-TEMP-008.md ]; then
    update_file_id "051" "008" "REQ-TEMP-008.md"
    mv REQ-TEMP-008.md REQ-008.md
    echo "Created REQ-008.md (was REQ-051)"
fi

if [ -f REQ-TEMP-009.md ]; then
    update_file_id "052" "009" "REQ-TEMP-009.md"
    mv REQ-TEMP-009.md REQ-009.md
    echo "Created REQ-009.md (was REQ-052)"
fi

if [ -f REQ-TEMP-010.md ]; then
    update_file_id "053" "010" "REQ-TEMP-010.md"
    mv REQ-TEMP-010.md REQ-010.md
    echo "Created REQ-010.md (was REQ-053)"
fi

if [ -f REQ-TEMP-011.md ]; then
    update_file_id "054" "011" "REQ-TEMP-011.md"
    mv REQ-TEMP-011.md REQ-011.md
    echo "Created REQ-011.md (was REQ-054)"
fi

if [ -f REQ-TEMP-012.md ]; then
    update_file_id "055" "012" "REQ-TEMP-012.md"
    mv REQ-TEMP-012.md REQ-012.md
    echo "Created REQ-012.md (was REQ-055)"
fi

if [ -f REQ-TEMP-013.md ]; then
    update_file_id "151" "013" "REQ-TEMP-013.md"
    mv REQ-TEMP-013.md REQ-013.md
    echo "Created REQ-013.md (was REQ-151)"
fi

if [ -f REQ-TEMP-014.md ]; then
    update_file_id "152" "014" "REQ-TEMP-014.md"
    mv REQ-TEMP-014.md REQ-014.md
    echo "Created REQ-014.md (was REQ-152)"
fi

if [ -f REQ-TEMP-015.md ]; then
    update_file_id "153" "015" "REQ-TEMP-015.md"
    mv REQ-TEMP-015.md REQ-015.md
    echo "Created REQ-015.md (was REQ-153)"
fi

if [ -f REQ-TEMP-016.md ]; then
    update_file_id "154" "016" "REQ-TEMP-016.md"
    mv REQ-TEMP-016.md REQ-016.md
    echo "Created REQ-016.md (was REQ-154)"
fi

if [ -f REQ-TEMP-017.md ]; then
    update_file_id "155" "017" "REQ-TEMP-017.md"
    mv REQ-TEMP-017.md REQ-017.md
    echo "Created REQ-017.md (was REQ-155)"
fi

if [ -f REQ-TEMP-018.md ]; then
    update_file_id "201" "018" "REQ-TEMP-018.md"
    mv REQ-TEMP-018.md REQ-018.md
    echo "Created REQ-018.md (was REQ-201)"
fi

if [ -f REQ-TEMP-019.md ]; then
    update_file_id "202" "019" "REQ-TEMP-019.md"
    mv REQ-TEMP-019.md REQ-019.md
    echo "Created REQ-019.md (was REQ-202)"
fi

if [ -f REQ-TEMP-020.md ]; then
    update_file_id "203" "020" "REQ-TEMP-020.md"
    mv REQ-TEMP-020.md REQ-020.md
    echo "Created REQ-020.md (was REQ-203)"
fi

if [ -f REQ-TEMP-021.md ]; then
    update_file_id "204" "021" "REQ-TEMP-021.md"
    mv REQ-TEMP-021.md REQ-021.md
    echo "Created REQ-021.md (was REQ-204)"
fi

if [ -f REQ-TEMP-022.md ]; then
    update_file_id "205" "022" "REQ-TEMP-022.md"
    mv REQ-TEMP-022.md REQ-022.md
    echo "Created REQ-022.md (was REQ-205)"
fi

echo "Step 3: Listing final result..."
echo ""
echo "Current REQ files:"
ls REQ-*.md | sort

echo ""
echo "Renumbering complete!"
