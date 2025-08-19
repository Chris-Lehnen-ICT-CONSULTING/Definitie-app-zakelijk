# 🤖 BMAD AI Agent Auto-Configuration Guide

## Overzicht

Deze guide legt uit hoe BMAD agents automatisch geconfigureerd worden voor AI code review.

## 🚀 Automatische Setup (Optie 1 - Aanbevolen)

### 1. Voor ALLE BMAD Agents

Voeg deze regel toe aan het startup script van je BMAD agents:

```bash
# In je BMAD agent startup/initialization
source /path/to/project/.bmad-core/init.sh
```

Of als je een `.bmad` launcher gebruikt:

```bash
#!/bin/bash
# .bmad launcher script

# Auto-load BMAD environment
if [[ -f ".bmad-core/init.sh" ]]; then
    source .bmad-core/init.sh
fi

# Rest van je BMAD launcher...
```

### 2. Wat gebeurt er automatisch?

Wanneer een BMAD agent start:
- ✅ `AI_AGENT_COMMIT=1` wordt gezet
- ✅ `AI_AGENT_NAME` wordt bepaald (Quinn, Claude, etc.)
- ✅ Git author info wordt geconfigureerd
- ✅ Review preferences worden geladen
- ✅ Helper functies beschikbaar (`ai_commit`)

### 3. Agent-Specifieke Configuratie

De configuratie herkent automatisch deze agents:
- **Quinn**: Extra strict review mode
- **Claude**: 5 iteraties voor fixes
- **Copilot**: Standaard settings
- **Overige**: BMAD-{ID} naming

## 📝 Gebruik door Agents

### Automatische Commits

Agents kunnen nu gewoon committen:

```bash
# Optie 1: Normale git commit (wordt automatisch AI-tagged)
git commit -m "implement feature X"

# Optie 2: Gebruik helper functie
ai_commit "implement feature X"  # Voegt automatisch "AI:" prefix toe
```

### Manual Review Trigger

```bash
# Agents kunnen ook manual review doen
review  # Alias voor python scripts/ai_code_reviewer.py
```

## 🔧 Configuratie Aanpassen

### Per-Agent Settings

Edit `.bmad-core/config/agent-environment.sh`:

```bash
case "$BMAD_AGENT_NAME" in
    "nieuwe-agent")
        export AI_AGENT_NAME="NieuweAgent"
        export AI_REVIEW_MAX_ITERATIONS=7
        export AI_REVIEW_STRICT=true
        ;;
esac
```

### Global Settings

In `.bmad-core/config/agent-environment.sh`:

```bash
# Pas deze waardes aan
export AI_REVIEW_MAX_ITERATIONS=${AI_REVIEW_MAX_ITERATIONS:-3}
export AI_REVIEW_AUTO_FIX=${AI_REVIEW_AUTO_FIX:-true}
```

## 🧪 Testen

### Test de Setup

```bash
# Simuleer een BMAD agent
export BMAD_AGENT_NAME="TestAgent"
source .bmad-core/init.sh

# Check environment
echo $AI_AGENT_COMMIT  # Moet "1" zijn
echo $AI_AGENT_NAME    # Moet "TestAgent" zijn

# Test commit
touch test.txt
git add test.txt
git commit -m "test AI review trigger"
# Moet AI review activeren
```

### Verificatie in Logs

Check of je dit ziet:
```
🤖 AI Agent commit detected!
Agent: TestAgent
Running enhanced AI code review...
```

## 🎯 Integratie met Quinn

Voor Quinn specifiek, update de task execution:

```yaml
# In .bmad-core/tasks/review-story.md
# Voeg toe aan task initialization:

setup:
  - source .bmad-core/init.sh
  - echo "Quinn QA Review Mode Active"
```

## 📊 Monitoring

Alle AI agent activities worden automatisch getracked:

```bash
# Bekijk metrics
python scripts/ai_metrics_tracker.py report

# Of start dashboard
streamlit run scripts/ai_metrics_tracker.py
```

## ❓ Troubleshooting

### Environment Variables Niet Gezet

```bash
# Debug commando
env | grep AI_AGENT

# Moet tonen:
# AI_AGENT_COMMIT=1
# AI_AGENT_NAME=<agent-naam>
```

### Review Wordt Niet Getriggerd

1. Check git hooks:
   ```bash
   ls -la .git/hooks/pre-commit
   # Moet executable zijn
   ```

2. Test manual:
   ```bash
   AI_AGENT_COMMIT=1 .git/hooks/pre-commit
   ```

### Agent Niet Herkend

Check `.bmad-core/config/agent-environment.sh` voor je agent naam in de case statement.

---

**Met deze setup hoef je NOOIT meer handmatig environment variables te zetten - alles gaat automatisch!** 🚀
