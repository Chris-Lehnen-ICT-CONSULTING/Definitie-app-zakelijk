# INT-02 O2 — sleutelstatus na gestopte proef (v1)

30 september 2026. Chris meldde in deze chat: **“ik weet het al: de api key is verlopen”**. De eerder gebruikte waarde kwam uit de bestaande `.env` van de projectrepository en is niet in het dossier opgeslagen of afgedrukt. Er wordt geen nieuwe API-poging gedaan zolang geen vervangende sleutel via de normale lokale projectconfiguratie beschikbaar is.

De eerste kwalificatieproef stopte bij de C105-tokenmeting met `connection` / `AIServiceError`, zonder HTTP-status, modelinferentie of antwoord. Dat bewijs toont geen 401 of vervaldatum. De sleutelstatus is daarom een mededeling van de projecteigenaar; de exacte technische oorzaak van de gemelde verbindingsfout is daarmee nog niet uit de runnerlog bewezen. De PreToolUse-hook weigerde een afzonderlijke credentialvrije netwerkdiagnose; de beveiligingsinstellingen blijven intact.

Vervolggrens: Chris vervangt de verlopen sleutel lokaal via het bestaande secretbeheer of de project-`.env`, **zonder de waarde in chat of dossier te plaatsen**. Daarna blijft voor de nieuwe v2-proef het afzonderlijke akkoord op de exacte manifest- en gevallenhashes vereist. Alleen de bestaande Q1-runner mag dan eerst de regressiefase proberen, binnen het geaccordeerde budget en zonder automatische retries. De mislukte v1-proef en haar bewijs blijven bewaard.
