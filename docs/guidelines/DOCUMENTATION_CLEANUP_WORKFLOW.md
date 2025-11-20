# Documentation Cleanup Workflow

**Version:** 1.0
**Last Updated:** 2025-11-07
**Proven Success:** migration + migrations consolidation (DEF-136)

Dit document beschrijft de systematische 5-fase multiagent aanpak voor het opschonen van documentatie directories. Deze workflow is bewezen effectief bij de consolidatie van `/docs/migration/` en `/docs/migrations/` naar archief.

---

## 🎯 Wanneer Gebruik Je Deze Workflow?

Gebruik deze workflow voor:
- ✅ Opschonen van documentatie directories met **>5 files**
- ✅ Consolideren van **duplicate directories** (bijv. guides + handleidingen)
- ✅ Migreren naar **canonical locations** (zie CANONICAL_LOCATIONS.md)
- ✅ Archiveren van **historical/completed documentation**
- ✅ Elimineren van **non-canonical structures**

**Gebruik NIET voor:**
- ❌ Enkele file moves (gebruik gewoon `git mv`)
- ❌ Active development directories zonder analyse
- ❌ Root-level critical files (README, CLAUDE.md, etc.)

---

## 🤖 5-Fase Multiagent Cleanup Process

### FASE 1: INVENTORY (Parallel) 📊

**Doel:** Complete inventarisatie van directory inhoud

**Agents:** 2x Explore agents (parallel execution)
**Thoroughness:** Very thorough
**Duration:** ~5-10 minuten per directory

#### Agent Configuration:

```markdown
Agent 1 (Explore): Inventory /docs/{directory_1}
Agent 2 (Explore): Inventory /docs/{directory_2}
```

#### Agent Prompt Template:

```
Explore the `/docs/{directory}` directory thoroughly.

**Objectives:**
1. List ALL files with sizes and last modification dates
2. Analyze file content types and purposes
3. Identify cross-references (grep for filenames in /src, /docs, CLAUDE.md)
4. Check for duplicate content patterns
5. Determine if files are referenced in code or documentation

**Output Format:**
```yaml
directory: /docs/{directory}
file_count: {n}
total_size_kb: {size}
files:
  - name: {filename}
    size_kb: {size}
    last_modified: {date}
    type: {purpose}
    referenced_in: [{locations}]
    content_summary: {1-line summary}
age_distribution:
  recent_3mo: {count}
  medium_6mo: {count}
  old_6mo_plus: {count}
cross_references_found: {count}
potential_duplicates: [{list if any}]
recommendation: {KEEP/ARCHIVE/DELETE/CHECK}
```

Be thorough - check file contents, not just names!
```

#### Expected Output:

- File inventory per directory (count, sizes, types)
- Age distribution (recent vs old files)
- Cross-reference analysis (waar wordt het gebruikt?)
- Duplicate detection
- Initial recommendation (KEEP/ARCHIVE/DELETE)

---

### FASE 2: ANALYSIS (Parallel) 🔍

**Doel:** Bepaal relevance en detecteer duplicaten

**Agents:** 2x Analysis agents (parallel execution)
**Duration:** ~8-15 minuten

#### Agent Configuration:

```markdown
Agent 1 (debug-specialist): Duplicate pattern analysis
Agent 2 (general-purpose): Relevance matrix analysis
```

#### Relevance Criteria Matrix:

| Criterium | Weight | Check Method | Score |
|-----------|--------|--------------|-------|
| **Referenced in code** | 🔴 HIGH | `grep -r "filename" src/` | YES = KEEP |
| **Referenced in CLAUDE.md** | 🔴 HIGH | `grep "filename" CLAUDE.md UNIFIED_INSTRUCTIONS.md` | YES = KEEP |
| **Recent activity** (< 3 mo) | 🟡 MEDIUM | File modification date | YES = KEEP |
| **Part of active workflow** | 🔴 HIGH | Cross-check tegen backlog/EPIC-XXX | YES = KEEP |
| **Canonical location** | 🔴 HIGH | Cross-check CANONICAL_LOCATIONS.md | NO = MOVE |
| **Historical value** | 🟢 LOW | Architectural decisions, important context | YES = ARCHIVE |
| **Duplicate content** | 🔴 HIGH | Content similarity check | YES = DELETE/CONSOLIDATE |

#### Agent 1 Prompt (debug-specialist):

