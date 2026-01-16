---
name: database-location
enabled: true
event: file
action: block
conditions:
  - field: file_content
    operator: regex_match
    # Detecteert database paden die NIET in data/ zijn
    # Matcht: sqlite:///path, .db bestanden buiten data/, hardcoded db paths
    # Negative lookahead voor data/ voorkomt false positives
    pattern: (sqlite:\/\/\/(?!.*data\/)|["'](?!.*data\/)[\w\/\.\-]+\.db["']|\.connect\(["'](?!.*data\/)[\w\/\.\-]+\.db["']\)|Path\(["'](?!.*data\/)[\w\/\.\-]+\.db["']\))
---

**DATABASE LOCATIE OVERTREDING**

Je probeert een database pad te gebruiken dat **niet** in `data/` staat. Dit is verboden.

**Enige toegestane locatie:**
```python
# CORRECT
database_path = "data/definities.db"
connection = sqlite3.connect("data/definities.db")

# WRONG - Elke andere locatie
connection = sqlite3.connect("definities.db")           # Root
connection = sqlite3.connect("src/database/app.db")     # In src/
connection = sqlite3.connect("/tmp/temp.db")            # Temp
```

**Waarom deze regel:**
- Consistente data locatie maakt backups eenvoudiger
- Voorkomt dat databases verspreid raken over het project
- `.gitignore` is geconfigureerd voor `data/*.db`

**Referenties:**
- Huidige database: `data/definities.db`
- Schema: `src/database/schema.sql`
- Migrations: `src/database/migrations/`

**Zie:** CLAUDE.md §Critical Rules, §File Locations
