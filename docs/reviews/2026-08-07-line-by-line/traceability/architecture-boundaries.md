# Architectuurgrenzen

## Domein en presentatie

`src/domain` en definitiemodellen vormen het gegevenscontract. Streamlit-code in
`src/ui` hoort alleen presentatie en interactiestate te beheren. De review vond
meerdere plekken waar session state, tijdelijke context of technische fouten
door deze grens lekken.

## Services en orkestratie

De container assembleert AI-, validatie-, weblookup-, context- en
repositoryservices. Orchestrators moeten deadlines, cancellation, provenance en
typed fouten over de grens behouden. Bevindingen rond eager credentials,
exception-swallowing en contextcleanup tonen dat dit contract niet overal hard
is.

## Persistentie

Repositories, schema en migraties delen één SQLite-database. Connection
ownership, transactionele atomiciteit, WAL-aware backups en reversible
migraties zijn de kritieke architectuurgrens. Dit is de grootste concentratie
van P1/P2-data-integriteitsbevindingen.

## Configuratie en validatie

De repo presenteert meerdere YAML/JSON-bronnen als SSoT, maar enkele secties
hebben geen consumer of botsen met hardcoded defaults. Voor de 53 toetsregels
moet één getypeerde loader het contract afdwingen; tests mogen geen lokale
kopieën van productielogica simuleren.

## Externe grenzen

AI-providers, HTTP-bronnen, documentparsers en GitHub Actions zijn
onbetrouwbare grenzen. Inputvalidatie, timeouts, monotone deadlines,
outputsanitatie, dependency-pins en least-privilege workflows moeten daar
fail-closed zijn.