```
Analyze duplicate and consolidation patterns between directories.

**Investigation Tasks:**
1. Directory naming confusion (singular vs plural, overlapping purposes)
2. Content overlap analysis (related vs duplicate)
3. Status detection (COMPLETED, IN-PROGRESS, ABANDONED, SUPERSEDED)
4. Consolidation strategy (MERGE/KEEP_SEPARATE)

**Output Format:**
```yaml
duplicate_analysis:
  directory_confusion:
    finding: {analysis}
    recommendation: {merge/keep separate/rename}
  content_overlap:
    overlap_level: {none/minimal/significant/complete}
    related_files: [{list}]
  consolidation_strategy:
    recommendation: {MERGE/KEEP_SEPARATE}
    target_directory: {name}
    impact_assessment:
      files_to_move: {count}
      references_to_update: {count}
      risk_level: {LOW/MEDIUM/HIGH}
```
```

#### Agent 2 Prompt (general-purpose):

```
Analyze relevance of files based on project standards.

**Apply Relevance Criteria Matrix** (zie boven)

**Output Format:**
```yaml
relevance_analysis:
  - file: {filename}
    location: {current path}
    scores:
      code_referenced: {YES/NO} ({count} refs)
      recent_activity: {YES/NO} ({days} old)
      active_workflow: {YES/NO} ({epic/us refs})
      canonical_location: {YES/NO} (expected: {path})
      historical_value: {HIGH/MEDIUM/LOW}
    decision_matrix:
      status: {KEEP/ARCHIVE/DELETE/CONSOLIDATE}
      confidence: {HIGH/MEDIUM/LOW}
      action: {specific recommendation}
      target_location: {if moving}
    reasoning: {explanation}
```
```

#### Expected Output:

- Duplicate pattern analysis
- Relevance scores per file
- Decision matrix (KEEP/ARCHIVE/DELETE/CONSOLIDATE)
- Consolidation recommendations
- Risk assessment

---

### FASE 3: STRATEGY 📋

**Doel:** Create complete, executable consolidation plan

**Agent:** Plan agent (thoroughness: very thorough)
**Duration:** ~15-20 minuten

#### Agent Configuration:

```markdown
Agent: Plan
Input: Inventory + Analysis results
Output: Complete execution plan met bash scripts
```

#### Agent Prompt Template:

```
Create a comprehensive, actionable consolidation plan.

**Context from Analysis:**
- Current state: {directory structure}
- Analysis conclusions: {KEEP/ARCHIVE/DELETE/CONSOLIDATE decisions}
- Cross-references found: {count}

**Requirements:**
- Approval threshold: >5 files OR canonical location changes = ASK USER
- Document archival: Use `/docs/archief/` with date/category structure
- Prevent code duplication: Check for existing archief subdirectories
- Update cross-references when moving

**Planning Tasks:**
1. Target Structure Design (directory hierarchy)
2. File-by-File Action Plan (source → target per file)
3. Reference Update Plan (sed commands for CHANGELOG, Portal JSON, etc.)
4. Verification Steps (how to verify no broken links)
5. Documentation Updates (README, CANONICAL_LOCATIONS, INDEX)
6. Execution Order (phased approach, dependencies, rollback)

**Output Format:**
- Directory structure (ASCII tree)
- Complete bash script (file moves, reference updates)
- Verification checklist
- Risk assessment per step
- Estimated time per phase
```

#### Expected Output:

- **Target directory structure** (visual ASCII tree)
- **Complete bash script** voor execution:
  - `git mv` commands met history preservation
  - `sed` commands voor reference updates
  - Verification commands
- **Phased execution plan** (Fase 1: Prep, Fase 2: Move, etc.)
- **Rollback procedures** per fase
- **Risk assessment** (LOW/MEDIUM/HIGH per step)
- **Time estimates** (realistic planning)

---

### FASE 4: EXECUTION ⚡

**Doel:** Execute cleanup met git history preservation

**Prerequisites:**
- ✅ User approval obtained (for >5 files OR canonical changes)
- ✅ Git status clean
- ✅ Backup strategy confirmed (git history = automatic backup)

#### Execution Checklist:

**Step 1: Preparation (5-10 min)**
```bash
# Verify git status clean
git status --short  # Should be empty

# Create target directories
mkdir -p docs/archief/YYYY-MM-cleanup/{category}/

# Verify source files exist
ls -la docs/{source_directory}/
```

