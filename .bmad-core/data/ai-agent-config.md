# AI Agent Configuration voor Code Review

## Automatische Code Review Setup

### Voor BMAD Agents

Alle BMAD AI agents moeten deze environment variables zetten voordat ze committen:

```bash
# In agent startup/config
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="<agent-naam>"
```

### Configuratie per Agent

#### Claude
```bash
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="Claude"
```

#### GitHub Copilot
```bash
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="Copilot"
```

#### Custom BMAD Agents
```bash
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="BMAD-${AGENT_ID}"
```

### Git Alias Setup

Voor makkelijker gebruik, voeg toe aan `.gitconfig`:

```gitconfig
[alias]
    ai-commit = !AI_AGENT_COMMIT=1 git commit
```

Dan kunnen agents gebruiken:
```bash
git ai-commit -m "AI: implemented feature X"
```

### Verificatie

Test of het werkt:
```bash
# Simuleer AI agent commit
AI_AGENT_COMMIT=1 AI_AGENT_NAME="TestAgent" git commit -m "test"
# Moet de enhanced AI review triggeren
```
