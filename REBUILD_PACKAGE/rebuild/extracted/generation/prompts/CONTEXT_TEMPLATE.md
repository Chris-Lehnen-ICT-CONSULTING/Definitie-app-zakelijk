# Context Injection Template

## Term to Define

**Begrip:** {{begrip}}

## Business Context

{{#if organisatorische_context}}
**Organisatorische Context:** {{organisatorische_context}}
{{/if}}

{{#if juridische_context}}
**Juridische Context:** {{juridische_context}}
{{/if}}

{{#if wettelijke_basis}}
**Wettelijke Basis:** {{wettelijke_basis}}
{{/if}}

{{#if ontologische_categorie}}
**Voorgestelde Categorie:** {{ontologische_categorie}}
{{/if}}

## Related Information

{{#if web_lookup_results}}
### External Sources

**Wikipedia Summary:**
{{web_lookup_results.wikipedia}}

**SRU Registry:**
{{web_lookup_results.sru}}
{{/if}}

{{#if existing_definitions}}
### Existing Similar Definitions

{{#each existing_definitions}}
- **{{this.begrip}}:** {{this.definitie}}
{{/each}}
{{/if}}

## Your Task

Generate a definition for "{{begrip}}" that:
1. Matches the {{ontologische_categorie}} category
2. Fits the {{organisatorische_context}} context
3. Complies with all validation rules below
4. Is distinct from existing definitions
