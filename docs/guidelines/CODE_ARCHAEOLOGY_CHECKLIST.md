# Code Archaeology Checklist

**Purpose**: Quick reference voor het verifiëren of features wel/niet geïmplementeerd zijn in brownfield codebases.

**Origin**: Lessons learned van DEF-39/DEF-13 analyse (2025-11-03) - Multiagent exploration concludeerde "niet geïmplementeerd" terwijl features volledig inline geïntegreerd waren.

---

## 🎯 Use This Checklist When

- [ ] Verifying Linear issue status ("Is feature X implemented?")
- [ ] Multiagent exploration concludeert "not found"
- [ ] Expected filename/component niet gevonden
- [ ] Before claiming "feature missing" to user/team

---

## ✅ Search Strategy (Execute In Order)

### 1️⃣ Search Exact UI Text (HIGHEST PRIORITY)

**What to do**: Grep voor user-visible text strings

```bash
# Examples from DefinitieAgent ontology feature:
grep -r "Voorgesteld:" .
grep -r "Waarom deze categorie" .
grep -r "Aanpassen?" .
grep -r "✓ Gebruik" .

# Generic pattern:
grep -r "<exact button/label text>" .
```

**Why**: UI text is most stable. User knows what they see. Filenames change, UI text doesn't.

**Success indicators**:
- ✅ Found in unexpected file (e.g., `tabbed_interface.py` not `ontology_widget.py`)
- ✅ Inline implementation discovered
- ❌ No results → Try next strategy

---

### 2️⃣ Check Main UI Entry Points

**What to do**: Target high-traffic UI files

```bash
# DefinitieAgent specific:
grep "<keyword>" src/ui/tabbed_interface.py
grep "<keyword>" src/ui/main.py
grep "<keyword>" src/main.py

# Generic pattern:
grep "<keyword>" <main_ui_file>
grep "<keyword>" <app_entry_point>
```

**Why**: Complex features often integrated in main UI, not standalone widgets.

**Common filenames**:
- `tabbed_interface.py` (Streamlit apps)
- `main.py`, `app.py` (FastAPI/Flask)
- `index.tsx`, `App.tsx` (React)
- `main_window.py` (Qt/Tkinter)

---

### 3️⃣ Search Function/Method Names

**What to do**: Wildcard search for related methods

```bash
# DefinitieAgent example:
grep -r "def.*category" src/ui/
grep -r "def.*ontolog" src/ui/
grep -r "def.*preview" src/ui/

# Generic pattern:
grep -r "def.*<keyword>" <target_dir>/
find . -name "*.py" -exec grep -l "def.*<keyword>" {} \;
```

**Why**: Methods reveal implementation even if file name unexpected.

---

### 4️⃣ Search Expected Filenames (LAST RESORT)

**What to do**: Try expected paths

```bash
# DefinitieAgent example:
find . -name "*ontology*widget*.py"
find . -name "*suggestion*.py"

# Generic:
find . -name "*<expected_name>*.<ext>"
```

**Why**: Filename expectations often wrong in brownfield code. Use as validation, not primary search.

---

## 🚫 Anti-Patterns to Avoid

| ❌ Don't Do This | ✅ Do This Instead |
|------------------|---------------------|
| Assume expected filename exists | Search UI text first |
| Grep only technical terms (`ontological_classifier`) | Grep user-visible text ("Voorgesteld:") |
| Stop after first search fails | Try all 4 strategies sequentially |
| Trust agent exploration alone | Validate findings with user |
| Conclude "not implemented" immediately | Complete full checklist first |

---

## 🤝 User Validation Step

**After completing search**: ALWAYS validate with user

```text
Template message:
"I searched for [feature] in:
- UI text strings: [results]
- Main UI files: [results]
- Method names: [results]
- Expected filenames: [results]

My conclusion: [implemented/not implemented]

Can you confirm if this matches your experience?
Did I miss any integration points?"
```

**Why**: User knows the codebase better. They'll catch inline implementations you missed.

---

## 📋 Before/After Example: DEF-39 & DEF-13

### ❌ Original (Incorrect) Analysis

**Search approach**:
1. Grep for `ontological_classifier` → Found backend
2. Look for `ontology_suggestion_widget.py` → Not found
3. Check `GenerationRequest` field → Found (nullable)
4. **Conclusion**: DEF-13 not implemented ❌

**Mistake**: Didn't search UI text. Didn't check `tabbed_interface.py`.

---

### ✅ Corrected Analysis

**Search approach**:
1. Grep for `"Voorgesteld:"` → Found in `tabbed_interface.py:545` ✅
2. Grep for `"Waarom deze categorie"` → Found in `tabbed_interface.py:547` ✅
3. Grep for `"Aanpassen?"` → Found in `tabbed_interface.py:551` ✅
4. Check `_render_category_preview()` method → Full implementation ✅
5. **Conclusion**: DEF-13 fully implemented ✅

**Key difference**: Started with UI text → Found inline implementation

---

## 🎓 Lessons Learned

1. **UI Text > Filenames**: Search what user sees, not what you expect
2. **Check Main UI Files**: `tabbed_interface.py` is goldmine for integrated features
3. **Inline != Missing**: Features don't need standalone files to be "implemented"
4. **Always Validate**: User feedback catches agent blind spots
5. **Complete Checklist**: Don't shortcut - run all 4 search strategies

---

## 🔗 References

- **Full methodology**: `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` → "Code Archaeology Search Strategies"
- **Project context**: `CLAUDE.md` → "Pattern Selection voor DefinitieAgent"
- **Case study**: `docs/analyses/ONTOLOGICAL_CATEGORIE_COMPREHENSIVE_EXPLORATION.md`
- **Validated by**: DEF-39 & DEF-13 analysis (2025-11-03)

---

## 🚀 Quick Start

**Copy-paste search commands**:

```bash
# 1. UI Text Search
grep -r "your_ui_text_here" .

# 2. Main UI Files
grep "keyword" src/ui/tabbed_interface.py src/ui/main.py src/main.py

# 3. Method Names
grep -r "def.*keyword" src/

# 4. Expected Filenames
find . -name "*expected_name*"
```

**Then**: Validate findings with user before concluding.

---

**Last Updated**: 2025-11-03
**Author**: BMad Master (via multiagent analysis lessons learned)
**Status**: Active guideline for all code archaeology tasks
