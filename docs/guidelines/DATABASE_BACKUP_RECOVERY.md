# Database Backup & Recovery Guide

## 🔴 Probleem: Data Loss bij Branch Switches

**Wat gebeurde:**
- Database (`data/definities.db`) stond in `.gitignore` maar werd **toch getracked** door git
- Bij branch switches overschreef git de lokale database met oudere versies
- Resulteerde in verlies van 14-16 definities (IDs 74-75, 80-91)

**Root cause:**
- Database was ooit toegevoegd aan git (`git add data/definities.db`)
- `.gitignore` voorkomt alleen nieuwe files, geen reeds getracked files
- `git rm --cached` was nodig om tracking te stoppen

## ✅ Oplossingen Geïmplementeerd

### 1. Stop Git Tracking (2025-10-30)

**Commit:** `5c761e94` - "fix: stop tracking data/definities.db"

```bash
# Database is nu NIET meer getracked
git rm --cached data/definities.db

# Blijft wel in .gitignore (regels 131, 133)
```

**Effect:**
- ✅ Geen automatische overwrites meer bij branch switches
- ✅ Database veranderingen blijven lokaal
- ✅ Elke developer heeft eigen database

### 2. Data Recovery via TXT Exports

**Script:** `scripts/import_from_txt_exports.py`

**Hersteld:** 11 van 14 definities
- IDs 80-88 (9 definities) uit `exports/definities_export_20251029_130927.txt`
- IDs 90-91 (2 definities) uit `exports/definities_export_20251030_*.txt`
- **Verloren:** IDs 74-75, 89 (permanent verloren)

**Gebruik:**
```bash
# Import automatisch
python3 scripts/import_from_txt_exports.py

# Script zoekt automatisch naar:
# - definities_export_20251029_130927.txt (IDs 80-88)
# - definities_export_20251030_100359.txt (ID 90)
# - definities_export_20251030_101334.txt (ID 91)
```

### 3. Auto-Backup Systeem

**Scripts:**
- `scripts/auto_backup_database.sh` - Backup script
- `scripts/setup_auto_backup.sh` - Installatie via launchd

**Features:**
- ✅ Elk uur automatische backup
- ✅ Integrity check voor + na backup
- ✅ Behoudt laatste 24 backups (1 dag history)
- ✅ Symlink naar `latest.db` voor quick recovery
- ✅ Automatische cleanup oude backups

**Installatie:**
```bash
# Setup auto-backups (eenmalig)
bash scripts/setup_auto_backup.sh

# Status checken
launchctl list | grep backup

# Logs bekijken
tail -f logs/backup.log
```

**Manual backup:**
```bash
# Maak nu een backup
bash scripts/auto_backup_database.sh
```

**Backup locaties:**
```
data/backups/auto/          # Hourly auto-backups (laatste 24)
data/backups/DEF-54/        # Feature-specifieke backups
data/backups/               # Overige backups
```

## 🚨 Data Recovery Procedures

### Scenario 1: Recent Data Loss (< 1 uur)

```bash
# Laatste auto-backup herstellen
cp data/backups/auto/latest.db data/definities.db

# Verify
sqlite3 data/definities.db "PRAGMA integrity_check;"
sqlite3 data/definities.db "SELECT COUNT(*) FROM definities;"
```

### Scenario 2: Data Loss met TXT Exports

```bash
# Zoek relevante exports
ls -lht exports/*.txt | head -20

# Import via script
python3 scripts/import_from_txt_exports.py

# Script vraagt om confirmatie en toont preview
```

### Scenario 3: Specifieke Feature Backup

```bash
# Lijst backups
ls -lht data/backups/*/

# Restore specifieke backup
cp data/backups/DEF-54/definities_pre_refactor.db data/definities.db

# Verify
sqlite3 data/definities.db "PRAGMA integrity_check;"
```

### Scenario 4: Time Machine (macOS)

```bash
# 1. Open Time Machine
# 2. Navigate naar: /Users/chrislehnen/Projecten/Definitie-app/data/
# 3. Zoek definities.db op gewenste tijdstip
# 4. Restore
```

## 📋 Preventieve Maatregelen Checklist

### Voor Developers

