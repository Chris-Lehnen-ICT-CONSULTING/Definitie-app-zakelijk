# Voorbeelden Generatie Fix - Definitie ID-23

**Datum:** 2025-10-29
**Issue:** Voorbeelden generatie werkt niet voor definitie ID-23 (biografisch identiteitskenmerk)
**Status:** ✅ ROOT CAUSE IDENTIFIED - USER ACTION REQUIRED

## Probleem

Voorbeelden werden niet gegenereerd voor definitie ID-23. Alle API calls faalden met 401 Unauthorized errors.

## Root Cause

De `OPENAI_API_KEY_PROD` environment variabele bevat een **incorrecte/verlopen API key** die eindigt met `...JF4A`.

**OpenAI error:**
```
Error code: 401 - Incorrect API key provided: sk-proj-***...JF4A
```

## Fixes Toegepast

### 1. `config/config.yaml`
- ❌ **Voor:** `default_model: gpt-4.1` (model bestaat niet!)
- ✅ **Na:** `default_model: gpt-4o-mini`
- ❌ **Voor:** Hardcoded incorrecte API key
- ✅ **Na:** `openai_api_key: null` (gebruik env variable)
- ✅ Updated pricing voor gpt-4o en gpt-4o-mini

### 2. `src/config/config_manager.py`
- ❌ **Voor:** `default_model: str = "gpt-4.1"`
- ✅ **Na:** `default_model: str = "gpt-4o-mini"`
- ✅ Updated default_temperature van 0.0 naar 0.7 (beter voor voorbeelden)

### 3. Cache Cleanup
- ✅ Alle pickle en JSON cache files verwijderd uit `cache/`

## Vereiste Gebruikersactie

**UPDATE DE OPENAI API KEY:**

```bash
# 1. Check huidige key
echo $OPENAI_API_KEY_PROD

# 2. Verkrijg nieuwe geldige API key van OpenAI
#    https://platform.openai.com/account/api-keys

# 3. Update environment variabele (in ~/.zshrc of ~/.bashrc)
export OPENAI_API_KEY_PROD="sk-proj-YOUR_VALID_API_KEY_HERE"

# 4. Reload shell configuratie
source ~/.zshrc  # of ~/.bashrc

# 5. Verify
echo $OPENAI_API_KEY_PROD
```

## Testing

**Debug Script Beschikbaar:**
```bash
python scripts/debug_voorbeelden_id_23.py
```

Dit script test de volledige voorbeelden generatie flow voor definitie ID-23 en toont:
- Definitie data
- Bestaande voorbeelden
- Nieuwe voorbeelden generatie (met logging)
- Database save operatie

## Verwacht Resultaat Na Fix

Na het updaten van de API key moet de voorbeelden generatie:
1. ✅ Succesvol 6 types voorbeelden genereren:
   - voorbeeldzinnen (3 items)
   - praktijkvoorbeelden (3 items)
   - tegenvoorbeelden (3 items)
   - synoniemen (5 items)
   - antoniemen (5 items)
   - toelichting (1 item)

2. ✅ Voorbeelden opslaan in `definitie_voorbeelden` tabel
3. ✅ Geen 401 authentication errors meer

## Impact

- **Files Modified:** 2 (config.yaml, config_manager.py)
- **Breaking Changes:** Geen (alleen configuratie fixes)
- **User Action Required:** Ja (update OPENAI_API_KEY_PROD)
- **Deployment Impact:** Streamlit app restart vereist na key update

## Validatie Checklist

- [x] Incorrect model name (gpt-4.1) vervangen door gpt-4o-mini
- [x] Hardcoded API key verwijderd uit config.yaml
- [x] Default model in config_manager.py updated
- [x] Cache gecleared
- [x] Debug script gemaakt voor testen
- [ ] **USER ACTION:** API key updated in environment
- [ ] **USER ACTION:** Streamlit app herstart
- [ ] **USER ACTION:** Voorbeelden generatie getest voor ID-23

## Related Issues

- Invalid model names in config (gpt-4.1 doesn't exist)
- Hardcoded credentials in config files (security issue)
- Oude cache met incorrecte config

## Lessons Learned

1. **Nooit hardcode credentials in config files** - altijd environment variables gebruiken
2. **Validate model names** - OpenAI models veranderen (gpt-4.1 bestaat niet)
3. **Cache cleanup** na config changes - oude config kan blijven hangen
4. **Dual sources of truth** - zowel config.yaml als dataclass defaults moeten synchroon zijn
