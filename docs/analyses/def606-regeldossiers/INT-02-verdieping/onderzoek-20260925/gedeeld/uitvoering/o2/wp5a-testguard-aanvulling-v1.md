# WP5a — noodzakelijke herijking van één bestaande test

28 september 2026. De geaccordeerde WP5a-containerfactory is expliciet en optioneel; O1 mag geen automatische dienst of modelcall krijgen.

Actuele test tests/unit/validation/test_def835_int02_assessment_service.py:305–308:

```python
def test_dienst_wordt_niet_door_de_container_aangemaakt():
    container = (ROOT / "src/services/container.py").read_text(encoding="utf-8")
    assert "int02_assessment" not in container
    assert "Int02AssessmentService" not in container
```

Deze oude WP2-tekstguard verbiedt elk voorkomen van INT-02 in de containerbron en faalt dus ook voor de nu geaccordeerde expliciete factory. De productieroute hoeft hiervoor niet aangepast te worden.

Voorstel: in hetzelfde testbestand deze bestaande test behouden maar hernoemen/herijken naar het geldende gedrag: een gewone container/orchestrator maakt geen INT-02-dienst aan en start geen INT-02-aanroep; een expliciet aangevraagde factory met profiel en budget is toegestaan. Geen testgeval verwijderen, geen standaardactivering en geen zwakkere nulcall-eis. Claude CLI corrigeert, dezelfde WP5a-reviewer controleert de concrete aanvulling. Eerst de bestaande failure als RED, daarna gericht GREEN en toepasselijke regressie.

Dit raakt een achtste software/testbestand naast de zeven van WP5a, geraamd 10–30 regels. De oorspronkelijke >5-bestandenregel en expliciete WP5a-scope vragen daarom akkoord op deze concrete toevoeging. Andere twee failures uit test_performance_tracker worden afzonderlijk met de ongewijzigde basis vergeleken; geen reparatie daarvan in dit voorstel.