- [ ] **Nooit** `git add data/definities.db` runnen
- [ ] Bij nieuwe feature: maak backup in `data/backups/FEATURE-NAME/`
- [ ] Voor major refactors: manual backup + BACKUP_INFO.txt
- [ ] Gebruik UI export functie regelmatig (TXT/Excel)

### Voor Feature Work

```bash
# VÓÓR feature branch werk:
mkdir -p data/backups/EPIC-XXX
cp data/definities.db data/backups/EPIC-XXX/definities_pre_EPIC.db

# Metadata toevoegen
cat > data/backups/EPIC-XXX/BACKUP_INFO.txt <<EOF
Feature: EPIC-XXX
Date: $(date +"%Y-%m-%d %H:%M:%S")
Definities: $(sqlite3 data/definities.db "SELECT COUNT(*) FROM definities;")
Purpose: Pre-feature backup
EOF
```

### Database Hygiene

```bash
# Weekly check
sqlite3 data/definities.db "PRAGMA integrity_check;"

# Vacuum (compacteren)
sqlite3 data/definities.db "VACUUM;"

# Analyze (query optimization)
sqlite3 data/definities.db "ANALYZE;"
```

## 🔍 Troubleshooting

### Auto-backup draait niet

```bash
# Check launchd status
launchctl list | grep backup

# Reload service
launchctl unload ~/Library/LaunchAgents/com.definitieagent.backup.plist
launchctl load ~/Library/LaunchAgents/com.definitieagent.backup.plist

# Check logs
tail -n 50 logs/backup.log
tail -n 50 logs/backup.error.log
```

### Backup corrupt

```bash
# Verify backup
sqlite3 data/backups/auto/definities_backup_YYYYMMDD_HHMMSS.db "PRAGMA integrity_check;"

# Try older backup
ls -lt data/backups/auto/ | head -10
```

### Import script fails

```bash
# Check export file format
head -50 exports/definities_export_YYYYMMDD_HHMMSS.txt

# Verify IDs in export
grep "^ID: " exports/definities_export_YYYYMMDD_HHMMSS.txt | sort -u

# Run with debug
python3 -v scripts/import_from_txt_exports.py
```

## 📊 Monitoring & Metrics

### Backup Status Dashboard

```bash
# Aantal backups
echo "Auto backups: $(ls -1 data/backups/auto/*.db 2>/dev/null | wc -l)"

# Laatste backup tijd
ls -lt data/backups/auto/ | head -2

# Disk usage
du -sh data/backups/

# Database size trend
ls -lh data/definities.db data/backups/auto/definities_backup_*.db | tail -5
```

### Alerts

**Setup email alerts (optioneel):**

```bash
# Toevoegen aan auto_backup_database.sh
# Als backup faalt, stuur email
if ! sqlite3 "$BACKUP_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "Backup failed!" | mail -s "DefinitieAgent Backup FAILED" your@email.com
fi
```

## 🎯 Best Practices

1. **Gebruik UI export functie**
   - Wekelijks volledige export (TXT + Excel)
   - Voor belangrijke definities: individuele exports

2. **Feature branches**
   - Altijd backup maken voor major changes
   - Include BACKUP_INFO.txt met metadata

3. **Git hygiene**
   - NOOIT database committen
   - Check `git status` voor `data/definities.db`

4. **Recovery testing**
   - Test recovery procedure 1x per maand
   - Verify backups zijn valid

5. **Documentation**
   - Update deze guide bij nieuwe procedures
   - Document custom backup strategies per EPIC

## 📚 Related Documents

- `docs/analyses/BUG_HUNT_ANALYSIS_2025-10-30.md` - Root cause analysis
- `scripts/import_from_txt_exports.py` - Import script source
- `scripts/auto_backup_database.sh` - Backup script source
- `CLAUDE.md` - Project guidelines (database section)

## 🔗 Links

- [SQLite PRAGMA commands](https://www.sqlite.org/pragma.html)
- [macOS launchd](https://www.launchd.info/)
- [Git ignore patterns](https://git-scm.com/docs/gitignore)

---

**Last updated:** 2025-10-30
**Maintainer:** DevOps / Data Recovery Team
