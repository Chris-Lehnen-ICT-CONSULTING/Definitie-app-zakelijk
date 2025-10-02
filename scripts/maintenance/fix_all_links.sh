#!/bin/bash

# Script om alle links naar de nieuwe backlog structuur te updaten

echo "🔗 Fixing all backlog links in documentation..."

# Maak eerst een mapping van alle user stories naar hun EPICs
declare -A US_TO_EPIC

# Loop door alle EPIC directories en bouw de mapping
for epic_dir in docs/backlog/EPIC-*/; do
  if [ -d "$epic_dir" ]; then
    epic_name=$(basename "$epic_dir")

    # Loop door alle user stories in deze EPIC
    for us_dir in "$epic_dir"/User\ Stories/US-*/; do
      if [ -d "$us_dir" ]; then
        us_name=$(basename "$us_dir")
        US_TO_EPIC[$us_name]=$epic_name
        echo "  Mapped $us_name -> $epic_name"
      fi
    done
  fi
done

echo "📝 Updating links in all markdown files..."

# Function to fix links in a file
fix_links_in_file() {
  local file="$1"
  local temp_file="${file}.tmp"

  cp "$file" "$temp_file"

  # Fix EPIC links (from ../epics/EPIC-XXX.md to ../EPIC-XXX/EPIC-XXX.md)
  sed -i '' 's|\.\./epics/\(EPIC-[0-9]*\)[-a-z]*\.md|../\1/\1.md|g' "$temp_file"
  sed -i '' 's|\.\./\.\./epics/\(EPIC-[0-9]*\)[-a-z]*\.md|../../\1/\1.md|g' "$temp_file"
  sed -i '' 's|docs/backlog/epics/\(EPIC-[0-9]*\)[-a-z]*\.md|docs/backlog/\1/\1.md|g' "$temp_file"

  # Fix Story links - we need to know which EPIC each story belongs to
  # This is more complex and needs the mapping

  # For each US in our mapping, replace the old path with new path
  for us_name in "${!US_TO_EPIC[@]}"; do
    epic_name="${US_TO_EPIC[$us_name]}"

    # Various patterns to match
    # Pattern: ../stories/US-XXX.md -> ../EPIC-XXX/User Stories/US-XXX/US-XXX.md
    sed -i '' "s|\.\./stories/${us_name}\.md|../${epic_name}/User Stories/${us_name}/${us_name}.md|g" "$temp_file"

    # Pattern: ../../stories/US-XXX.md -> ../../EPIC-XXX/User Stories/US-XXX/US-XXX.md
    sed -i '' "s|\.\./\.\./stories/${us_name}\.md|../../${epic_name}/User Stories/${us_name}/${us_name}.md|g" "$temp_file"

    # Pattern: docs/backlog/stories/US-XXX.md -> docs/backlog/EPIC-XXX/User Stories/US-XXX/US-XXX.md
    sed -i '' "s|docs/backlog/stories/${us_name}\.md|docs/backlog/${epic_name}/User Stories/${us_name}/${us_name}.md|g" "$temp_file"

    # Pattern: (US-XXX.md) in same directory references
    sed -i '' "s|(${us_name}\.md)|(../${epic_name}/User Stories/${us_name}/${us_name}.md)|g" "$temp_file"
  done

  # Only replace if changes were made
  if ! cmp -s "$file" "$temp_file"; then
    mv "$temp_file" "$file"
    echo "  ✅ Updated: $file"
  else
    rm "$temp_file"
  fi
}

# Find all markdown files and fix links
find . -name "*.md" -type f | while read -r file; do
  # Skip node_modules and other directories we don't want to touch
  if [[ "$file" == *"node_modules"* ]] || [[ "$file" == *".git"* ]] || [[ "$file" == *"backlog_old"* ]]; then
    continue
  fi

  fix_links_in_file "$file"
done

echo "🔧 Fixing special cases..."

# Fix INDEX.md files that might have different patterns
if [ -f "docs/INDEX.md" ]; then
  sed -i '' 's|backlog/stories/INDEX\.md|backlog/README.md|g' "docs/INDEX.md"
  sed -i '' 's|backlog/epics/INDEX\.md|backlog/README.md|g' "docs/INDEX.md"
  echo "  ✅ Fixed docs/INDEX.md"
fi

# Fix references to dashboard
if [ -f "docs/backlog/dashboard/README.md" ]; then
  # Dashboard needs special handling for relative paths
  sed -i '' 's|\.\./\.\./epics/\(EPIC-[0-9]*\)|\.\./\1|g' "docs/backlog/dashboard/README.md"
  echo "  ✅ Fixed dashboard README"
fi

echo "✅ All links have been updated to new backlog structure!"
echo ""
echo "Summary:"
echo "  - User Stories: Now in docs/backlog/EPIC-XXX/User Stories/US-XXX/"
echo "  - EPICs: Now in docs/backlog/EPIC-XXX/"
echo "  - Bugs: Now in docs/backlog/EPIC-XXX/User Stories/US-XXX/bugs/"
