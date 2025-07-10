"""
Context Selector Component - Enhanced multi-select context management.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ui.session_state import SessionStateManager


@dataclass 
class ContextPreset:
    """Voorgedefinieerde context combinatie."""
    name: str
    organisatorische_context: List[str]
    juridische_context: List[str]
    wettelijke_basis: List[str]
    description: str = ""


class ContextSelector:
    """Enhanced context selector met presets en validation."""
    
    def __init__(self):
        """Initialiseer context selector."""
        self.presets = self._load_context_presets()
        self.validation_rules = self._load_validation_rules()
    
    def render(self) -> Dict[str, Any]:
        """
        Render context selector interface.
        
        Returns:
            Dictionary met geselecteerde context data
        """
        # Preset selector
        selected_preset = self._render_preset_selector()
        
        if selected_preset:
            # Load preset values
            context_data = self._apply_preset(selected_preset)
        else:
            # Manual selection
            context_data = self._render_manual_selector()
        
        # Validation en feedback
        self._render_context_validation(context_data)
        
        return context_data
    
    def _render_preset_selector(self) -> Optional[ContextPreset]:
        """Render preset selectie."""
        st.markdown("#### 🎯 Snelle Selectie")
        
        preset_options = ["Handmatig selecteren..."] + [p.name for p in self.presets]
        
        selected_name = st.selectbox(
            "Kies een voorgedefinieerde context combinatie:",
            options=preset_options,
            help="Selecteer een veelgebruikte context combinatie of kies handmatig"
        )
        
        if selected_name and selected_name != "Handmatig selecteren...":
            preset = next((p for p in self.presets if p.name == selected_name), None)
            if preset:
                st.info(f"💡 {preset.description}")
                return preset
        
        return None
    
    def _apply_preset(self, preset: ContextPreset) -> Dict[str, Any]:
        """Pas voorgedefinieerde context toe."""
        st.markdown("#### ✅ Geselecteerde Context")
        
        # Show preset details
        with st.expander("Context details", expanded=True):
            st.write(f"**Organisatorisch:** {', '.join(preset.organisatorische_context)}")
            st.write(f"**Juridisch:** {', '.join(preset.juridische_context)}")
            st.write(f"**Wettelijk:** {', '.join(preset.wettelijke_basis)}")
        
        # Option to modify
        if st.checkbox("🔧 Aanpassen", help="Wijzig de geselecteerde context"):
            return self._render_manual_selector(
                default_org=preset.organisatorische_context,
                default_jur=preset.juridische_context,
                default_wet=preset.wettelijke_basis
            )
        
        return {
            "organisatorische_context": preset.organisatorische_context,
            "juridische_context": preset.juridische_context, 
            "wettelijke_basis": preset.wettelijke_basis
        }
    
    def _render_manual_selector(
        self, 
        default_org: List[str] = None,
        default_jur: List[str] = None,
        default_wet: List[str] = None
    ) -> Dict[str, Any]:
        """Render handmatige context selectie."""
        st.markdown("#### 🛠️ Handmatige Selectie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Organisatorische context
            org_options = [
                "OM", "ZM", "Reclassering", "DJI", "NP", "Justid",
                "KMAR", "FIOD", "CJIB", "Strafrechtketen", "Migratieketen",
                "Justitie en Veiligheid"
            ]
            
            selected_org = st.multiselect(
                "📋 Organisatorische context",
                options=org_options,
                default=default_org or [],
                help="Selecteer één of meerdere organisaties"
            )
            
            # Custom org context
            custom_org = st.text_input(
                "Aangepaste organisatorische context",
                placeholder="Voer andere organisatie in..."
            )
            
            if custom_org.strip():
                selected_org.append(custom_org.strip())
            
            # Wettelijke basis
            wet_options = [
                "Wetboek van Strafvordering (huidige versie)",
                "Wetboek van strafvordering (nieuwe versie)",
                "Wet op de Identificatieplicht",
                "Wet op de politiegegevens",
                "Wetboek van Strafrecht",
                "Algemene verordening gegevensbescherming"
            ]
            
            selected_wet = st.multiselect(
                "📜 Wettelijke basis",
                options=wet_options,
                default=default_wet or [],
                help="Selecteer relevante wetgeving"
            )
            
            # Custom legal basis
            custom_wet = st.text_input(
                "Aangepaste wettelijke basis",
                placeholder="Voer andere wetgeving in..."
            )
            
            if custom_wet.strip():
                selected_wet.append(custom_wet.strip())
        
        with col2:
            # Juridische context
            jur_options = [
                "Strafrecht", "Civiel recht", "Bestuursrecht", 
                "Internationaal recht", "Europees recht", "Migratierecht"
            ]
            
            selected_jur = st.multiselect(
                "⚖️ Juridische context",
                options=jur_options,
                default=default_jur or [],
                help="Selecteer juridische gebieden"
            )
            
            # Custom juridical context
            custom_jur = st.text_input(
                "Aangepaste juridische context",
                placeholder="Voer ander rechtsgebied in..."
            )
            
            if custom_jur.strip():
                selected_jur.append(custom_jur.strip())
            
            # Additional metadata
            st.markdown("##### 📝 Metadata")
            
            voorsteller = st.text_input(
                "Voorgesteld door",
                value=SessionStateManager.get_value("voorsteller", "")
            )
            
            ketenpartners = st.multiselect(
                "Akkoord ketenpartners",
                options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"],
                help="Partners die akkoord zijn"
            )
            
            # Store metadata in session
            SessionStateManager.set_value("voorsteller", voorsteller)
            SessionStateManager.set_value("ketenpartners", ketenpartners)
        
        return {
            "organisatorische_context": selected_org,
            "juridische_context": selected_jur,
            "wettelijke_basis": selected_wet,
            "voorsteller": voorsteller,
            "ketenpartners": ketenpartners
        }
    
    def _render_context_validation(self, context_data: Dict[str, Any]):
        """Render context validation en feedback."""
        issues = []
        suggestions = []
        
        # Check voor verplichte velden
        if not context_data.get("organisatorische_context"):
            issues.append("❌ Organisatorische context is verplicht")
        
        # Check voor context combinaties
        org_contexts = context_data.get("organisatorische_context", [])
        jur_contexts = context_data.get("juridische_context", [])
        
        # Context logic validation
        if "KMAR" in org_contexts and "Strafrecht" not in jur_contexts:
            suggestions.append("💡 KMAR gebruikt meestal Strafrecht context")
        
        if "DJI" in org_contexts and not any("Straf" in j for j in jur_contexts):
            suggestions.append("💡 DJI gebruikt meestal strafrecht gerelateerde context")
        
        # Show validation results
        if issues:
            for issue in issues:
                st.error(issue)
        
        if suggestions:
            with st.expander("💡 Context Suggesties", expanded=False):
                for suggestion in suggestions:
                    st.info(suggestion)
        
        # Show context strength indicator
        if org_contexts and (jur_contexts or context_data.get("wettelijke_basis")):
            st.success("✅ Context configuratie is compleet")
    
    def _load_context_presets(self) -> List[ContextPreset]:
        """Laad voorgedefinieerde context presets."""
        return [
            ContextPreset(
                name="DJI Strafrecht",
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafvordering (huidige versie)", "Wetboek van Strafrecht"],
                description="Standaard context voor DJI strafrecht definities"
            ),
            ContextPreset(
                name="OM Vervolging",
                organisatorische_context=["OM"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafvordering (huidige versie)"],
                description="Context voor OM vervolgingsdefinities"
            ),
            ContextPreset(
                name="KMAR Identificatie",
                organisatorische_context=["KMAR"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wet op de Identificatieplicht", "Wet op de politiegegevens"],
                description="Context voor KMAR identificatie procedures"
            ),
            ContextPreset(
                name="Ketenbreed Strafrecht",
                organisatorische_context=["OM", "DJI", "KMAR", "CJIB"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafvordering (huidige versie)"],
                description="Brede ketencontext voor strafrecht definities"
            ),
            ContextPreset(
                name="Privacy & Gegevensbescherming",
                organisatorische_context=["OM", "DJI", "KMAR"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Algemene verordening gegevensbescherming", "Wet op de politiegegevens"],
                description="Context voor privacy en gegevensbescherming"
            )
        ]
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Laad context validatie regels."""
        return {
            "required_fields": ["organisatorische_context"],
            "suggested_combinations": {
                "KMAR": {"juridische_context": ["Strafrecht"]},
                "DJI": {"juridische_context": ["Strafrecht"]},
                "OM": {"juridische_context": ["Strafrecht"]}
            }
        }
    
    def save_as_preset(self, name: str, context_data: Dict[str, Any], description: str = ""):
        """Sla huidige context op als preset."""
        # TODO: Implement preset saving to database or config file
        st.success(f"Context preset '{name}' opgeslagen!")


def render_context_selector() -> Dict[str, Any]:
    """Standalone context selector rendering."""
    selector = ContextSelector()
    return selector.render()