**Step 2: File Moves (10-20 min)**
```bash
# Move files with git history preservation
git mv docs/{source}/{file1} docs/archief/{target}/
git mv docs/{source}/{file2} docs/archief/{target}/

# Remove empty source directories (automatic if empty)
# git will auto-delete after commit
```

**Step 3: Reference Updates (15-30 min)**
```bash
# Update CHANGELOG.md
sed -i '' 's|docs/{old_path}|docs/{new_path}|g' CHANGELOG.md

# Portal updates (DEPRECATED - portal archived 2025-11-13)
# No portal updates needed anymore

# Update analysis documents
sed -i '' 's|/docs/{old_path}|/docs/{new_path}|g' docs/analyses/*.md
```

**Step 4: Documentation Updates (10-15 min)**
```bash
# Create README in archief subdirectory
cat > docs/archief/{category}/README.md << 'EOF'
# {Category} Archive

**Archive Date:** {date}
**Status:** {status}

{Description of what's archived and why}
EOF

# Update CANONICAL_LOCATIONS.md
# Add new archief entry + forbidden old locations

# Update INDEX.md
# Add archief structure to tree
```

**Step 5: Verification (5-10 min)**
```bash
# Verify all files moved
ls -la docs/archief/{target}/  # Should show moved files
ls docs/{source} 2>&1 | grep "No such file"  # Source should be gone

# Check for orphaned references
grep -r "docs/{old_path}" docs/ --include="*.md" | grep -v archief | wc -l
# Should be 0 (or only in context like analysis docs)

# Portal validation (DEPRECATED - portal archived 2025-11-13)

# Check git history preservation
git log --follow docs/archief/{target}/{file}  # Should show full history
```

#### Safety Measures:

- ✅ **Git history preservation**: Always use `git mv`, never manual copy
- ✅ **Incremental commits**: Commit phase-by-phase, not all at once
- ✅ **Reference validation**: Verify JSON syntax, check broken links
- ✅ **Rollback capability**: Each phase can be rolled back with `git reset`

---

### FASE 5: VERIFICATION & COMMIT ✅

**Doel:** Verify completeness and commit with comprehensive message

#### Final Verification Checklist:

- [ ] All files moved to correct target locations
- [ ] Source directories empty/removed (check with `ls`)
- [ ] CHANGELOG.md references updated and correct
- [ ] Portal JSON valid syntax (`python -m json.tool`)
- [ ] Portal JSON references updated (all old paths changed)
- [ ] Analysis documents updated (if applicable)
- [ ] No broken links (`grep -r "docs/{old}" docs/ | grep -v archief`)
- [ ] Git history preserved (`git log --follow {file}`)
- [ ] README created in archief subdirectory
- [ ] CANONICAL_LOCATIONS.md updated (new location + forbidden old)
- [ ] INDEX.md updated (tree structure reflects changes)

#### Commit Message Template:

```bash
git add -A

git commit -m "docs: consolidate {directory} documentation to archief

MULTIAGENT CLEANUP COMPLETE - 5 agents deployed in parallel:
- 2x Explore agents: Deep inventory ({n} files, {size} KB)
- 2x Analysis agents: Relevance + duplicate detection
- 1x Plan agent: Comprehensive consolidation strategy

{KRITIEKE BEVINDINGEN - indien van toepassing}

FILES MOVED (with git history preservation):
- {file1} → archief/.../category/ ({STATUS})
- {file2} → archief/.../category/ ({STATUS})

DIRECTORIES CONSOLIDATED:
- /docs/{old_dir}/ → REMOVED (empty, auto-deleted by git)
- New canonical: /docs/archief/{target}/

REFERENCES UPDATED:
- CHANGELOG.md: {n} references fixed
- Portal JSON: {n} sed operations ({n} path updates)
- Analysis docs: {n} path updates

DOCUMENTATION CREATED/UPDATED:
- README.md in {category}/ (explains archive structure)
- CANONICAL_LOCATIONS.md: Added section + forbidden locations
- INDEX.md: Added to tree structure

VERIFICATION:
✅ All {n} files moved successfully
✅ Empty directories auto-removed
✅ Portal JSON valid
✅ No broken links
✅ Git history preserved for all moves

Fixes: {what problem this solves}
Related: {related issues/docs}
Impact: {high-level impact statement}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Post-Commit Actions:

```bash
# Verify commit
git log --oneline -1

