"""CON-02 — bronbasis: canonieke bronidentiteit en het broncontract (DEF-743).

Pure domeinlogica zonder Streamlit, database of AI-client. De evaluator
(`services.validation.evaluators.source_evidence`) en de beoordelingsservice
(`services.validation.source_assessment_service`) bouwen hierop; de
persistentielaag gebruikt de vingerafdruk- en normalisatiehelpers om een
opgeslagen beoordeling of uitzondering aan exact dezelfde invoer te binden.
"""
