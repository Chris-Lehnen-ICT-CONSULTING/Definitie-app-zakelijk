# DEFINITION OF DONE

## Mandatory Checks (Every Item - No Exceptions)

- [ ] **Smoke test exists** (or existing test updated)
- [ ] **Manual test by developer** (actually use the feature)
- [ ] **No console errors** (check browser console / terminal)
- [ ] **Git commit** with clear message (feat/fix/refactor)
- [ ] **PAIN-TEST updated** (mark issue as resolved)

---

## Context-Specific Checks

### For Bug Fixes
- [ ] Root cause identified (not just symptom)
- [ ] Regression test added (prevents recurrence)

### For New Features
- [ ] Documentation updated (if non-trivial)
- [ ] Performance acceptable (<5s for user-facing actions)

### For Refactoring
- [ ] All existing tests still pass
- [ ] No behavior changes (unless intentional + documented)

---

## ⚠️ NOT DONE UNTIL ALL MANDATORY CHECKS ✅

If you can't check all boxes → Item goes back to DOING

---

**Checklist Usage:**
1. Copy checklist to your commit message or notes
2. Check boxes as you complete each item
3. Only mark item DONE in ACTIVE.md when ALL mandatory boxes checked

---

**Updated:** 2025-10-13
