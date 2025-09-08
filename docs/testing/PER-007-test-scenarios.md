---
aangemaakt: '08-09-2025'
applies_to: definitie-app@v2
bijgewerkt: '08-09-2025'
canonical: true
last_verified: 04-09-2025
owner: testing
prioriteit: medium
status: active
---



# PER-007 Context Flow Fix - Test Scenarios
**Document ID:** TEST-PER-007
**Created:** 04-09-2025
**Eigenaar:** Business Analyst / Test Team
**Van Toepassing Op:** PER-007 Implementatie

## Test Strategy

This document defines comprehensive test scenarios for the PER-007 Context Flow Fix, ensuring proper handling of organizational, juridical, and legal basis context in the Dutch justice domain.

## Test Data Sets

### Valid Justice Organizations (ASTRA-compliant)
```json
{
  "primary_organizations": [
    "OM", "DJI", "Rechtspraak", "CJIB", "KMAR", "NP", "Justid"
  ],
  "secondary_organizations": [
    "IND", "RvdK", "SRN", "NRGD", "3RO", "FIOD"
  ],
  "chain_contexts": [
    "ZSM-keten", "Strafrechtketen", "Jeugdketen"
  ]
}
```

### Valid Juridical Contexts
```json
{
  "main_domains": [
    "Strafrecht",
    "Bestuursrecht",
    "Civiel recht",
    "Staatsrecht",
    "Europees recht"
  ],
  "sub_domains": [
    "Strafprocesrecht",
    "Materieel strafrecht",
    "Penitentiair recht",
    "Jeugdrecht",
    "Vreemdelingenrecht"
  ]
}
```

### Valid Legal Basis Formats
```json
{
  "criminal_law": [
    "Art. 27 Sv",
    "Art. 67 lid 1 Sv",
    "Art. 310 Sr"
  ],
  "civil_law": [
    "Art. 6:162 BW",
    "Art. 3:4 lid 2 Awb"
  ],
  "european_law": [
    "Art. 5 EVRM",
    "Art. 16 AVG"
  ]
}
```

## Functional Test Scenarios

### Scenario 1: Basic Context Mapping
```gherkin
Gegeven the user provides organizational context "DJI"
En juridical context "Strafrecht"
En legal basis "Art. 27 Sv"
Wanneer a definition is generated for "verdachte"
Dan the organizational context appears in "organisatorisch" category
En the juridical context appears in "juridisch" category
En the legal basis appears in "wettelijk" category
```

### Scenario 2: Multiple Organizations
```gherkin
Gegeven the user provides organizational context ["DJI", "OM", "Rechtspraak"]
Wanneer a definition is generated
Dan all three organizations appear in "organisatorisch" category
En the context indicates cross-organizational relevance
```

### Scenario 3: Complex Legal Basis
```gherkin
Gegeven the user provides legal basis ["Art. 27 Sv", "Art. 67 lid 1 Sv", "Art. 5 EVRM"]
Wanneer a definition is generated
Dan all legal references appear in "wettelijk" category
En both national and European law are recognized
```

### Scenario 4: Empty Context Fields
```gherkin
Gegeven the user provides only the term "sanctie"
En no context fields are filled
Wanneer a definition is generated
Dan the system uses default context inference
En no null pointer errors occur
```

### Scenario 5: Legacy Field Compatibility
```gherkin
Gegeven an old integration sends only the "context" field with "DJI Strafrecht"
Wanneer a definition is generated
Dan the context is parsed and categorized correctly
En the response maintains backward compatibility
```

## Validation Test Scenarios

### Scenario 6: Invalid Organization
```gherkin
Gegeven the user provides organizational context "InvalidOrg"
Wanneer validation is performed
Dan a warning is generated: "Organization not recognized in ASTRA registry"
En suggestions are provided: ["OM", "DJI", "CJIB"]
```

### Scenario 7: Malformed Legal Citation
```gherkin
Gegeven the user provides legal basis "Article 27 Criminal Code"
Wanneer validation is performed
Dan a warning is generated: "Use Dutch legal citation format"
En the suggested format is shown: "Art. 27 Sr"
```

### Scenario 8: Conflicting Contexts
```gherkin
Gegeven the user provides juridical context "Civiel recht"
En legal basis "Art. 310 Sr" (criminal law)
Wanneer validation is performed
Dan a warning is generated: "Legal basis doesn't match juridical context"
```

