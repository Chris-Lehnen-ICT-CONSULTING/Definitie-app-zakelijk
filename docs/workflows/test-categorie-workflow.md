# Test Procedure: Category Change Workflow

## Overview
This document describes how to test the complete category change workflow implementation to verify that:
1. The UI properly delegates to WorkflowService
2. The regeneration preview appears when appropriate
3. No st.rerun() occurs that would hide the preview
4. The UI responds correctly to WorkflowAction values

## Prerequisites
- Application running: `streamlit run src/main.py`
- Database contains at least one definition (or will generate a new one)

## Test Steps

### Test 1: Basic Category Change Flow

1. **Generate a Test Definition**
   - Navigate to the Definition Generator tab
   - Enter begrip: "testverificatie"
   - Enter context: "proces voor identiteitscontrole"
   - Click "Genereer Definitie"
   - Wait for generation to complete

2. **Observe Initial Category**
   - Look for the "🎯 Ontologische Categorie" section
   - Note the automatically determined category (likely "proces")
   - Verify the category reasoning is displayed

3. **Change the Category**
   - Click the "🔄 Wijzig Categorie" button
   - Select a different category from the dropdown (e.g., "📊 Resultaat/Uitkomst")
   - Click "✅ Toepassen"

4. **Verify Workflow Execution**
   - ✅ Success message should appear
   - ✅ NO page refresh should occur (no st.rerun)
   - ✅ Regeneration preview section should appear
   - ✅ Impact analysis should be displayed

### Test 2: Regeneration Preview Options

After changing the category, verify the regeneration preview shows:

1. **Category Change Overview**
   - Old category displayed
   - Arrow indicator
   - New category displayed

2. **Current Definition Preview**
   - Shows truncated current definition

3. **Impact Analysis**
   - List of expected impacts based on category change

4. **Three Action Buttons**
   - "🚀 Direct Regenereren" - generates new definition immediately
   - "🎯 Handmatig Aanpassen" - navigates to generator with context
   - "✅ Behoud Huidige" - keeps current definition with new category

### Test 3: Different Category Transitions

Test these specific transitions for different impact messages:

1. **Proces → Type**
   - Expected: "Focus verschuift van 'hoe' naar 'wat'"

2. **Type → Resultaat**
   - Expected: "Focus verschuift van object naar uitkomst"

3. **Same Category**
   - Expected: No action, error message about same category

### Test 4: Error Handling

1. **Unsaved Definition**
   - Change category before saving
   - Should work without database update

2. **Invalid Category**
   - Should not be possible via UI (dropdown constrained)

## Expected Results

### ✅ Success Indicators
- Category updates without page refresh
- Regeneration preview appears inline
- All three action buttons are functional
- Impact analysis is relevant to category change
- No duplicate UI elements after actions

### ❌ Failure Indicators
- Page refreshes after category change (st.rerun called)
- Regeneration preview doesn't appear
- Error messages without recovery options
- UI state inconsistency after actions

## Logging

Check the console/terminal for these log messages:

```
INFO - Category updated for definition X: proces → resultaat by web_user
INFO - Significant category change detected: ('proces', 'resultaat')
INFO - Category change event: {...}
```

## Architecture Verification

The implementation should follow this flow:
1. UI (DefinitionGeneratorTab) → calls WorkflowService
2. WorkflowService → orchestrates the change, returns CategoryChangeResult
3. CategoryChangeResult.action → determines UI behavior
4. UI responds to action without rerun when showing preview

## Notes

- The WorkflowService maintains separation of concerns
- No direct database access from UI components
- Business logic centralized in WorkflowService
- UI only handles presentation based on workflow results