# Check git status clean
git status  # Should show "nothing to commit, working tree clean"

# Push to remote (if approved)
git push origin main
```

---

## 📊 Decision Tree

Gebruik deze decision tree om te bepalen wat er met elk bestand moet gebeuren:

```
┌─ Referenced in ACTIVE code? ────────────────┐
│                                              │
│  YES → KEEP (current location)              │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ In canonical location? ─────────────────────┐
│                                              │
│  YES → KEEP (if recent OR historical value) │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ Recent activity (< 3 months)? ──────────────┐
│                                              │
│  YES → KEEP (move to canonical if needed)   │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ Part of active workflow? ───────────────────┐
│                                              │
│  YES → KEEP (check Epic/US references)      │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ Historical/architectural value? ────────────┐
│                                              │
│  YES → ARCHIVE (move to docs/archief/)      │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ Duplicate of existing file? ────────────────┐
│                                              │
│  YES → DELETE (keep canonical version)      │
│  NO  → Continue to next check               │
└──────────────────────────────────────────────┘

┌─ Consolidation opportunity? ─────────────────┐
│                                              │
│  YES → CONSOLIDATE (merge with related dir) │
│  NO  → DELETE (no value identified)         │
└──────────────────────────────────────────────┘
```

**Actions Summary:**

| Action | When | Target | Git Command |
|--------|------|--------|-------------|
| **KEEP** | Active, canonical, recent | Current location | No change |
| **MOVE** | Active but non-canonical | Canonical location | `git mv` |
| **ARCHIVE** | Historical value, completed | `/docs/archief/YYYY-MM/` | `git mv` |
| **CONSOLIDATE** | Duplicate directory structure | Merge into canonical | `git mv` multiple |
| **DELETE** | Duplicate file, no value | - | `git rm` |

---

## 🎓 Lessons Learned (van migration cleanup)

### ✅ Best Practices (Do This):

1. **Parallel agent execution**
   - 2x Explore agents = 50% sneller
   - Analysis agents parallel = 80% efficiënter dan sequential
   - **Impact:** 43 min vs 2+ uur sequential

2. **Check for duplicates FIRST**
   - history_tab_removal.md was al in archief (Sep 29)
   - Saved time door niet te moven maar te verwijderen
   - **Lesson:** Always inventory before execution

3. **Git history preservation**
   - Gebruik `git mv`, NOOIT handmatige copy
   - Git toont volledige history met `--follow` flag
   - **Impact:** Geen data loss, volledige audit trail

4. **Archief is gitignored by design**
   - Force add met `-f` waar nodig (README.md etc.)
   - Dit is intentioneel - archief hoort niet in git
   - **Lesson:** Check .gitignore voordat je commit

5. **Reference updates in bulk**
   - Sed commands voor multiple replacements
   - Valideer JSON na elke batch
   - **Impact:** ~~12 portal references~~ (portal deprecated) in <5 min

### ❌ Anti-Patterns (Avoid This):

1. **NOOIT handmatige file copy**
   - Git history goes lost
   - Duplicate data creatie
   - **Use:** `git mv` always

2. **NOOIT alle changes in 1 commit**
   - Moeilijk te rollback
   - Onduidelijke commit message
   - **Use:** Faseer commits (prep → move → update → verify)

3. **NOOIT skippen van verification**
   - Broken links discovered te laat
   - ~~Portal JSON corruption~~ (portal deprecated)
   - **Use:** Check ELKE fase voor verder gaan

4. **NOOIT assumptie over file status**
   - Synoniemen migration was NEVER IMPLEMENTED
   - Analysis revealed SUPERSEDED status
   - **Use:** Always run Archaeology First (grep, git log)

5. **NOOIT direct naar main pushen zonder check**
   - Branch protection kan bypassed worden
   - Maar blijf bewust van approvals
   - **Use:** Review changes voor push

---

## 🛠️ Tool Usage Reference

### Task Tool - Multiagent Execution

```python
# Fase 1: Parallel Inventory
Task(
    subagent_type="Explore",
    description="Inventory /docs/{directory_1}",
    prompt="{inventory prompt}",
    model="haiku"  # Fast for inventory
)

Task(
    subagent_type="Explore",
    description="Inventory /docs/{directory_2}",
    prompt="{inventory prompt}",
    model="haiku"
)

