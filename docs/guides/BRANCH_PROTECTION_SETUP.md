# 🔐 Branch Protection Setup Guide

**Date:** 2025-10-19  
**Purpose:** Step-by-step guide to configure branch protection for `main` branch  
**Time Required:** ~30 minutes  
**Recommended:** Do this immediately after auto-labeling setup

---

## 🎯 Why Branch Protection?

Branch protection prevents:
- ❌ Direct pushes to main without review
- ❌ Merging PRs with failing CI checks
- ❌ Force pushes that rewrite history
- ❌ Accidental branch deletion
- ❌ Merging without required approvals

**Result:** Higher code quality, better collaboration, fewer bugs in production

---

## 📋 Prerequisites

Before starting, ensure:
- ✅ You have admin access to the repository
- ✅ CI workflows are configured (they are!)
- ✅ You know which checks must pass (see below)

---

## 🚀 Step-by-Step Configuration

### Step 1: Navigate to Settings

1. Go to: https://github.com/ChrisLehnen/Definitie-app
2. Click **Settings** tab (top navigation)
3. Click **Branches** (left sidebar under "Code and automation")

### Step 2: Add Branch Protection Rule

1. Click **"Add branch protection rule"** button
2. In **"Branch name pattern"** field, enter: `main`

### Step 3: Configure Protection Settings

#### 🔒 Basic Protection (REQUIRED)

Check these boxes:

- ✅ **Require a pull request before merging**
  - ✅ **Require approvals**: Set to `1`
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners** (optional, if you have CODEOWNERS file)

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - Click **"Add more"** and search for these checks:

#### ✅ Required Status Checks (MUST PASS)

Add these exact check names (search for them):

**Security Checks (CRITICAL):**
```
Secret Scan (gitleaks)
Dependency Audit (pip-audit)
```

**CI Checks (CRITICAL):**
```
CI / Run Grep Gate (enforced for services)
CI / Run smoke test with coverage
```

**Quality Gates (CRITICAL):**
```
Quality Gates
No root-level DB files
```

**Optional but Recommended (Can add later):**
```
Tests / test (3.11)  [Add when Phase 2 complete]
Contract Tests       [Add when fixed]
```

#### 🔐 Additional Protection (STRONGLY RECOMMENDED)

- ✅ **Require conversation resolution before merging**
  - Forces all review comments to be resolved

- ✅ **Require signed commits** (if you use GPG signing)
  - Only if you have GPG configured

- ✅ **Include administrators**
  - ⚠️ IMPORTANT: Check this to apply rules to admins too
  - Prevents accidental bypassing of protection

- ✅ **Restrict who can push to matching branches**
  - Leave empty or add specific users if needed

#### 🚫 Lock Settings (CRITICAL)

- ✅ **Allow force pushes**: **UNCHECKED** (NO!)
- ✅ **Allow deletions**: **UNCHECKED** (NO!)

### Step 4: Save Changes

1. Scroll to bottom
2. Click **"Create"** or **"Save changes"**
3. You'll see a success message

---

## ✅ Verification Checklist

After configuration, verify:

### Test 1: Try Direct Push (Should FAIL)
```bash
# This should now be blocked:
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin main
# Expected: ! [remote rejected] main -> main (protected branch hook declined)
```

### Test 2: Create Test PR
```bash
# This should work:
git checkout -b test-branch-protection
echo "# Test Branch Protection" >> TEST_PR.md
git add TEST_PR.md
git commit -m "test: verify branch protection works"
git push origin test-branch-protection

# Then create PR via GitHub UI and verify:
# - Can create PR ✅
# - Cannot merge until checks pass ❌
# - Need 1 approval ❌
```

### Test 3: Check Status Checks
1. Go to your test PR
2. Scroll to bottom - you should see:
   - ⏳ "Waiting for status checks to pass"
   - List of required checks (Security, CI, Quality Gates)
   - 🔴 "Review required" (need 1 approval)

### Test 4: Cleanup
```bash
# After verifying, cleanup:
git checkout main
git branch -D test-branch-protection
# Delete the PR from GitHub UI
```

---

## 📊 Expected Behavior After Setup

