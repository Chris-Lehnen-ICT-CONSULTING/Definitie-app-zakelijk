# Toegankelijkheid en responsive gedrag

## Bewezen

- de primaire tabset exposeert tabrollen en ArrowRight veranderde de
  geselecteerde tab;
- bij 320, 390, 600, 768, 1024 en 1440 CSS-pixels was geen horizontale
  viewportoverflow zichtbaar in de geteste hoofdflow;
- drie actieve Streamlit-light-themecombinaties blijven onder 4,5:1:
  sidebar-success 4,044331:1, main-success 4,495615:1 en primaire knop
  3,301871:1 (`B044-005`);
- negen actieve calls gebruiken de verwijderingsgevoelige
  `use_container_width=True`-API; zeven emitten onder Streamlit 1.58 een
  deprecationwarning (`B044-006`);
- aanvullende concrete WCAG-defecten in actieve en archief-UI's staan als
  afzonderlijke accessibilityfindings in de canonieke CSV.

## Niet getest

Geen volledige VoiceOver/NVDA-run, forced-colors, echte 200%-zoomreflow,
Dynamic Type, fysieke touch targets of browsermatrix. Archief-HTML is statisch
beoordeeld en als dormant gelabeld waar geen actieve caller bestaat.