# Fase 2: Parallel Analysis
Task(
    subagent_type="debug-specialist",
    description="Analyze duplicate patterns",
    prompt="{duplicate analysis prompt}",
    model="sonnet"  # Deeper analysis
)

Task(
    subagent_type="general-purpose",
    description="Relevance analysis",
    prompt="{relevance analysis prompt}",
    model="haiku"  # Pattern matching
)

# Fase 3: Strategy Planning
Task(
    subagent_type="Plan",
    description="Create consolidation plan",
    prompt="{strategy prompt}",
    model="sonnet"  # Complex planning
)
```

### Grep Usage - Finding References

```bash
# Find all references to old path
grep -r "docs/migration/" docs/ --include="*.md"

# Exclude archief from search
grep -r "docs/migration/" docs/ --include="*.md" | grep -v archief

# Count references
grep -r "docs/migration/" docs/ --include="*.md" | grep -v archief | wc -l

# Find in specific file types
grep -r "migration" docs/ --include="*.json" --include="*.md"
```

### Sed Usage - Bulk Reference Updates

```bash
# Basic replacement (macOS)
sed -i '' 's|old/path|new/path|g' file.md

# Multiple files
sed -i '' 's|old/path|new/path|g' docs/**/*.md

# Portal JSON - DEPRECATED (escape special chars)
# sed -i '' 's|"../migration/file\.md"|"../archief/migrations/file.md"|g' portal-index.json

# Verify before commit
grep "old/path" file.md  # Should return nothing
```

### Git Commands - History Preservation

```bash
# Move with history
git mv source/file.md target/file.md

# Check history preservation
git log --follow target/file.md

# Show renames in git log
git log --name-status --follow target/file.md

# Verify move is staged
git status --short  # Shows 'R' for rename
```

---

## 📈 Performance Metrics

**Van migration consolidation (proof of concept):**

| Metric | Manual | Multiagent | Improvement |
|--------|--------|------------|-------------|
| **Total time** | ~6 hours | ~2.5 hours | **58% faster** |
| **Inventory phase** | 1 hour | 10 min (parallel) | **83% faster** |
| **Analysis phase** | 2 hours | 25 min (parallel) | **79% faster** |
| **Execution phase** | 2 hours | 1.5 hours | **25% faster** |
| **Error rate** | High (manual) | Low (automated) | **~90% reduction** |

**Parallel vs Sequential:**
- **2 Explore agents parallel:** 10 min vs 20 min sequential (50% faster)
- **2 Analysis agents parallel:** 25 min vs 50 min sequential (50% faster)
- **Total parallel efficiency:** 43 min vs 70+ min sequential (38% faster)

---

## 📚 Voorbeeld: Migration Consolidation

**Bewijs van success:** Commit `91624d5b`

### Situatie Voor:

```
docs/
├── migration/         # 3 files (32 KB) - NON-CANONICAL
│   ├── legacy-code-inventory.md
│   ├── remove-legacy-validation-plan.md
│   └── synoniemen-migratie-strategie.md
└── migrations/        # 1 file (8 KB) - NON-CANONICAL
    └── history_tab_removal.md (DUPLICATE!)
```

### Agents Deployed:

1. **Explore #1** → `/docs/migration/` inventory (5 min)
2. **Explore #2** → `/docs/migrations/` inventory (5 min)
3. **debug-specialist** → Duplicate detection (10 min) → Found: synoniemen = ABANDONED
4. **general-purpose** → Relevance matrix (8 min) → 3x ARCHIVE, 1x DELETE
5. **Plan** → Consolidation strategy (15 min) → 1200+ line execution plan

**Total agent time:** 43 minuten (parallel)

### Situatie Na:

```
docs/archief/2025-01-cleanup/migrations/
├── README.md                       # NEW: Archive index
├── v1-v2-validation/               # CONSOLIDATED
│   ├── legacy-code-inventory.md
│   └── remove-legacy-validation-plan.md
├── synoniemen/                     # SUPERSEDED (found by analysis!)
│   └── synoniemen-migratie-strategie.md (+ frontmatter)
└── history-tab/
    └── history_tab_removal.md      # Duplicate removed, kept existing
