# Aanvulling bij GREEN-opdracht WP3

De coördinator heeft RED gecontroleerd: 92 failed, 19 passed, testhashes gelijk aan de logkop. De eerste shellfout blijft zichtbaar bewaard. Je routinekeuzes uit het RED-verslag zijn aanvaard: exacte recordtekst, WP1-contractversie voor het deelresultaat, getypeerd document, geen onverifieerbaar assessment bij fouten, hergebruik van toets_actualiteit.

Voer nu wp3-opdracht-claude-groen-v1.md uit binnen de negen geaccordeerde bestanden. De vijf aangetroffen bestaande testbestanden buiten de scope zijn nog NIET geaccordeerd. Wijzig ze niet. Leg hun verwachte failures door versie 2.3.0 en de specifiek toegestane INT-02-velden wel vast; dit is een verklaarde oude verwachting en geen aanleiding het nieuwe gedrag terug te draaien. De coördinator heeft een gebundeld voorstel aan Chris voorgelegd.

Neem daarom naast de GREEN-testfiles en gerichte regressies ook deze bestaande bestanden mee in één aparte controle: tests/unit/validation/test_validation_readiness.py en tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py, test_def772_int03_wrappers.py, test_def766_ess03_wrappers.py. Log volledig als wp3-claude-bestaande-versiepins-rood-v1.log. Er mogen geen andere onverwachte failures stil verdwijnen.

Je bent dezelfde Claude-uitvoerder; geen agents/reviewers/extra CLI's. Lees de TDD-skill via bestand /Users/chrislehnen/.agents/skills/test-driven-development/SKILL.md wanneer de Skill-tool ontbreekt. Stop na GREEN-verslag; geen commit/push.
