# 🚨 IMMEDIATE WORKAROUNDS - Context Flow Issues

**Created:** 2025-09-04
**Severity:** CRITICAL
**Affected Users:** All users requiring justice domain context in definitions
**Until Fixed:** Use these workarounds to continue working

## Problem Summary

The system currently has two critical bugs preventing proper context usage:
1. **Context fields are NOT passed to AI prompts** - your selections are ignored
2. **"Anders..." option causes crashes** - custom entries break the application

## Workaround 1: Manual Context Addition

Since context fields are not being passed to the AI, you must manually add context to your term.

### Instead of:
```
Term: voorlopige hechtenis
Organisatorische Context: [OM, Rechtspraak]
Juridische Context: [Strafrecht]
Wettelijke Basis: [Wetboek van Strafvordering]
```

### Use this format:
```
Term: voorlopige hechtenis binnen OM en Rechtspraak context,
      specifiek voor Strafrecht volgens Wetboek van Strafvordering
```

### Examples:

**Criminal Law Term:**
```
Instead of: "dwangsom"
Use: "dwangsom in context van Strafrecht en OM procedures volgens Wetboek van Strafvordering"
```

**Administrative Law Term:**
```
Instead of: "bezwaarschrift"
Use: "bezwaarschrift binnen Bestuursrecht context voor DJI volgens Algemene wet bestuursrecht"
```

**Migration Law Term:**
```
Instead of: "vreemdelingenbewaring"
Use: "vreemdelingenbewaring in Migratierecht context voor DJI en KMAR volgens Vreemdelingenwet"
```

## Workaround 2: Avoiding "Anders..." Crashes

**DO NOT USE "Anders..." option** - it will crash the application.

### Alternative Approaches:

1. **Include custom context in the term itself:**
   ```
   Term: datalek binnen context van nieuwe EU AI Act regelgeving
   ```

2. **Use closest matching option then edit definition:**
   - Select nearest equivalent from dropdown
   - Generate definition
   - Manually edit to add specific context

3. **Use organizational context creatively:**
   ```
   If you need "Raad voor de Kinderbescherming":
   - Select "Justitie en Veiligheid" (parent organization)
   - Add specifics in the term: "ondertoezichtstelling door Raad voor de Kinderbescherming"
   ```

## Workaround 3: Ensuring Compliance Without System Context

Since ASTRA compliance requires context documentation, maintain it manually:

### Create a context record alongside your definition:
```markdown
**Term:** [your term]
**Definition:** [generated definition]

**Context Gebruikt:**
- Organisatorisch: [your selections]
- Juridisch: [your selections]
- Wettelijke Basis: [your selections]
- Datum/Tijd: [timestamp]
- Gebruiker: [your name]
```

### Example Compliance Record:
```markdown
**Term:** voorlopige hechtenis
**Definition:** [AI generated text]

**Context Gebruikt:**
- Organisatorisch: OM, Rechtspraak, KMAR
- Juridisch: Strafrecht, Europees recht
- Wettelijke Basis: Sv art. 63-88, EVRM art. 5
- Datum/Tijd: 2025-09-04 14:30
- Gebruiker: Juridisch Analist
```

## Workaround 4: Batch Processing Strategy

If you have multiple definitions to create:

1. **Prepare enriched terms list:**
   ```csv
   voorlopige hechtenis,OM/Rechtspraak/Strafrecht/Sv
   dwangsom,OM/Bestuursrecht/Awb
   vreemdelingenbewaring,DJI/KMAR/Migratierecht/Vw
   ```

2. **Process with context in term:**
   - Copy full enriched term into input field
   - Generate definition
   - Extract clean term for saving

## Workaround 5: Testing Your Context

To verify if context is being passed (for developers/testers):

1. Enable "Debug Mode" if available
2. Check the prompt in debug output
3. Look for these sections:
   ```
   Organisatorische context: [should show your selections]
   Juridische context: [should show your selections]
   Wettelijke basis: [should show your selections]
   ```

If these are empty or missing, the bug is still present.

## Temporary Quality Checklist

Until the system properly handles context, manually verify each definition:

- [ ] Definition mentions the organizational context
- [ ] Legal framework is referenced
- [ ] Juridical domain is clear
- [ ] No generic definitions without justice context
- [ ] Compliance record created for audit trail

## Support Contacts

If these workarounds don't help:
- **Technical Support:** Contact Development Team
- **Business Questions:** Contact Business Analyst
- **Compliance Issues:** Contact Compliance Officer

## Status Updates

Check for updates at:
- [Epic CFR Status](./stories/MASTER-EPICS-USER-STORIES.md#epic-cfr-context-flow-refactoring)
- [Bug CFR-BUG-001](./stories/MASTER-EPICS-USER-STORIES.md#bug-report-cfr-bug-001)
- [Bug CFR-BUG-002](./stories/MASTER-EPICS-USER-STORIES.md#bug-report-cfr-bug-002)

## Expected Resolution

**Phase 1 Fix:** Week of 2025-09-09 (context mapping)
**Phase 2 Fix:** Week of 2025-09-16 (Anders... option)
**Full Resolution:** By 2025-09-30 (complete refactoring)

---

**Note:** These are TEMPORARY workarounds. The development team is actively working on permanent fixes as outlined in Epic CFR. Thank you for your patience.