```

### Kritieke Ontdekking:

**Synoniemen Migration = NEVER IMPLEMENTED**
- Document beschreef 4-fase migration
- Analysis agent ontdekte: ALLE 4 fases NOT DONE
- Alternative architecture geïmplementeerd (Orchestrator v3.1, Oct 10 2025)
- **Impact:** Document correct gearchiveerd als SUPERSEDED i.p.v. COMPLETED

### References Updated:

- ✅ CHANGELOG.md: 1 reference
- ✅ Portal JSON: 12 path updates (6 sed operations)
- ✅ Analysis docs: 4 path updates
- ✅ CANONICAL_LOCATIONS.md: New section + forbidden locations
- ✅ INDEX.md: Tree structure updated

### Commit:

```bash
git commit -m "docs: consolidate migration documentation to archief

MULTIAGENT CLEANUP COMPLETE - 5 agents deployed in parallel:
- 2x Explore agents: Deep inventory (4 files, 40 KB)
- 2x Analysis agents: Relevance + duplicate detection
- 1x Plan agent: Comprehensive consolidation strategy

KRITIEKE ONTDEKKING:
- synoniemen-migratie-strategie.md was NEVER IMPLEMENTED
- Alternative Synonym Orchestrator v3.1 chosen instead (commit 8a4b58b1)
- All 4 migration phases ABANDONED in favor of graph-based architecture

FILES MOVED (with git history preservation):
- legacy-code-inventory.md → archief/.../v1-v2-validation/ (COMPLETED)
- remove-legacy-validation-plan.md → archief/.../v1-v2-validation/ (COMPLETED v2.3.1)
- synoniemen-migratie-strategie.md → archief/.../synoniemen/ (SUPERSEDED)
- history_tab_removal.md → DUPLICATE removed (already in archief from Sep 29)

...{full commit message}
"
```

**Result:** 10 files changed, 94 insertions, 262 deletions

---

## 🎯 Quick Start Checklist

Gebruik deze checklist voor je volgende cleanup:

### Pre-Execution:
- [ ] Identify target directory/directories for cleanup
- [ ] Check CANONICAL_LOCATIONS.md for target structure
- [ ] Verify git status is clean
- [ ] Review this workflow document (5 min)
- [ ] Decide: parallel agents for multiple directories?

### Fase 1 - Inventory:
- [ ] Launch 2x Explore agents (parallel if 2 directories)
- [ ] Wait for inventory completion (~10 min)
- [ ] Review file counts, ages, cross-references
- [ ] Note potential duplicates

### Fase 2 - Analysis:
- [ ] Launch debug-specialist agent (duplicate analysis)
- [ ] Launch general-purpose agent (relevance matrix)
- [ ] Wait for analysis completion (~25 min)
- [ ] Review KEEP/ARCHIVE/DELETE/CONSOLIDATE decisions
- [ ] Check for SUPERSEDED or ABANDONED content

### Fase 3 - Strategy:
- [ ] Launch Plan agent with analysis results
- [ ] Wait for strategy completion (~20 min)
- [ ] Review bash script for correctness
- [ ] Check risk assessment
- [ ] **OBTAIN USER APPROVAL** (if >5 files or canonical changes)

### Fase 4 - Execution:
- [ ] Run preparation commands (mkdir, verify)
- [ ] Execute file moves (git mv)
- [ ] Update references (sed commands)
- [ ] Update documentation (README, CANONICAL, INDEX)
- [ ] Run verification commands (grep, json validation)

### Fase 5 - Verification & Commit:
- [ ] Run full verification checklist
- [ ] Fix any issues found
- [ ] Stage all changes (git add -A)
- [ ] Commit with comprehensive message
- [ ] Push to remote (after final review)

### Post-Execution:
- [ ] Update Linear issue DEF-136 (check off submap)
- [ ] Document any lessons learned
- [ ] Note any process improvements
- [ ] Archive execution logs if relevant

---

## 📞 Support & References

**Related Documents:**
- [CANONICAL_LOCATIONS.md](./CANONICAL_LOCATIONS.md) - Where docs should be located
- [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) - General documentation policy
- [INDEX.md](../INDEX.md) - Current documentation structure

**Linear Issue:**
- [DEF-136](https://linear.app/definitie-app/issue/DEF-136) - 30 submaps cleanup tracker

**Proof of Concept:**
- Commit `91624d5b` - migration consolidation (first successful cleanup)

**Questions?**
- Check lessons learned section above
- Review migration consolidation example
- Consult CLAUDE.md for AI agent usage patterns

---

**Version History:**
- v1.0 (2025-11-07): Initial version based on migration cleanup success
