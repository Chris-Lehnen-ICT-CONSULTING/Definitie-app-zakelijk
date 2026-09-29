# DEF-835 — gerichte providercontrole bij runnerreview

28 september 2026. Aanleiding: uitvoerdersverslag noemt ongeverifieerde usagevelden. Dit document is feitelijke aanvulling voor correctie/review, geen toestemming voor calls.

De lokaal gebruikte officiële Anthropic-SDK 0.107.1 declareert in `anthropic/types/usage.py` naast de reeds toegelaten velden ook `inference_geo: Optional[str]` en `output_tokens_details: Optional[OutputTokensDetails]`. Bij output_tokens_details vermeldt de SDK expliciet dat output_tokens het inclusieve, gezaghebbende totaal voor facturering blijft. Het zijn dus bestaande velden, geen alleen hypothetische toekomstige uitbreiding.

De runner op dff713fd4 laat beide velden niet toe in USAGE_VELDEN. Aanwezigheid stopt de proef als onbekende usage. Dit is veilig weigeren, maar kan de geplande technische proef onnodig afbreken. De onafhankelijke reviewer beoordeelt de impact; een eventuele correctie gaat naar dezelfde Claude-uitvoerder, met tests op de werkelijk ondersteunde vorm. Geen ongecontroleerde verruiming van willekeurige usagevelden.

Geraadpleegde primaire bronnen:

- [Anthropic data residency](https://platform.claude.com/docs/en/manage-claude/data-residency): response-usage bevat inference_geo. Global gebruikt standaardprijzen; US-only heeft voor de relevante modellen 1,1× tarief. Workspace-defaults kunnen van global afwijken; een weggelaten requestveld bewijst geen global-uitvoering.
- [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing): dezelfde global/US-prijsafspraak.
- [Service tiers](https://platform.claude.com/docs/en/api/service-tiers?hsLang=en-us): auto kan Priority Tier kiezen. De huidige runner controleert de gerapporteerde tier na de call; hij pint geen request-tier vóór verzending. De proef mag dat niet omschrijven als vooraf technisch afgedwongen standaardtier.

Rechtstreeks openen van de volledige messages-API-documentatie gaf een toolgroottefout (>4 MB); de bovenstaande gerichte primaire bronnen en geïnstalleerde SDK zijn wel gelezen. Geen ontbrekende bron als gecontroleerd presenteren. Tokenmeting/thinking-type: de geïnstalleerde `message_count_tokens_params.py` ondersteunt ThinkingConfigParam; werkelijk providerantwoord blijft onderdeel van de live proef.

Coördinatorcontrole op de gecommitte runner: 40 passed in 2.07s, exit 0; log `bewijs/modelproef-coordinator-v1.log`. Dit bewijst offline gedrag, niet de hierboven nog open providervelden.
