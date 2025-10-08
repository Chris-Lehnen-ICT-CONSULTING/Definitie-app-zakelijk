# UI Classificatie Flows - Implementation Guide

**Datum**: 2025-10-07
**Doel**: Concrete UI code voorbeelden voor verschillende classificatie workflows

---

## 🎯 AANBEVOLEN HYBRIDE FLOW

Combinatie van **snelheid** (auto) + **controle** (override):

```python
# ============================================================
# src/ui/tabs/definition_generator_tab.py
# ============================================================

def _render_classification_section(self, begrip: str, org_ctx: str, jur_ctx: str):
    """Render classificatie sectie met auto + override."""

    st.markdown("### 🔶 Ontologische Classificatie")

    # ========================================
    # OPTIE 1: "Vertrouw AI" (default, snel)
    # ========================================
    use_auto = st.checkbox(
        "Automatische classificatie gebruiken (aanbevolen)",
        value=True,  # Default: trust AI
        key="use_auto_classification"
    )

    if use_auto:
        # PREVIEW mode (toon wat AI doet)
        with st.spinner("Analyseren..."):
            classification = self.definition_service.classify_begrip(
                begrip=begrip,
                org_context=org_ctx,
                jur_context=jur_ctx
            )

        # Toon AI resultaat (compact)
        confidence_emoji = "🟢" if classification.confidence > 0.7 else "🟡"

        st.success(f"""
        {confidence_emoji} **{classification.level.value.upper()}**
        ({classification.confidence:.0%} zekerheid)
        """)

        # Expandable details
        with st.expander("📊 Details tonen"):
            st.markdown(f"**Redenering**: {classification.rationale}")

            # Score breakdown
            if classification.test_scores:
                st.markdown("**Score verdeling:**")
                scores_df = pd.DataFrame([classification.test_scores])
                st.bar_chart(scores_df.T)

        # Return AI result
        return classification.level

    else:
        # ========================================
        # OPTIE 2: "Ik wil zelf kiezen" (override)
        # ========================================
        st.info("Je kunt de categorie handmatig selecteren:")

        # Eerst nog steeds AI suggestie ophalen (voor guidance)
        with st.spinner("Suggestie ophalen..."):
            classification = self.definition_service.classify_begrip(
                begrip=begrip,
                org_context=org_ctx,
                jur_context=jur_ctx
            )

        st.markdown(f"💡 **AI suggestie**: {classification.level.value} "
                   f"({classification.confidence:.0%})")

        # Manual selectbox
        manual_category = st.selectbox(
            "Kies categorie",
            options=["type", "proces", "resultaat", "exemplaar"],
            index=["type", "proces", "resultaat", "exemplaar"].index(
                classification.level.value
            ),
            help="""
            - **Type**: Algemene soort/klasse (bijv. 'toets', 'document')
            - **Proces**: Handeling/procedure (bijv. 'validatie', 'beoordeling')
            - **Resultaat**: Uitkomst/product (bijv. 'besluit', 'vergunning')
            - **Exemplaar**: Specifiek exemplaar (bijv. 'deze toets', 'het document')
            """,
            key="manual_category_select"
        )

        # Visual feedback als user override doet
        if manual_category != classification.level.value:
            st.warning(f"⚠️ Je hebt de AI suggestie overschreven: "
                      f"{classification.level.value} → {manual_category}")

        # Return user choice
        return OntologischeCategorie(manual_category)


async def _handle_definition_generation(self):
    """Main generation handler met classificatie."""

    # Collect basic inputs
    begrip = st.text_input("Begrip", key="begrip_input")
    org_ctx = st.text_area("Organisatorische context", key="org_ctx")
    jur_ctx = st.text_area("Juridische context", key="jur_ctx")

    if not begrip:
        st.warning("Voer een begrip in om te starten")
        return

    # ========================================
    # CLASSIFICATIE STAP (los van generatie!)
    # ========================================
    selected_category = self._render_classification_section(
        begrip=begrip,
        org_ctx=org_ctx,
        jur_ctx=jur_ctx
    )

    st.markdown("---")  # Visual separator

    # ========================================
    # GENERATIE STAP (met categorie)
    # ========================================
    st.markdown("### 📝 Definitie Genereren")

    if st.button("🚀 Genereer Definitie", type="primary"):
        with st.spinner("Definitie genereren..."):
            try:
                # Generate MET gekozen categorie
                result = await self.definition_service.generate_definition(
                    begrip=begrip,
                    context_dict={
                        "organisatie": org_ctx,
                        "juridisch": jur_ctx,
                    },
                    categorie=selected_category,  # ← Gebruikt classification
                    **self._get_generation_params()
                )

                # Display result
                if result.success:
                    st.success("✅ Definitie gegenereerd!")

                    # Show definition
                    st.markdown("#### Gegenereerde Definitie")
                    st.markdown(f"> {result.definition}")

                    # Show metadata (including category used)
                    with st.expander("ℹ️ Metadata"):
                        st.json({
                            "categorie": selected_category.value,
                            "tokens": result.metadata.get("tokens_used"),
                            "duration": f"{result.metadata.get('duration_ms')}ms"
                        })
                else:
                    st.error(f"❌ Fout bij genereren: {result.error_message}")

            except Exception as e:
                st.error(f"❌ Onverwachte fout: {str(e)}")
                logger.exception("Definition generation failed")
```

