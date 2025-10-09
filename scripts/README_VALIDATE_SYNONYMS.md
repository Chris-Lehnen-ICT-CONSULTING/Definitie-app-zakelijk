# Juridische Synoniemen Validator

Comprehensive validation script for `config/juridische_synoniemen.yaml`.

## Features

The validator performs the following checks:

1. **Empty Synonym Lists**: Ensures no hoofdterm has an empty list of synonyms
2. **Duplicate Detection**: Finds duplicate synonyms within the same hoofdterm (including after normalization)
3. **Cross-Contamination**: Detects synonyms appearing under multiple hoofdtermen
4. **Circular References**: Identifies hoofdtermen that also appear as synonyms elsewhere
5. **Normalization Consistency**: Warns about inconsistent formatting (spaces, underscores, whitespace)
6. **YAML Syntax**: Validates YAML syntax and structure

## Usage

### Basic Usage

```bash
# Validate the production file
python scripts/validate_synonyms.py

# Validate a specific file
python scripts/validate_synonyms.py --config path/to/synoniemen.yaml

# Disable colored output (for CI/logging)
python scripts/validate_synonyms.py --no-color
```

### Exit Codes

- `0`: Validation passed (no errors)
- `1`: Validation failed (errors found)

**Note**: Warnings do not cause a non-zero exit code.

### Output Example

```
======================================================================
Juridische Synoniemen Validator
======================================================================

Validating: config/juridische_synoniemen.yaml

[1/5] Checking for empty synonym lists...
  ✓ No empty lists found

[2/5] Checking for duplicate synonyms within hoofdtermen...
  ✓ No duplicates found

[3/5] Checking for cross-contamination...
  ✗ Cross-contamination: synonym 'hogere voorziening' appears under
    multiple hoofdtermen: 'cassatie', 'hoger_beroep'

[4/5] Checking for circular references...
  ✓ No circular references found

[5/5] Checking normalization consistency...
  ⚠ Synonym contains underscore in 'term': 'some_synonym'

======================================================================
Validation Summary
======================================================================

File Statistics:
  Hoofdtermen: 50
  Total synonyms: 184
  Average synonyms per hoofdterm: 3.7

Validation Results:
  Errors: 1
  Warnings: 1

✗ Validation failed
```

## Pre-commit Hook

The validator is automatically run as a pre-commit hook when `config/juridische_synoniemen.yaml` is modified.

To install pre-commit hooks:

```bash
pre-commit install
```

To run manually:

```bash
pre-commit run validate-juridische-synoniemen --all-files
```

## Normalization Rules

The validator uses the same normalization rules as the application:

1. **Lowercase**: All terms are converted to lowercase
2. **Strip**: Leading/trailing whitespace is removed
3. **Underscores → Spaces**: Underscores are replaced with spaces

### Best Practices

- **Hoofdtermen**: Use underscores for multi-word terms (e.g., `voorlopige_hechtenis`)
- **Synonyms**: Use spaces for multi-word terms (e.g., `voorlopige vrijheidsbeneming`)
- **No Duplicates**: Ensure each synonym appears only once per hoofdterm
- **No Cross-Contamination**: Each synonym should belong to only one hoofdterm
- **No Circular References**: Hoofdtermen should not appear as synonyms

## Common Issues and Fixes

### Cross-Contamination

**Problem**: A synonym appears under multiple hoofdtermen

```yaml
hoger_beroep:
  - hogere voorziening

cassatie:
  - hogere voorziening  # ✗ Duplicate
```

**Fix**: Decide which hoofdterm is most appropriate and remove from the other

```yaml
hoger_beroep:
  - appel
  - appelprocedure

cassatie:
  - hogere voorziening  # ✓ Only here
```

### Duplicate Synonyms

**Problem**: Same synonym appears twice (exact or after normalization)

```yaml
onherroepelijk:
  - kracht van gewijsde
  - kracht_van_gewijsde  # ✗ Same after normalization
```

**Fix**: Remove the duplicate

```yaml
onherroepelijk:
  - kracht van gewijsde  # ✓ Single entry
```

### Circular References

**Problem**: A hoofdterm appears as a synonym elsewhere

```yaml
vonnis:
  - uitspraak

uitspraak:
  - vonnis  # ✗ Circular reference
```

**Fix**: Remove the circular reference or restructure

```yaml
vonnis:
  - uitspraak
  - rechterlijke beslissing

# If 'uitspraak' is a synonym, don't make it a hoofdterm
```

### Empty Lists

**Problem**: A hoofdterm has no synonyms

```yaml
empty_term: []  # ✗ Empty list
```

**Fix**: Either add synonyms or remove the hoofdterm

```yaml
# Remove if no synonyms exist, or:
filled_term:
  - synonym1
  - synonym2
```

## Testing

Unit tests are available in `tests/scripts/test_validate_synonyms.py`:

```bash
# Run all tests
pytest tests/scripts/test_validate_synonyms.py -v

# Run specific test class
pytest tests/scripts/test_validate_synonyms.py::TestValidateCrossContamination -v

# Run with coverage
pytest tests/scripts/test_validate_synonyms.py --cov=scripts.validate_synonyms
```

### Test Fixtures

Test fixtures are available in `tests/fixtures/`:

- `valid_synoniemen.yaml` - Valid file (all checks pass)
- `empty_list_synoniemen.yaml` - Contains empty lists
- `duplicate_synoniemen.yaml` - Contains duplicate synonyms
- `cross_contamination_synoniemen.yaml` - Synonyms under multiple hoofdtermen
- `circular_reference_synoniemen.yaml` - Circular references present
- `normalization_issues_synoniemen.yaml` - Normalization warnings
- `invalid_yaml_synoniemen.yaml` - Invalid YAML syntax

## Implementation Details

### Architecture

The validator follows a functional design with separate validation functions:

- `load_yaml_file()` - Loads and parses YAML
- `validate_empty_lists()` - Checks for empty synonym lists
- `validate_duplicates_within_hoofdterm()` - Detects duplicates
- `validate_cross_contamination()` - Finds cross-contamination
- `validate_circular_references()` - Identifies circular references
- `validate_normalization_consistency()` - Checks formatting

### Performance

- Handles large files efficiently (tested with 1000+ hoofdtermen)
- Progress indicators show validation progress
- Normalization cache prevents redundant processing

### Error Messages

All error messages include:

- Affected hoofdterm(s)
- Specific synonym causing the issue
- Clear description of the problem
- Line numbers (where applicable from YAML parser)

## Integration

The validator integrates with:

1. **Pre-commit hooks**: Automatic validation on commit
2. **CI/CD pipeline**: Can be added to GitHub Actions
3. **Make commands**: Can be added to Makefile for convenience

### Example Makefile Integration

```makefile
.PHONY: validate-synonyms
validate-synonyms:
	python scripts/validate_synonyms.py

.PHONY: validate-synonyms-ci
validate-synonyms-ci:
	python scripts/validate_synonyms.py --no-color
```

## Future Enhancements

Potential improvements:

- [ ] YAML auto-fix mode (--fix flag)
- [ ] JSON output for machine parsing (--json flag)
- [ ] Detailed statistics report (--stats flag)
- [ ] Synonym suggestion engine
- [ ] Integration with VS Code extension
- [ ] Batch validation of multiple files
- [ ] Performance profiling mode

## License

Part of the DefinitieAgent project.

## Contact

For issues or questions, see the main project documentation.
