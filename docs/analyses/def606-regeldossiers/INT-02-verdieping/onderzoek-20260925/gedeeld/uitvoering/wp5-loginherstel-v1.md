# WP5 — loginherstel en concrete reviewhervatting

26 september 2026, na Chris' opdracht ‘ga verder’.

De normale `/Users/chrislehnen/.local/bin/codex login` is gestart; uitvoer meldt een lokale callbackserver op localhost:1455. De login wacht nog op afronding door Chris. Exec-sessie: 49438. Er zijn geen credentials gelezen of handmatig gewijzigd.

Het OpenAI-aanmeldscherm is zichtbaar geopend in de Codex-browser, tab 1, titel ‘Welkom terug - OpenAI’. Dit is de normale OAuth-flow van de CLI. De pagina vraagt om een aanmeldoptie/e-mailadres. De tab is als overdracht behouden; Chris is gevraagd de aanmelding te voltooien.

De volledige reviewopdracht is inmiddels klaar in wp-5-opdracht-codex-review-v2.md. App-HEAD 5fb535ee45671007e5cb4557509560c793eec290; binaire appdiff-SHA 957f41d59734cd1866931b47d59b7782b6c5b445e075eee469b5bf6a6e7efacd. Skill-HEAD 750068253a7389e201daedc5b9aa0afd5c0be032; diff-SHA 35e40ddbc4caffe65df3d45b7a06d5313c036cde04e29f43b84e5da12e19174a. De bestaande detached reviewwerkboom /private/tmp/def771-codex-review-1ZSCEP is normaal op de actuele app-HEAD gezet. Volledig testbewijs en de 67 op basis gereproduceerde failures zijn in de reviewopdracht opgenomen.

Na succesvolle login: derde eigen reviewstart uitvoeren met de volledige v2-opdracht, dezelfde voorgeschreven CLI-instellingen en nieuwe log-/rapportnamen. De twee eerdere starts hadden geen inhoudelijke review. Geen nieuwe reviewaanroep uitgevoerd zolang de aanmelding wacht. Bij succesvolle inhoudelijke review die sessie voor eventuele correcties behouden.

Actuele checklist: takenlijst-v5.md; testverslag: wp5-testbevindingen-v1.md; overige processtand: processtatus-uitvoering-v4.md. De testonderzoeken zijn afgerond, er draait geen pytest meer. Deze aanvulling actualiseert de oude handover met de toen nog actieve volledige testsuite.
