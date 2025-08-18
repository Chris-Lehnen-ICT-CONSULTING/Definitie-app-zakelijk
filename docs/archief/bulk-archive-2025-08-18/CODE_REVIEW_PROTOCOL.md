# 🔍 Code Review Protocol V2 - Systematische Verificatie
*Enhanced by Quinn - Senior Developer & QA Architect*

**Doel**: Verifiëren wat werkelijk functioneert vs wat alleen bestaat/geclaimd wordt  
**Gebruik**: Dit protocol voor ELKE component/feature uitvoeren

---

## 📋 Enhanced Review Checklist

### Phase 1: Quick Existence Check (5 min)
```bash
□ Bestaat het bestand/de module?
□ Kan het geïmporteerd worden zonder errors?
□ Zijn er obvious syntax errors?
□ Bestaat de documentatie?
□ Type hints aanwezig en correct?
```

### Phase 2: Dependency Analysis (10 min)
```bash
□ Lijst alle imports
□ Verifieer dat alle dependencies bestaan
□ Check of import namen kloppen
□ Identificeer circulaire dependencies
□ Controleer versie compatibiliteit
□ Dependency injection correct gebruikt?
□ Interfaces vs concrete dependencies
```

### Phase 3: Functionality Test (20 min)
```bash
□ Start de functionaliteit op
□ Voer happy path test uit
□ Test edge cases
□ Test error handling
□ Verifieer output format
□ Memory/resource cleanup
□ Async/await correctheid
```

### Phase 4: Integration Check (15 min)
```bash
□ Hoe integreert het met andere componenten?
□ Worden interfaces correct gebruikt?
□ Data flow verificatie
□ Side effects check
□ Transaction boundaries correct?
□ Event propagation werkt?
```

### Phase 5: Test Suite Verification (10 min)
```bash
□ Draaien de tests echt?
□ Wat is de werkelijke coverage?
□ Zijn er skipped tests?
□ Mock vs echte functionaliteit
□ Test pyramid ratio (70/20/10)?
□ Flaky tests aanwezig?
```

### Phase 6: Security & Performance (15 min) 🆕
```bash
## Security
□ Input validation compleet?
□ SQL Injection preventie?
□ XSS/CSRF bescherming?
□ Authentication/Authorization correct?
□ Secrets management veilig?
□ Rate limiting geïmplementeerd?

## Performance
□ Database queries geoptimaliseerd?
□ N+1 query problemen?
□ Caching strategy aanwezig?
□ Resource pooling correct?
□ Async waar nodig?
□ Memory leaks check
```

### Phase 7: Code Quality Metrics (10 min) 🆕
```bash
□ Cyclomatic Complexity < 10
□ Method length < 50 lines
□ Class cohesion acceptabel
□ DRY principle gevolgd
□ SOLID principles nageleefd
□ Design patterns correct toegepast
□ Code duplication < 5%
```

---

## 🎯 Enhanced Component Reviews

### 1. Service Review Template
```python
# VOOR ELKE SERVICE (Generator, Validator, Repository, etc.)

## Stap 1: Import & Architecture Test
try:
    from services.{service_name} import {ServiceClass}
    from services.interfaces import {ServiceInterface}
    
    # Verify implements interface
    assert issubclass({ServiceClass}, {ServiceInterface})
    print("✅ Import & interface compliance")
except Exception as e:
    print(f"❌ Architecture violation: {e}")

## Stap 2: Instantiation & Configuration Test  
try:
    # Test with different configs
    configs = [None, test_config, prod_config]
    for config in configs:
        service = {ServiceClass}(config)
        print(f"✅ Instantiation with {config}")
except Exception as e:
    print(f"❌ Instantiation failed: {e}")

## Stap 3: Method Contract Test
# Test ELKE publieke methode met contract validation
@measure_performance
def test_method_with_contract(method, args, expected_type):
    start_memory = get_memory_usage()
    try:
        result = getattr(service, method)(*args)
        assert isinstance(result, expected_type)
        assert get_memory_usage() - start_memory < MAX_MEMORY_DELTA
        print(f"✅ {method} contract & performance OK")
    except Exception as e:
        print(f"❌ {method} contract violation: {e}")

## Stap 4: Error Handling & Recovery
error_scenarios = [
    (None, "null_input"),
    ("", "empty_input"),
    (very_large_input, "scale_test"),
    (malicious_input, "security_test")
]

for input_data, scenario in error_scenarios:
    try:
        result = service.process(input_data)
        # Should handle gracefully
    except Exception as e:
        log_error_handling(scenario, e)
```

