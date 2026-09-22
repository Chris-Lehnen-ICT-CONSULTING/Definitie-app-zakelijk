ESS-03 vroeg om serienummers of andere identifiers als bewijs voor onderscheidbare instanties. De vijf definitievaardigheden volgen nu dezelfde telbaarheidsnorm: een passend bovenbegrip en begripsbepalende kenmerken kunnen volstaan; een naam, code of het woord ‘uniek’ bewijst geen identiteit.

De wijziging verwerkt de gezamenlijke norm en instructies voor genereren, toetsen en herstel. ESS-03 geeft geen cijfer en activeert geen automatische blokkade of reparatie. Het toetsregels-entrypoint bevat de expliciete uitzondering; de volledige referentie is lokaal beschikbaar in beide pakketten die deze nodig hebben. Eerdere CON-01/02- en ESS-01/02-teksten blijven behouden. De vijf Cowork-ZIP’s zijn door de bestaande commit-hook bijgewerkt en bytegewijs tegen hun bron gecontroleerd.

Ref: https://linear.app/definitie-app/issue/DEF-766

Validatie: referentie-/descriptioncontroles, 38 gerichte entrypointchecks, 29 inhoudelijke vergelijkingen en geïsoleerde pakkettests slagen. Claude Code CLI implementeerde; een afzonderlijke Codex CLI-review en gerichte correctiereview zijn akkoord. De acht beoordeelde tekstbestanden zijn ongewijzigd sinds die eindreview (manifest SHA256 d10531485f649380aabf16eb1d4a10dd4a76c903cbb5fda3742ae9e869582ae2).

De generieke skillvalidator heeft een bestaande mismatch met repo-eigen frontmatterkeys; YAML-parse en repo-validaties slagen. De gedeelde menselijke reviewafronding en niet-toepasselijkheidsmapping blijven open onder DEF-624. Dit is geen sluiting van DEF-766.

Publicatiegrens: deze PR wijzigt de beheerde bron en uploadpakketten. Geen actieve installatie geclaimd; de ALG-391-publicatiestop blijft staan. De reeds gemergede ESS-02-skillwijziging uit PR #333 is behouden.
