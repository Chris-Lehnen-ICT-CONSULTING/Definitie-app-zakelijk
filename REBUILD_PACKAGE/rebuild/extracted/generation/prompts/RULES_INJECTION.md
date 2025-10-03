# Validation Rules Injection

## 46 Validation Rules You Must Follow

{{#each validation_rules}}
### {{this.id}}: {{this.metadata.naam}}

**Priority:** {{this.priority}}

**Rule:** {{this.metadata.uitleg}}

**Good Examples:**
{{#each this.examples.good}}
- {{this}}
{{/each}}

**Bad Examples (AVOID):**
{{#each this.examples.bad}}
- {{this}}
{{/each}}

**Generation Hints:**
{{#each this.generation_hints}}
- {{this}}
{{/each}}

---
{{/each}}

## Critical Rules (High Priority)

Focus especially on these high-priority rules:
{{#each high_priority_rules}}
- **{{this.id}}:** {{this.metadata.naam}}
{{/each}}
