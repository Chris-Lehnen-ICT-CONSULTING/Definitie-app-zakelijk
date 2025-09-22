id: US-204
titel: UI DataFrame type-safety (ArrowTypeError fix)

Doel
- Dtypes afdwingen (kolom 'status' e.a.) vóór Streamlit render om ArrowTypeError te voorkomen.

Waarom
- Logs tonen ArrowTypeError door mixed types (int/bytes) in DataFrame; belemmert gebruikservaring en debugging.

Scope
- Normaliseer types (string/categorical) in UI pipeline.
- Toevoegen tests met gemengde input.

Acceptatiecriteria
- 0 ArrowTypeErrors in UI smoke suite.

