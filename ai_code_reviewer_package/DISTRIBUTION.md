# AI Code Reviewer Distribution Guide

## Voor Ontwikkelaars

### Opties voor Package Distributie

#### 1. **Directe Git Installatie (Simpelst)**
```bash
# In elk project waar je het wilt gebruiken:
pip install -e git+file:///Users/chrislehnen/Projecten/Definitie-app#subdirectory=ai_code_reviewer_package&egg=ai-code-reviewer

# Of met pip install vanaf lokale directory:
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package
```

#### 2. **Quick Update Script (Aanbevolen)**
Kopieer `quick-update.sh` naar je andere projecten:
```bash
# Eenmalig kopieren naar ander project
cp /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package/quick-update.sh .

# Daarna updaten met:
./quick-update.sh
```

#### 3. **Symbolische Link (Voor Development)**
```bash
# In je andere project's virtual environment
cd /path/to/other/project/venv/lib/python3.x/site-packages/
ln -s /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package/ai_code_reviewer ai_code_reviewer
```

#### 4. **Build & Distribute**
```bash
# In ai_code_reviewer_package directory
./distribute.sh

# Installeer wheel in ander project
pip install /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package/dist/ai_code_reviewer-2.1.0-py3-none-any.whl
```

### Update Workflow

1. **Check huidige versie:**
   ```bash
   ai-code-review update --check-only
   ```

2. **Update package:**
   ```bash
   # Via ingebouwde updater
   ai-code-review update
   
   # Of via quick script
   ./quick-update.sh
   ```

3. **Verify installatie:**
   ```bash
   ai-code-review --version
   ```

### Voor Teams

#### Shared Network Drive
```bash
# Build en kopieer naar shared location
./distribute.sh
cp dist/*.whl /path/to/shared/python-packages/

# Team members installeren met:
pip install /path/to/shared/python-packages/ai_code_reviewer-2.1.0-py3-none-any.whl
```

#### Private PyPI Server
Zie `setup-private-pypi.md` voor complete instructies.

### Development Tips

1. **Editable Install voor Development:**
   ```bash
   pip install -e /path/to/ai_code_reviewer_package
   ```
   Wijzigingen in de source zijn direct beschikbaar zonder herinstallatie.

2. **Version Management:**
   - Update versie in `ai_code_reviewer/__init__.py`
   - Tag release in git: `git tag v2.1.0`
   - Build nieuwe distributie: `./distribute.sh`

3. **Testing in Isolated Environment:**
   ```bash
   python -m venv test-env
   source test-env/bin/activate
   pip install /path/to/dist/ai_code_reviewer-2.1.0-py3-none-any.whl
   ai-code-review --version
   ```