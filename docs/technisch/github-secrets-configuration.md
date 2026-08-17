# GitHub Secrets Configuration

**Last Updated:** 2026-08-17
**Status:** Active

## Available Secrets

This document describes the GitHub repository secrets that can be configured for CI/CD workflows.

### GITLEAKS_LICENSE

**Purpose:** License key for Gitleaks organization scanning
**Used in:** `.github/workflows/security.yml`
**Required:** No (Gitleaks works fine in open source mode)
**Type:** Repository or Organization secret
**Status:** Not configured - using open source mode

#### Configuration Steps (Optional)

**Note:** Gitleaks works perfectly fine without a license in open source mode. Only configure this if you have purchased an enterprise license and need advanced features.

1. **Obtain License:**
   - Purchase from https://gitleaks.io/products
   - Store securely (password manager/vault)

2. **Add to GitHub:**
   - Navigate to: Repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GITLEAKS_LICENSE`
   - Value: `<your-license-key>`
   - Click "Add secret"

3. **Update Workflow:**
   - Add env section to `.github/workflows/security.yml`:
   ```yaml
   - name: Run gitleaks
     uses: gitleaks/gitleaks-action@v2
     env:
       GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
     with:
       args: --redact --no-banner --verbose
   ```

4. **Verify:**
   - Push to a branch matching: `main`, `develop`, `feature/DEF-*`, `fix/DEF-*`, `DEF-*`
   - Check Actions tab → Security workflow
   - Confirm gitleaks scan shows licensed features

#### Current Workflow Usage

```yaml
- name: Run gitleaks
  uses: gitleaks/gitleaks-action@v2
  with:
    args: --redact --no-banner --verbose
```

**Mode:** Open source (no license required)

## Coverage Reporting (No Secret Required)

Coverage is reported entirely inside GitHub Actions — no external service and no
secret are involved:

| Concern | Where |
|---------|-------|
| Blocking coverage floor (45%) | `make test-cov-ci` in the `Coverage ratchet` step of `.github/workflows/test.yml` |
| Coverage report on `main` | `coverage report --format=markdown >> $GITHUB_STEP_SUMMARY` in the same workflow |
| Raw artifacts (`htmlcov/`, `coverage.xml`, `.coverage`) | `Archive test results` step in the same workflow |

**Codecov is not in use.** A `CODECOV_TOKEN` secret was documented here but never
configured on this repository, so every upload failed with `Token required - not
valid tokenless upload` while the step still reported `success`. The upload steps
were removed in DEF-678. Do not re-add a Codecov step without also adding the
secret and using the correct `files:` input.

## Workflow Branch Triggers

All CI/CD workflows are configured to trigger on these branch patterns:

**Push triggers:**
- `main` - Production branch
- `develop` - Development branch
- `feature/DEF-*` - Feature branches with Linear issue prefix
- `fix/DEF-*` - Fix branches with Linear issue prefix
- `DEF-*` - Direct issue branches

**Pull request triggers:**
- Target branches: `main`, `develop`

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Rotate secrets** regularly (quarterly recommended)
3. **Use organization secrets** for shared resources
4. **Limit secret access** to required workflows only
5. **Monitor secret usage** in GitHub Actions logs
6. **Document secret purpose** and rotation schedule

## Troubleshooting

### Gitleaks License Error

**Error:** `License key invalid or missing`

**Solution:**
1. Verify secret name is exactly `GITLEAKS_LICENSE`
2. Check secret value has no extra spaces/newlines
3. Confirm license is valid and not expired
4. Re-add secret if necessary

## Related Documentation

- [GitHub Actions Workflows](../../.github/workflows/)
- [Security Scanning](./security-scanning.md) (if exists)
- [CI/CD Pipeline](../architectuur/ci-cd-pipeline.md) (if exists)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-08-17 | DEF-678: removed the `CODECOV_TOKEN` section and its troubleshooting entry — the secret was never configured and the Codecov steps have been removed from CI. Replaced by a description of the in-Actions coverage reporting. | Claude |
| 2025-01-20 | Initial documentation | Claude/BMad Master |
