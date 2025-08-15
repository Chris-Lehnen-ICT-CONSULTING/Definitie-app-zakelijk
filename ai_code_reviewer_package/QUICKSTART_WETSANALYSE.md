# Quickstart: AI Code Reviewer in Wetsanalyse Project

## Directe Installatie & Gebruik

```bash
# 1. Ga naar Wetsanalyse project
cd /Users/chrislehnen/Projecten/Wetsanalyse

# 2. Installeer ai-code-reviewer vanaf Definitie-app
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package

# 3. Setup voor eerste gebruik
ai-code-review setup

# 4. Run je eerste code review!
ai-code-review
```

## Wat Gebeurt Er?

1. **Setup** maakt `.ai-review-config.yaml` aan
2. **AI Review** scant je code voor:
   - Syntax errors
   - Type hints issues  
   - Security problemen
   - Best practices
   - Framework-specifieke patterns
3. **Automatische Fixes** worden direct toegepast
4. **Rapport** toont wat er is gefixt

## Dagelijks Gebruik

### Na het schrijven van nieuwe code:
```bash
ai-code-review
```

### Voor een snelle check (max 3 iteraties):
```bash
ai-code-review --max-iterations 3
```

### Check specifieke directories:
```bash
ai-code-review --source-dirs src/ lib/
```

## Updates Installeren

### Optie 1: Kopieer update script (eenmalig)
```bash
# Kopieer script
cp /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package/quick-update.sh .

# Voer updates uit
./quick-update.sh
```

### Optie 2: Direct updaten
```bash
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package --upgrade
```

## Voorbeeld Workflow

```bash
# 1. Schrijf je code
vim mijn_nieuwe_feature.py

# 2. Test lokaal
python mijn_nieuwe_feature.py

# 3. Laat AI de code reviewen en fixen
ai-code-review

# 4. Check wat er is aangepast
git diff

# 5. Als tevreden, commit
git add .
git commit -m "feat: nieuwe feature met AI code review"
```

## Tips

- 💡 Run `ai-code-review` NA het schrijven van code, VOOR het committen
- 🎯 Gebruik `--max-iterations 3` voor snelle checks tijdens development
- 📝 Pas `.ai-review-config.yaml` aan voor project-specifieke regels
- 🔄 Update regelmatig met `./quick-update.sh`

## Hulp Nodig?

```bash
# Bekijk alle opties
ai-code-review --help

# Check versie
python -c "from ai_code_reviewer import __version__; print(__version__)"
```