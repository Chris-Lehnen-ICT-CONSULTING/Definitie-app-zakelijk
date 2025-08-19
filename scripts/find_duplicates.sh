#!/bin/bash

# Find Duplicates Script
# Finds all duplicate markdown files in the docs directory

echo "# Deduplicatie Rapport"
echo "Gegenereerd op: $(date)"
echo ""
echo "## Duplicaten Analyse"
echo ""

# Create temporary directory for hashes
temp_dir=$(mktemp -d)

# Find all markdown files and calculate MD5 hashes
find docs -name "*.md" -type f -exec md5 -q {} \; > "$temp_dir/all_hashes.txt"
find docs -name "*.md" -type f > "$temp_dir/all_files.txt"

# Combine hashes with filenames
paste "$temp_dir/all_hashes.txt" "$temp_dir/all_files.txt" > "$temp_dir/hash_file_pairs.txt"

# Sort by hash to group duplicates
sort -k1 "$temp_dir/hash_file_pairs.txt" > "$temp_dir/sorted_pairs.txt"

# Find duplicate groups
current_hash=""
duplicate_count=0
total_duplicates=0

echo "### Duplicaten Groepen"
echo ""

while IFS=$'\t' read -r hash file; do
    if [ "$hash" = "$current_hash" ]; then
        if [ $duplicate_count -eq 0 ]; then
            echo "**Groep $((total_duplicates + 1))** (Hash: ${hash:0:8}...)"
            echo "- $prev_file"
        fi
        echo "- $file"
        duplicate_count=$((duplicate_count + 1))
    else
        if [ $duplicate_count -gt 0 ]; then
            echo ""
            total_duplicates=$((total_duplicates + 1))
        fi
        current_hash="$hash"
        prev_file="$file"
        duplicate_count=0
    fi
done < "$temp_dir/sorted_pairs.txt"

if [ $duplicate_count -gt 0 ]; then
    echo ""
    total_duplicates=$((total_duplicates + 1))
fi

echo ""
echo "## Samenvatting"
echo ""
echo "- Totaal aantal duplicate groepen: $total_duplicates"
echo "- Totaal aantal markdown bestanden: $(wc -l < "$temp_dir/all_files.txt" | tr -d ' ')"

# Cleanup
rm -rf "$temp_dir"
