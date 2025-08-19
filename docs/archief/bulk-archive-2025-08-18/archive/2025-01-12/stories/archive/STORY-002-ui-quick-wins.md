# STORY-002: UI Quick Wins Implementation

## User Story
Als een **eindgebruiker**
wil ik dat alle UI elementen correct werken zonder bugs
zodat ik een soepele gebruikerservaring heb bij het genereren van definities.

## Acceptance Criteria
- [ ] Widget key generator bug gefixed - geen random resets meer
- [ ] Metadata velden (context_type, versie) geactiveerd in UI
- [ ] Prompt viewer tab toont volledige prompt met copy knop
- [ ] Ontologische score zichtbaar in definitie output
- [ ] Developer tools tab met logging toggle werkend
- [ ] Aangepaste definitie edit mode functioneel

## Technical Notes

### Widget Key Fix
```python
# OLD - BROKEN
key = f"widget_{random.randint(1000, 9999)}"

# NEW - STABLE
def get_stable_widget_key(prefix: str, tab: str, index: int = 0) -> str:
    return f"{prefix}_{tab}_{index}"
```

### UI Components to Activate
1. **Metadata Fields**
   - Add context_type dropdown (proces/resultaat/type/exemplaar)
   - Add version display field
   - Connect to database fields

2. **Prompt Viewer**
   ```python
   with st.expander("🔍 Bekijk Prompt"):
       st.code(st.session_state.get('last_prompt', ''), language='text')
       if st.button("📋 Kopieer", key="copy_prompt"):
           pyperclip.copy(st.session_state.last_prompt)
           st.success("Prompt gekopieerd!")
   ```

3. **Score Display**
   ```python
   col1, col2 = st.columns(2)
   with col1:
       st.metric("Validatie Score", f"{validation_score}%")
   with col2:
       st.metric("Ontologie Score", f"{ontology_score:.1f}/10")
   ```

### Dependencies
- Fix session state management first
- Update UI component imports
- Add pyperclip for copy functionality

## QA Notes

### Test Scenarios
1. **Widget Stability Test**
   - Navigate between tabs rapidly
   - Verify form inputs retain values
   - Check no unexpected resets occur

2. **Metadata Fields Test**
   - Select different context types
   - Verify storage in database
   - Check display in history

3. **Prompt Viewer Test**
   - Generate definition
   - Open prompt viewer
   - Copy prompt and paste elsewhere
   - Verify complete prompt is shown

4. **Developer Tools Test**
   - Toggle logging on/off
   - Verify log output changes
   - Check performance impact

### Edge Cases
- Very long prompts (>10k chars)
- Special characters in prompts
- Switching tabs during generation
- Multiple browser tabs open

### Expected Behavior
- Widget values persist across tab switches
- All UI elements responsive and functional
- Copy buttons work across all browsers
- Scores display with proper formatting

## Definition of Done
- [ ] All UI components implemented
- [ ] No widget reset bugs
- [ ] Copy functionality works cross-browser
- [ ] UI elements match legacy styling
- [ ] Performance acceptable (<100ms response)
- [ ] Code reviewed and approved

## Priority
**High** - UI bugs severely impact user experience

## Estimated Effort
**5 story points** - 2 days of development work

## Sprint
Sprint 1 - Quick Wins

## Notes
- Reference legacy UI code in `centrale_module_definitie_kwaliteit_legacy.py`
- Maintain consistent styling with existing components
- Test on multiple browsers (Chrome, Firefox, Safari)

---
*Story generated from PRD Epic 1: Quick Wins & Stabilisatie*
