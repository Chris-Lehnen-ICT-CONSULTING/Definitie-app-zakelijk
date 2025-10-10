# Synonym Migration Quick Reference

## Quick Start

```bash
# 1. Preview migration (safe, no writes)
python scripts/migrate_synonyms_to_registry.py --dry-run

# 2. Backup database
cp data/definities.db data/definities.db.backup

# 3. Execute migration
python scripts/migrate_synonyms_to_registry.py --execute

# 4. If needed: Rollback
python scripts/migrate_synonyms_to_registry.py --rollback
```

## What Gets Migrated

### Source 1: YAML File (70 synoniemen)
`config/juridische_synoniemen.yaml` → `imported_yaml` source, global scope

### Source 2: Approved Suggestions (0 unique, 13 duplicates)
`synonym_suggestions` table → `ai_suggested` source, global scope

### Source 3: Definitie Voorbeelden (122 synoniemen)
`definitie_voorbeelden` table → `manual` source, **per-definitie scope**

### Expected Results
- **70 groups** created (unique hoofdtermen/begrippen)
- **192 members** added (unique synoniemen)
- **36 conflicts** detected (expected duplicates)
- **0 errors**

## CLI Options

```bash
# Modes (mutually exclusive, required)
--dry-run       # Preview only, no writes
--execute       # Actually migrate
--rollback      # Delete migrated data

# Paths (optional)
--db-path PATH          # Default: data/definities.db
--yaml-path PATH        # Default: config/juridische_synoniemen.yaml

# Options
--verbose               # DEBUG logging
--help                  # Show help
```

## Output Example

```
MIGRATION DRY-RUN SUMMARY
Duration: 0.02 seconds

GROUPS & MEMBERS:
  Groups created: 70
  Members added: 192

BY SOURCE:
  YAML imported: 70
  DB approved suggestions: 0
  Definitie voorbeelden: 122

ISSUES:
  Conflicts detected: 36 (expected)
  Errors encountered: 0
  Items skipped: 36
```

## Verify After Migration

```sql
-- Check counts
SELECT COUNT(*) FROM synonym_groups;        -- Should be 70
SELECT COUNT(*) FROM synonym_group_members; -- Should be 192

-- Check sources
SELECT source, COUNT(*) FROM synonym_group_members GROUP BY source;
-- imported_yaml: 70
-- manual: 122

-- Check statuses
SELECT status, COUNT(*) FROM synonym_group_members GROUP BY status;
-- active: 192
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| YAML file not found | Check path or use `--yaml-path` |
| Table not found | Update schema: `sqlite3 data/definities.db < src/database/schema.sql` |
| Permission denied | Check file permissions |
| Conflicts detected | **Expected** - duplicates are skipped (first wins) |

## Logs

- **Console:** INFO level (DEBUG with `--verbose`)
- **File:** `logs/synonym_migration.log` (persistent, all levels)

## Architecture

**Specification:** `docs/architectuur/synonym-orchestrator-architecture-v3.1.md` (lines 814-913)
**Guide:** `docs/technisch/synonym-migration-guide.md`
**Report:** `docs/technisch/phase-1.4-completion-report.md`

## Next Steps After Migration

1. Verify data (see SQL queries above)
2. Test SynonymRegistry queries:
   ```python
   from repositories.synonym_registry import get_synonym_registry
   registry = get_synonym_registry()
   synonyms = registry.get_synonyms("onherroepelijk", statuses=["active"])
   ```
3. Proceed to PHASE 2: Connect ProviderManager to Registry
4. Archive legacy YAML (keep as backup)

---

**Questions?** See full guide: `docs/technisch/synonym-migration-guide.md`
