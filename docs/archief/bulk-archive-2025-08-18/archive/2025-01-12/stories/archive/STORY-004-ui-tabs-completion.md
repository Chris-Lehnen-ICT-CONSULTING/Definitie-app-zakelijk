# STORY-004: Complete UI Tab Activation

## User Story
Als een **power user**
wil ik toegang tot alle 10 UI tabs met volledige functionaliteit
zodat ik alle features van de applicatie kan gebruiken voor mijn werk.

## Acceptance Criteria
- [ ] Management tab volledig functioneel
- [ ] Orchestratie tab werkend met multi-agent view
- [ ] Monitoring tab toont real-time metrics
- [ ] Externe Bronnen tab verbeterd met drag-drop
- [ ] Web Lookup tab werkend met UTF-8 fix
- [ ] Alle tabs hebben consistente styling en layout

## Technical Notes

### Tabs to Implement

1. **Management Tab** (`management_tab.py`)
   ```python
   def management_tab():
       st.header("📊 Management")

       # Configuration section
       with st.expander("⚙️ Configuratie"):
           temperature = st.slider("Default Temperature", 0.0, 1.0, 0.3)
           model = st.selectbox("Default Model", ["gpt-4", "gpt-3.5-turbo"])

       # User management (future)
       with st.expander("👥 Gebruikers"):
           st.info("Gebruikersbeheer komt in versie 2.0")

       # System stats
       with st.expander("📈 Systeem Statistieken"):
           show_system_stats()
   ```

2. **Orchestration Tab** (`orchestration_tab.py`)
   ```python
   def orchestration_tab():
       st.header("🎭 Multi-Agent Orchestratie")

       # Agent selection
       agents = st.multiselect(
           "Selecteer agents",
           ["Definitie", "Validatie", "Enrichment", "Export"]
       )

       # Workflow builder
       if agents:
           build_workflow(agents)
   ```

3. **Monitoring Tab** (`monitoring_tab.py`)
   ```python
   def monitoring_tab():
       st.header("📈 Monitoring Dashboard")

       # Real-time metrics
       col1, col2, col3 = st.columns(3)
       with col1:
           st.metric("API Calls Today", 142)
       with col2:
           st.metric("Avg Response Time", "6.3s")
       with col3:
           st.metric("Cache Hit Rate", "73%")

       # Charts
       show_performance_charts()
   ```

4. **External Sources Tab** (`external_sources_tab.py`)
   ```python
   def external_sources_tab():
       st.header("🌐 Externe Bronnen")

       # Drag-drop upload
       uploaded_files = st.file_uploader(
           "Sleep documenten hierheen",
           accept_multiple_files=True,
           type=['pdf', 'docx', 'txt']
       )

       if uploaded_files:
           process_documents(uploaded_files)
   ```

5. **Web Lookup Tab** (`web_lookup_tab.py`)
   ```python
   def web_lookup_tab():
       st.header("🔍 Web Lookup")

       term = st.text_input("Zoekterm")
       sources = st.multiselect(
           "Bronnen",
           ["wetten.nl", "officielebekendmakingen.nl", "rechtspraak.nl"]
       )

       if st.button("Zoeken"):
           # Fixed encoding
           results = search_with_encoding_fix(term, sources)
           display_results(results)
   ```

### Implementation Priority
1. Management & Orchestration (core functionality)
2. External Sources & Web Lookup (user requested)
3. Monitoring (nice to have)

### Common Components
- Use consistent header styling
- Implement loading states
- Add help tooltips
- Use session state for persistence

## QA Notes

### Test Scenarios
1. **Tab Navigation Test**
   - Click through all 10 tabs
   - Verify no errors or blank screens
   - Check loading times

2. **Functionality Test per Tab**
   - Management: Change settings and verify persistence
   - Orchestration: Build and execute workflow
   - Monitoring: Verify real-time updates
   - External Sources: Upload various file types
   - Web Lookup: Search with special characters

3. **Integration Test**
   - Upload document in External Sources
   - Use content in Definition Generator
   - Verify in History tab

### Edge Cases
- Large file uploads (>10MB)
- Invalid file formats
- Network failures during web lookup
- Rapid tab switching
- Multiple concurrent uploads

### Expected Behavior
- All tabs load within 1 second
- Clear error messages for failures
- Graceful degradation when services unavailable
- Consistent UI across all tabs
- Session state preserved when switching

## Definition of Done
- [ ] All 5 remaining tabs implemented
- [ ] Consistent styling applied
- [ ] Loading states implemented
- [ ] Error handling complete
- [ ] Help documentation added
- [ ] Integration tests passing
- [ ] Performance acceptable

## Priority
**High** - Core feature completeness

## Estimated Effort
**13 story points** - 5 days of development

## Sprint
Sprint 2-3 - Feature Completeness

## Dependencies
- Legacy code reference for UI patterns
- Web lookup service must be fixed first
- File processing utilities needed

## Notes
- Reference legacy implementation for exact functionality
- Maintain Streamlit best practices
- Consider mobile responsiveness
- Add keyboard shortcuts where applicable

---
*Story generated from PRD Epic 3: UI Completeness*