## Integration Test Scenarios

### Scenario 9: End-to-End Flow
```gherkin
Gegeven a UI form with all three context fields
Wanneer the user fills:
  - Organizational: ["OM", "Rechtspraak"]
  - Juridical: ["Strafrecht"]
  - Legal basis: ["Art. 27 Sv"]
En submits the form
Dan the GenerationRequest contains all three fields
En the definition_generator_context maps them correctly
En the generated definition reflects all contexts
```

### Scenario 10: Database Persistence
```gherkin
Gegeven a definition with full context is generated
Wanneer it is saved to the database
Dan all context fields are persisted
En can be retrieved with original structure
En appear in export formats correctly
```

## Prestaties Test Scenarios

### Scenario 11: Context Processing Speed
```gherkin
Gegeven a request with maximum context complexity
Wanneer context building is measured
Dan processing time is less than 100ms
En memory usage remains stable
```

### Scenario 12: Bulk Context Validation
```gherkin
Gegeven 1000 definitions with various contexts
Wanneer bulk validation is performed
Dan all complete within 10 seconds
En validation results are accurate
```

## Beveiliging Test Scenarios

### Scenario 13: SQL Injection Prevention
```gherkin
Gegeven malicious input in context field: "'; DROP TABLE definitions;--"
Wanneer the request is processed
Dan the input is properly escaped
En no database damage occurs
```

### Scenario 14: XSS Prevention
```gherkin
Gegeven context contains: "<script>alert('XSS')</script>"
Wanneer the definition is displayed
Dan the script is not executed
En HTML is properly escaped
```

## Compliance Test Scenarios

### Scenario 15: AVG/GDPR Compliance
```gherkin
Gegeven context contains personal case references
Wanneer the definition is stored
Dan personal data is properly marked
En retention policies are enforced
En audit trail is maintained
```

### Scenario 16: ASTRA Architecture Compliance
```gherkin
Gegeven all supported organizations
Wanneer validation is performed
Dan each maps to official ASTRA identifiers
En chain relationships are recognized
```

## Edge Case Scenarios

### Scenario 17: Unicode and Special Characters
```gherkin
Gegeven context contains "Ministerie van Justitie en Veiligheid (MinJ&V)"
Wanneer processed
Dan special characters are handled correctly
En no encoding errors occur
```

### Scenario 18: Very Long Context Lists
```gherkin
Gegeven 50 legal basis references
Wanneer the definition is generated
Dan all are processed
Maar output is summarized for readability
```

## Regression Test Scenarios

### Scenario 19: Existing Functionality
```gherkin
Gegeven the new context fields are geïmplementeerd
Wanneer existing tests are run
Dan all legacy tests still pass
En existing integrations work unchanged
```

### Scenario 20: Context Prioriteit
```gherkin
Gegeven both old "context" field and new specific fields are provided
Wanneer processed
Dan new specific fields take precedence
Maar old field is used as fallback
```

## Test Execution Matrix

| Scenario | Type | Prioriteit | Automated | Frequency |
|----------|------|----------|-----------|-----------|
| 1-5 | Functional | HOOG | Yes | Every build |
| 6-8 | Validation | HOOG | Yes | Every build |
| 9-10 | Integration | HOOG | Yes | Daily |
| 11-12 | Prestaties | GEMIDDELD | Yes | Weekly |
| 13-14 | Beveiliging | HOOG | Yes | Every build |
| 15-16 | Compliance | HOOG | Partial | Release |
| 17-18 | Edge Case | LAAG | Yes | Weekly |
| 19-20 | Regression | HOOG | Yes | Every build |

## Success Criteria

All tests must pass with the following metrics:
- Functional coverage: 100%
- Code coverage: >80%
- Prestaties: <100ms context processing
- Zero security vulnerabilities
- Full ASTRA compliance
- No regression in existing features

## Test Data Management

- Test data is version controlled
- Separate test databases for each environment
- Anonymized production-like data for acceptance testing
- Regular test data refresh procedures

---
*These test scenarios ensure comprehensive validation of the PER-007 Context Flow Fix implementation in compliance with Dutch justice sector vereistes.*