### ✅ What Will Work
- Creating feature branches
- Opening pull requests
- Auto-labeling on PRs (via labeler workflow)
- CI checks running automatically
- PR size labels appearing
- Viewing all changes before merge

### ❌ What Will Be Blocked
- Direct pushes to `main`
- Merging without approval
- Merging with failing CI checks
- Force pushing to `main`
- Deleting `main` branch
- Merging with unresolved comments

---

## 🔧 Troubleshooting

### Problem: "Status check not found"

**Cause:** Check name doesn't match exactly

**Solution:** 
1. Open a recent PR or workflow run
2. Copy the exact check name from GitHub Actions
3. Add that exact name to required checks

### Problem: "Cannot push even with PR"

**Cause:** You're trying to push to `main` directly

**Solution:**
```bash
# Always use feature branches:
git checkout -b feature/my-change
# Make changes
git push origin feature/my-change
# Then create PR from GitHub UI
```

### Problem: "Too many required checks"

**Cause:** Some checks are failing/flaky

**Solution:**
1. Check CI_FAILURES_ANALYSIS.md for pre-existing issues
2. Remove pre-existing failing checks from required list (temporary)
3. Add them back after fixing in Phase 2-4

### Problem: "Admin override not working"

**Cause:** "Include administrators" is checked

**Solution:**
- This is INTENTIONAL! It's a best practice
- If you really need to override (emergency):
  1. Temporarily disable protection
  2. Make change
  3. Re-enable protection immediately
  4. Document why in commit message

---

## 📚 Additional Resources

**GitHub Documentation:**
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)

**Project Documentation:**
- [GITHUB_BEST_PRACTICES.md](../analyses/GITHUB_BEST_PRACTICES.md)
- [CI_FAILURES_ANALYSIS.md](../analyses/CI_FAILURES_ANALYSIS.md)
- [CLAUDE.md - CI/CD Section](../../CLAUDE.md#cicd-pipeline--github-workflow-management)

---

## 🎯 Quick Configuration (TL;DR)

If you just want the essentials:

**Settings → Branches → Add rule for `main`:**

```yaml
Protections:
  ✅ Require PR with 1 approval
  ✅ Dismiss stale reviews
  ✅ Require status checks:
     - Secret Scan (gitleaks)
     - Dependency Audit (pip-audit)
     - CI / Run Grep Gate
     - CI / Run smoke test
     - Quality Gates
     - No root-level DB files
  ✅ Require up-to-date branches
  ✅ Require conversation resolution
  ✅ Include administrators
  ❌ Allow force pushes: NO
  ❌ Allow deletions: NO
```

**Time:** ~5 minutes if you follow this exactly

---

## 🚨 Emergency Override (Last Resort)

If you MUST bypass protection (emergency only):

### Via GitHub UI:
1. Settings → Branches → Edit rule
2. Temporarily uncheck "Include administrators"
3. Make emergency change
4. **IMMEDIATELY** re-enable protection
5. Document in commit: `fix: emergency fix for [issue] - bypassed protection`

### Via git:
```bash
# DON'T DO THIS unless absolutely necessary
# And ONLY if you disabled "Include administrators"
git push --force origin main  # DANGEROUS!
```

**⚠️ WARNING:** Document every bypass in:
- Commit message
- PR description (if you create one after)
- Team chat/documentation

---

## ✅ Success Criteria

You've successfully configured branch protection when:

1. ✅ Direct push to main is rejected
2. ✅ PR requires 1 approval before merge
3. ✅ Required CI checks must pass
4. ✅ Stale reviews are dismissed on new commits
5. ✅ Force push is blocked
6. ✅ Branch deletion is blocked
7. ✅ Administrators are included in rules

**Verification:** Create and try to merge a test PR without approval → Should be blocked ✅

---

## 📝 Post-Setup Checklist

After configuration:

- [ ] Test direct push (should fail)
- [ ] Test PR creation (should work)
- [ ] Test merge without approval (should fail)
- [ ] Test merge without passing checks (should fail)
- [ ] Document configuration in team docs
- [ ] Notify team about new workflow
- [ ] Update onboarding docs with new process
- [ ] Add to CLAUDE.md reference (already done ✅)

---

**Last Updated:** 2025-10-19  
**Next Review:** After Phase 2 CI fixes complete