---

## 🎨 **VISUAL MOCKUP**

### **Versie A: Auto Mode (default)**

```
┌────────────────────────────────────────────────────────┐
│ 🔶 Ontologische Classificatie                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ☑ Automatische classificatie gebruiken (aanbevolen)   │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ 🟢 PROCES (85% zekerheid)                      │   │
│ │                                                 │   │
│ │ ▼ 📊 Details tonen                             │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
└────────────────────────────────────────────────────────┘
────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────┐
│ 📝 Definitie Genereren                                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│ [  🚀 Genereer Definitie  ]                            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### **Versie B: Manual Mode**

```
┌────────────────────────────────────────────────────────┐
│ 🔶 Ontologische Classificatie                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ☐ Automatische classificatie gebruiken (aanbevolen)   │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ Je kunt de categorie handmatig selecteren      │   │
│ │                                                 │   │
│ │ 💡 AI suggestie: proces (85%)                  │   │
│ │                                                 │   │
│ │ Kies categorie:                                 │   │
│ │ ┌──────────────────────────────────┐            │   │
│ │ │ proces              ▼            │            │   │
│ │ └──────────────────────────────────┘            │   │
│ │ ⓘ Type: Algemene soort/klasse                  │   │
│ │   Proces: Handeling/procedure                   │   │
│ │   ...                                           │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
└────────────────────────────────────────────────────────┘
────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────┐
│ 📝 Definitie Genereren                                 │
│ [  🚀 Genereer Definitie  ]                            │
└────────────────────────────────────────────────────────┘
```

---

## 📊 **USE CASE MATRIX**

| Scenario | Checkbox | User Experience | Category Used |
|----------|----------|----------------|---------------|
| **Normale flow** | ☑ Auto | Ziet AI suggestie, klikt genereer | AI (snel) |
| **Twijfel aan AI** | ☐ Manual | Ziet suggestie, kiest zelf | User override |
| **Expert user** | ☐ Manual | Weet al welke categorie | User direct |
| **Low confidence** | ☑ Auto | Ziet 🟡 50%, kan naar manual | AI maar visible |

---

## 🔄 **EDGE CASE HANDLING**

### **Edge Case 1: Lage Confidence (<60%)**

```python
if classification.confidence < 0.6:
    st.warning(f"""
    ⚠️ **Lage zekerheid ({classification.confidence:.0%})**

    De AI is onzeker over de classificatie. Overweeg om handmatig te kiezen.
    """)

    # Auto-switch to manual mode
    if st.button("Schakel over naar handmatige selectie"):
        st.session_state.use_auto_classification = False
        st.rerun()