### 2. Enhanced Database Review
```python
## Stap 1: Connection Pool Test
with connection_pool_monitor():
    □ Pool size configureerbaar?
    □ Connection leaks detectie
    □ Timeout handling correct
    □ Retry logic aanwezig

## Stap 2: Transaction Integrity
@test_transaction_rollback
def verify_acid_compliance():
    □ Atomicity gegarandeerd
    □ Consistency checks
    □ Isolation levels correct
    □ Durability verified

## Stap 3: Performance Benchmarks
benchmarks = {
    "single_insert": 10,     # ms
    "bulk_insert_1k": 100,   # ms
    "complex_query": 50,     # ms
    "concurrent_10": 200     # ms
}

run_performance_suite(benchmarks)
```

### 3. Security-First API Review 🆕
```python
## Authentication & Authorization
□ JWT validation correct?
□ Role-based access control?
□ API key rotation supported?
□ Rate limiting per user/IP?

## Input Validation
for endpoint in api.endpoints:
    □ Schema validation actief?
    □ SQL injection preventie?
    □ XSS sanitization?
    □ File upload restrictions?
    □ Request size limits?

## Security Headers
required_headers = [
    "X-Content-Type-Options: nosniff",
    "X-Frame-Options: DENY",
    "Content-Security-Policy",
    "Strict-Transport-Security"
]
```

---

## 📊 Enhanced Review Output Template

```markdown
# Component: [Naam]
**Review Datum**: [YYYY-MM-DD]
**Reviewer**: [Naam/Tool]
**Protocol Version**: 2.0
**Claimed Status**: [Wat wordt beweerd]
**Actual Status**: [Wat werkelijk werkt]

## Risk Assessment 🆕
- **Business Impact**: HIGH/MEDIUM/LOW
- **Security Risk**: CRITICAL/HIGH/MEDIUM/LOW  
- **Technical Debt**: €[amount] (hours × rate)
- **Performance Impact**: [latency/throughput metrics]

## Bevindingen

### ✅ Wat Werkt
- [Lijst met performance metrics waar relevant]

### ❌ Wat Niet Werkt  
- [Lijst met root cause analysis]
- [Security implications per issue]

### ⚠️ Gedeeltelijk Werkend
- [Met specifieke failure conditions]

## Quality Metrics 🆕
- **Code Coverage**: Actual: Y% (Target: 80%)
- **Cyclomatic Complexity**: Avg: X (Target: <10)
- **Technical Debt Ratio**: X% (Target: <5%)
- **Security Score**: X/100 (Target: >85)
- **Performance Score**: X/100 (Target: >90)

## Architectural Fitness 🆕
- **SOLID Compliance**: ✅/⚠️/❌
- **Clean Architecture**: ✅/⚠️/❌
- **12-Factor App**: X/12 factors met
- **Design Patterns**: [Correct toegepast/Misbruikt]

## Action Items (Prioritized by Risk)
1. 🔴 **CRITICAL**: [Security/Data loss issues]
2. 🟠 **HIGH**: [Business blocking issues]  
3. 🟡 **MEDIUM**: [Performance/UX degradation]
4. 🟢 **LOW**: [Technical debt/refactoring]

## Monitoring & Observability 🆕
- [ ] Metrics endpoints aanwezig
- [ ] Structured logging geïmplementeerd
- [ ] Tracing instrumentation
- [ ] Custom dashboards needed
- [ ] Alert rules gedefinieerd
```

---

## 🔧 Enhanced Automation Toolkit

### Local Development Setup
```bash
# Install pre-commit hooks
pre-commit install
pre-commit run --all-files

# Setup linting
pip install ruff black mypy
ruff check src/
black src/
mypy src/
```

### Continuous Quality Checks
```bash
# Full quality suite
make quality-check

# Individual checks
make security-scan      # Bandit, safety
make performance-test   # pytest-benchmark
make architecture-check # import-linter
make dependency-audit   # pip-audit
```

### Git Hooks Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.5
    hooks:
      - id: ruff
        args: [--fix]
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### IDE Integration
```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Architecture Decision Records (ADR)
```bash
# Generate ADR for significant changes
adr new "Migrate to service architecture"
adr status
```

---

## 👥 Team Collaboration Guidelines

### Code Review Etiquette
- **Be Constructive**: "Consider using X" vs "This is wrong"
- **Ask Questions**: "What's the reasoning behind X?"
- **Acknowledge Good Work**: "Nice abstraction here!"
- **Provide Context**: Link to docs/examples
- **Be Timely**: Review within 24 hours

### Review Comments Format
```python
# 🔴 BLOCKING: Security vulnerability
# This allows SQL injection. Use parameterized queries:
query = f"SELECT * FROM users WHERE id = {user_id}"  # Vulnerable
query = "SELECT * FROM users WHERE id = ?", (user_id,)  # Safe

# 🟡 IMPORTANT: Performance concern
# This creates N+1 queries. Consider eager loading:
for item in items:
    item.category  # Triggers query per item

# 🟢 NITPICK: Naming convention
# Consider more descriptive name: calculate_compound_interest

