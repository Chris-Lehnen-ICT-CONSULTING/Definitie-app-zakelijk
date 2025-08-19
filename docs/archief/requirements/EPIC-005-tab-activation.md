# Epic 5: Tab Activatie

**Epic Goal**: Maak alle 10 UI tabs volledig functioneel.

**Business Value**: Unlock volledige applicatie functionaliteit voor power users.

**Total Story Points**: 21

**Target Sprint**: 3-4

## Current State

Van de 10 tabs zijn er momenteel slechts 3 werkend:
- ✅ Definition Generator
- ✅ History
- ✅ Export
- ❌ Management
- ❌ Orchestration
- ❌ Monitoring
- ❌ External Sources
- ❌ Web Lookup
- ❌ Prompt Viewer
- ❌ Custom Definition

## Stories

### STORY-005-01: Activeer Management Tab

**Story Points**: 3

**Als een** admin
**wil ik** systeem settings beheren
**zodat** ik de applicatie kan configureren.

#### Acceptance Criteria
- [ ] Temperature defaults instelbaar
- [ ] Model selectie opties
- [ ] Rate limiting configuratie
- [ ] Settings persistent

#### Implementation
```python
def management_tab():
    st.header("⚙️ Management Console")

    # System Configuration
    with st.expander("🔧 Systeem Configuratie", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            default_temp = st.slider(
                "Default Temperature",
                0.0, 1.0,
                st.session_state.get('default_temperature', 0.3),
                0.1
            )

            default_model = st.selectbox(
                "Default Model",
                ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                index=0
            )

        with col2:
            rate_limit = st.number_input(
                "API Calls per Minuut",
                1, 60,
                value=st.session_state.get('rate_limit', 10)
            )

            cache_ttl = st.number_input(
                "Cache TTL (seconden)",
                60, 3600,
                value=st.session_state.get('cache_ttl', 300)
            )

    # User Management (Phase 2)
    with st.expander("👥 Gebruikersbeheer", expanded=False):
        st.info("Gebruikersbeheer komt in versie 2.0")

    # Save Configuration
    if st.button("💾 Configuratie Opslaan"):
        save_configuration({
            'default_temperature': default_temp,
            'default_model': default_model,
            'rate_limit': rate_limit,
            'cache_ttl': cache_ttl
        })
        st.success("Configuratie opgeslagen!")
```

---

### STORY-005-02: Activeer Orchestration Tab

**Story Points**: 5

**Als een** power user
**wil ik** multi-agent workflows bouwen
**zodat** ik complexe taken kan automatiseren.

#### Acceptance Criteria
- [ ] Agent selectie interface
- [ ] Workflow builder UI
- [ ] Execution monitoring
- [ ] Results aggregatie

#### Workflow Builder Design
```python
def orchestration_tab():
    st.header("🎭 Multi-Agent Orchestration")

    # Workflow Builder
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Available Agents")
        agents = {
            "Definitie Generator": "generate_definition",
            "Validator": "validate_definition",
            "Enrichment": "enrich_content",
            "Translator": "translate_definition",
            "Exporter": "export_definition"
        }

        selected_agents = st.multiselect(
            "Selecteer Agents",
            list(agents.keys())
        )

    with col2:
        st.subheader("Workflow Pipeline")
        if selected_agents:
            # Visual workflow builder
            workflow = build_workflow_pipeline(selected_agents)

            # Workflow configuration
            for agent in selected_agents:
                with st.expander(f"Configure {agent}"):
                    render_agent_config(agent)

    # Execute Workflow
    if st.button("▶️ Execute Workflow"):
        execute_multi_agent_workflow(workflow)
```

#### Workflow Execution Engine
```python
class WorkflowEngine:
    async def execute(self, workflow: Workflow) -> WorkflowResult:
        results = {}

        for step in workflow.steps:
            agent = self.get_agent(step.agent_type)

            # Pass previous results as context
            context = self._build_context(results, step.dependencies)

            # Execute agent
            result = await agent.execute(
                input_data=step.input,
                context=context,
                config=step.config
            )

            results[step.id] = result

            # Update UI with progress
            self._update_progress(step.id, result)

        return WorkflowResult(results)
```

---

### STORY-005-03: Activeer Monitoring Tab

**Story Points**: 3

**Als een** developer
**wil ik** systeem metrics zien
**zodat** ik performance kan monitoren.

#### Acceptance Criteria
- [ ] API call counts
- [ ] Response time graphs
- [ ] Error rate tracking
- [ ] Cost calculator

#### Monitoring Dashboard
```python
def monitoring_tab():
    st.header("📊 System Monitoring")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "API Calls Today",
            value=get_metric("api_calls_today"),
            delta=get_metric_delta("api_calls")
        )

    with col2:
        st.metric(
            "Avg Response Time",
            value=f"{get_metric('avg_response_time')}s",
            delta=f"{get_metric_delta('response_time')}s"
        )

    with col3:
        st.metric(
            "Error Rate",
            value=f"{get_metric('error_rate')}%",
            delta=f"{get_metric_delta('error_rate')}%"
        )

    with col4:
        st.metric(
            "Estimated Cost",
            value=f"€{get_metric('daily_cost'):.2f}",
            delta=f"€{get_metric_delta('cost'):.2f}"
        )

    # Charts
    st.subheader("Performance Trends")

    # Response time chart
    response_times = get_response_time_data()
    st.line_chart(response_times)

    # API usage by endpoint
    usage_data = get_api_usage_data()
    st.bar_chart(usage_data)

    # Error log
    with st.expander("Recent Errors"):
        errors = get_recent_errors(limit=10)
        for error in errors:
            st.error(f"{error.timestamp}: {error.message}")
```