```

### **Edge Case 2: ONBESLIST**

```python
# In classify_begrip (ServiceAdapter):
def classify_begrip(self, begrip, org_ctx, jur_ctx):
    result = self.classifier.classify(begrip, org_ctx, jur_ctx)

    if result.level == "ONBESLIST":
        # Policy: Forceer naar manual mode in UI
        return ClassificationResult(
            level=OntologischeCategorie.TYPE,  # Safe default
            confidence=0.3,  # Low confidence triggers warning
            rationale=(
                f"Classificatie onzeker. Oorspronkelijk: {result.rationale}. "
                f"Standaard ingesteld op TYPE - controleer handmatig."
            ),
            needs_manual_review=True  # Flag for UI
        )

    return result
```

```python
# In UI:
if classification.needs_manual_review:
    st.error("""
    🚫 **Handmatige review vereist**

    De AI kon geen betrouwbare classificatie maken.
    Schakel over naar handmatige modus.
    """)
    # Force manual mode
    st.session_state.use_auto_classification = False
```

---

## 🎯 **BEST PRACTICES**

### **1. Default naar Auto (trust AI)**

```python
# GOED: Meeste users willen gewoon snel werken
use_auto = st.checkbox("Automatisch", value=True)  # ← Default True

# SLECHT: Forceer users om elke keer te kiezen
use_auto = st.checkbox("Automatisch", value=False)  # ← Te omslachtig
```

### **2. Toon Rationale (transparantie)**

```python
# GOED: User begrijpt waarom AI deze keuze maakte
st.markdown(f"**Redenering**: {classification.rationale}")

# SLECHT: Black box
# (geen uitleg)
```

### **3. Easy Override (one-click)**

```python
# GOED: Checkbox toggle
if not use_auto:
    manual_category = st.selectbox(...)  # One click to override

# SLECHT: Forceer herstart of complex menu
```

### **4. Visual Feedback (confidence)**

```python
# GOED: Emoji indicators
emoji = "🟢" if conf > 0.7 else "🟡" if conf > 0.5 else "🔴"
st.success(f"{emoji} {category} ({conf:.0%})")

# SLECHT: Alleen tekst
st.write(f"{category} {conf}")  # Minder duidelijk
```

---

## 🚀 **MIGRATION PATH**

### **Phase 1: Backward Compatible (Week 1)**

```python
# ServiceAdapter blijft werken met oude UI
async def generate_definition(self, begrip, categorie=None, ...):
    if categorie is None:
        # Auto-classify (silent, zoals nu)
        categorie = self.classify_begrip(begrip, ...).level
    # Continue...
```

**Result**: Bestaande UI blijft werken (geen breaking changes)

---

### **Phase 2: Add Preview (Week 2)**

```python
# Nieuwe UI: Toon wat AI doet (maar nog auto-accept)
classification = service.classify_begrip(begrip)
st.info(f"Categorie: {classification.level.value}")
await service.generate_definition(begrip, categorie=classification.level)
```

**Result**: Transparantie, maar geen extra clicks

---

### **Phase 3: Add Override (Week 3)**

```python
# Nieuwe UI: Checkbox voor manual mode
if use_auto:
    category = classification.level  # AI
else:
    category = st.selectbox(...)  # User choice

await service.generate_definition(begrip, categorie=category)
```

**Result**: Volledige controle voor power users

---

## 📊 **A/B TEST METRICS**

Als je wilt testen welke UX het beste werkt:

```python
# Track user behavior
metrics = {
    "auto_mode_usage": 0,  # % users die checkbox aanlaat
    "manual_overrides": 0,  # % users die categorie wijzigt
    "low_confidence_switches": 0,  # % users die bij <60% naar manual gaat
    "regenerations": 0,  # % users die regenereert met andere categorie
}

# Goal: Optimize for speed + control balance
# Sweet spot: 80% auto, 20% manual (power users)
```

---

## 🎓 **KEY TAKEAWAYS**

1. **Automatisch = Default** - Meeste users vertrouwen AI
2. **Transparantie = Must** - Toon altijd WAT en WAAROM
3. **Override = Safety Net** - Voor edge cases en expert users
4. **Progressive Disclosure** - Start simpel (auto), expand on demand (manual)
5. **Visual Feedback** - Emoji's, kleuren, confidence scores

---

**END OF GUIDE**