# 💡 SUGGESTION: Future improvement
# We could cache this result for better performance
```

### Handling Disagreements
1. **Technical Disputes**: Refer to project standards/ADRs
2. **Style Preferences**: Defer to linting rules
3. **Architecture Decisions**: Escalate to tech lead
4. **Performance vs Readability**: Measure first, optimize if needed

---

## 🚀 Quick Reference Card

### Review Priority Order
1. **Security vulnerabilities** (injection, auth, crypto)
2. **Data corruption risks** (transactions, concurrency)
3. **Performance regressions** (N+1, memory leaks)
4. **Business logic errors** (incorrect calculations)
5. **Code maintainability** (complexity, duplication)
6. **Style consistency** (naming, formatting)

### Common Python Gotchas
- Mutable default arguments
- Late binding closures
- Integer division differences (Python 2 vs 3)
- Unicode handling in file I/O
- Circular imports
- Global interpreter lock (GIL) implications

### Red Flags Checklist
- [ ] `eval()` or `exec()` usage
- [ ] Bare `except:` clauses
- [ ] Hardcoded secrets/credentials
- [ ] `# TODO: fix this` without ticket
- [ ] Commented out code blocks
- [ ] Copy-pasted code sections
- [ ] Functions > 50 lines
- [ ] Classes > 300 lines
- [ ] Circular dependencies
- [ ] Missing error handling

---

## 📚 Resources & Learning

### Essential Reading
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)
- [Effective Python by Brett Slatkin](https://effectivepython.com/)
- [Architecture Patterns with Python](https://www.oreilly.com/library/view/architecture-patterns-with/9781492052197/)

### Tools Documentation
- [Ruff - Fast Python Linter](https://beta.ruff.rs/docs/)
- [Black - Code Formatter](https://black.readthedocs.io/)
- [MyPy - Static Type Checker](https://mypy.readthedocs.io/)
- [Bandit - Security Linter](https://bandit.readthedocs.io/)

---

## 🔄 Protocol Maintenance

**This protocol is a living document.**

### Update Process
1. Propose changes via PR
2. Discuss in team meeting
3. Test new additions for 1 sprint
4. Incorporate feedback
5. Update protocol version

**Current Version**: 2.1 (Enhanced)  
**Last Updated**: 2025-01-15  
**Next Review**: 2025-04-15

---

## 📈 Continuous Improvement Loop

1. **Execute Protocol** → 2. **Measure Results** → 3. **Update Baselines** → 4. **Refine Protocol**

### Review Metrics to Track
- **Review Turnaround Time**: Target < 24 uur
- **Defect Density**: Bugs gevonden post-review
- **Review Coverage**: % van code die reviewed is
- **Feedback Quality**: Actionable vs nitpicks ratio
- **Security Issues Found**: Critical/High/Medium/Low
- **Performance Regressions**: Caught in review vs production

### Team Learning
- **Knowledge Sharing**: Document patterns found
- **Common Issues**: Update linting rules
- **Best Practices**: Share in team meetings
- **Tool Improvements**: Automate repetitive checks

---

*Remember: Perfect is the enemy of good. Focus on high-risk areas first, but maintain consistent quality standards across the codebase.*

---

## 🔄 Review Process & Workflow

### Pre-Review Checklist (Developer)
Voordat je een review aanvraagt:
- [ ] **Zelf-review** uitgevoerd met dit protocol
- [ ] **Tests** draaien lokaal en zijn groen
- [ ] **Linting** geen errors of warnings
- [ ] **Branch** is up-to-date met main/develop
- [ ] **Documentatie** bijgewerkt waar nodig

### Pull Request Requirements
```markdown
## Beschrijving
[Wat is veranderd en waarom]

## Type wijziging
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Security fix
- [ ] Performance improvement

## Test instructies
[Hoe kan een reviewer dit testen]

## Checklist
- [ ] Code volgt project style guidelines
- [ ] Self-review uitgevoerd
- [ ] Tests toegevoegd/aangepast
- [ ] Documentatie bijgewerkt
```

### Review Workflow
1. **Automated Checks** (CI/CD)
   - Linting passes
   - Tests passes (coverage ≥ 80%)
   - Security scan clean
   - Build succeeds

2. **Peer Review** (Minimaal 1 reviewer)
   - Functionele correctheid
   - Code kwaliteit volgens protocol
   - Security & performance checks
   - Architectuur compliance

3. **Feedback Categorisering**
   - 🔴 **BLOCKING**: Must fix voor merge
   - 🟡 **IMPORTANT**: Should fix, maar niet blocking
   - 🟢 **NITPICK**: Nice to have, optional
   - 💡 **SUGGESTION**: Ideeën voor verbetering

4. **Resolution & Merge**
   - Developer addressed alle blocking feedback
   - Re-review bij major changes
   - Approval van reviewer(s)
   - Squash & merge naar target branch