---

### STORY-005-04: Activeer External Sources Tab

**Story Points**: 3

**Als een** gebruiker
**wil ik** documenten uploaden
**zodat** ik eigen bronnen kan gebruiken.

#### Acceptance Criteria
- [ ] Drag-drop file upload
- [ ] PDF, DOCX, TXT support
- [ ] Progress indicators
- [ ] Document management

#### Document Upload Interface
```python
def external_sources_tab():
    st.header("📁 External Sources")

    # File Upload
    uploaded_files = st.file_uploader(
        "Sleep documenten hierheen of klik om te selecteren",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'csv'],
        key="doc_uploader"
    )

    if uploaded_files:
        # Process each file
        for file in uploaded_files:
            with st.spinner(f"Verwerken {file.name}..."):
                process_document(file)

        st.success(f"{len(uploaded_files)} documenten verwerkt!")

    # Document Library
    st.subheader("📚 Document Bibliotheek")

    documents = get_uploaded_documents()
    if documents:
        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"📄 {doc.filename}")
                st.caption(f"Geüpload: {doc.uploaded_at}")

            with col2:
                if st.button("👁️ Bekijk", key=f"view_{doc.id}"):
                    view_document(doc)

            with col3:
                if st.button("🗑️ Verwijder", key=f"del_{doc.id}"):
                    delete_document(doc)
```

---

### STORY-005-05: Activeer Web Lookup Tab

**Story Points**: 2

**Als een** gebruiker
**wil ik** online bronnen doorzoeken
**zodat** ik actuele informatie heb.

#### Acceptance Criteria
- [ ] Depends on Epic 2 completion
- [ ] Search interface werkend
- [ ] Results weergave
- [ ] Bron attributie

*Note: Deze story is afhankelijk van Epic 2 completion*

---

### STORY-005-06: Activeer Prompt Viewer Tab

**Story Points**: 2

**Als een** developer
**wil ik** gebruikte prompts zien
**zodat** ik kan debuggen en leren.

#### Acceptance Criteria
- [ ] Toon laatste 10 prompts
- [ ] Copy-to-clipboard functie
- [ ] Token count weergave
- [ ] Prompt templates zichtbaar

#### Prompt Viewer Implementation
```python
def prompt_viewer_tab():
    st.header("🔍 Prompt Viewer")

    # Get recent prompts
    prompts = get_recent_prompts(limit=10)

    if not prompts:
        st.info("Nog geen prompts gegenereerd")
        return

    # Prompt selector
    selected_prompt = st.selectbox(
        "Selecteer een prompt",
        options=range(len(prompts)),
        format_func=lambda x: f"{prompts[x].timestamp} - {prompts[x].type}"
    )

    if selected_prompt is not None:
        prompt = prompts[selected_prompt]

        # Display prompt details
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Prompt Content")
            st.code(prompt.content, language='text')

            # Copy button
            if st.button("📋 Copy to Clipboard"):
                pyperclip.copy(prompt.content)
                st.success("Gekopieerd!")

        with col2:
            st.subheader("Metadata")
            st.metric("Tokens", prompt.token_count)
            st.metric("Model", prompt.model)
            st.metric("Temperature", prompt.temperature)
            st.metric("Cost", f"€{prompt.estimated_cost:.4f}")
```

---

### STORY-005-07: Activeer Custom Definition Tab

**Story Points**: 3

**Als een** gebruiker
**wil ik** definities kunnen aanpassen
**zodat** ik maatwerk kan leveren.

#### Acceptance Criteria
- [ ] Rich text editor
- [ ] Version history
- [ ] Save/load functionaliteit
- [ ] Validatie na aanpassing

#### Custom Definition Editor
```python
def custom_definition_tab():
    st.header("✏️ Custom Definition Editor")

    # Load or create definition
    col1, col2 = st.columns([2, 1])

    with col1:
        term = st.text_input("Term", key="custom_term")

    with col2:
        action = st.radio(
            "Actie",
            ["Nieuwe definitie", "Bestaande laden"]
        )

    if action == "Bestaande laden" and term:
        definition = load_definition(term)
    else:
        definition = create_empty_definition()

    # Rich text editor
    edited_content = st.text_area(
        "Definitie",
        value=definition.content,
        height=300,
        key="definition_editor"
    )

    # Validation
    if st.button("✅ Valideer"):
        validation_result = validate_definition(edited_content)
        display_validation_results(validation_result)

    # Save options
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Opslaan"):
            save_custom_definition(term, edited_content)
            st.success("Definitie opgeslagen!")

    with col2:
        if st.button("📤 Exporteer"):
            export_custom_definition(term, edited_content)

    with col3:
        if st.button("🔄 Reset"):
            st.experimental_rerun()
```

## Definition of Done (Epic Level)

- [ ] Alle 7 tabs geactiveerd
- [ ] Consistente UI/UX
- [ ] Performance acceptabel
- [ ] Geen memory leaks
- [ ] Help documentatie per tab
- [ ] Mobile responsive (waar mogelijk)

## Technical Considerations

### State Management
- Gebruik st.session_state voor persistence
- Implementeer proper cleanup
- Voorkom circular dependencies

### Performance
- Lazy loading voor zware componenten
- Caching waar mogelijk
- Async operations voor I/O

### Security
- Input validatie op alle user inputs
- File upload size limits
- Rate limiting op expensive operations

## Success Metrics

- 100% tabs functioneel
- <2s load time per tab
- Zero crash reports
- User adoption van advanced features +40%

---
*Epic owner: Full Stack Team*
*Last updated: 2025-01-18*
