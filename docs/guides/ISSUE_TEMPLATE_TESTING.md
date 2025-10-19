# 🧪 Issue Template Testing Guide

**Date:** 2025-10-19  
**Purpose:** Verify GitHub issue templates work correctly  
**Time Required:** ~10 minutes  
**Status:** ✅ Templates validated (YAML syntax correct)

---

## 📋 What Was Created

Three issue templates were added:

1. **Bug Report** (`bug_report.yml`) - Structured bug reporting
2. **Feature Request** (`feature_request.yml`) - Feature proposals with impact assessment
3. **Template Config** (`config.yml`) - Template chooser and links

---

## ✅ Automated Validation (Already Done)

All templates passed YAML syntax validation:

```bash
✅ bug_report.yml is valid YAML
✅ feature_request.yml is valid YAML  
✅ config.yml is valid YAML
```

---

## 🧪 Manual Testing Steps

### Test 1: Access Template Chooser

1. **Navigate to Issues:**
   - Go to: https://github.com/ChrisLehnen/Definitie-app/issues

2. **Click "New Issue":**
   - You should see a template chooser screen

3. **Verify Template Options:**
   - [ ] 🐛 Bug Report (with description)
   - [ ] ✨ Feature Request (with description)
   - [ ] Links section at bottom with:
     - [ ] 📚 Documentation link
     - [ ] 💬 Discussions link
     - [ ] 🔒 Security Vulnerability link

**Expected:** Clean template chooser with all options visible

---

### Test 2: Bug Report Template

1. **Select Bug Report:**
   - Click "Get started" on Bug Report

2. **Verify Form Fields:**
   - [ ] Title pre-filled with "[Bug]: "
   - [ ] Bug Description (required)
   - [ ] Expected Behavior (required)
   - [ ] Actual Behavior (required)
   - [ ] Steps to Reproduce (required)
   - [ ] Severity dropdown (Critical/High/Medium/Low)
   - [ ] Component/Area dropdown
   - [ ] Version/Branch input
   - [ ] Environment dropdown
   - [ ] Error Logs/Stack Trace (code block)
   - [ ] Screenshots upload area
   - [ ] Additional Context
   - [ ] Pre-submission checklist

3. **Fill Out Test Bug:**
   ```
   Title: [Bug]: Test issue template validation
   
   Bug Description: This is a test to verify the bug report template works correctly.
   
   Expected: Template should render with all fields
   Actual: Testing if it works
   
   Steps:
   1. Go to Issues
   2. Click New Issue
   3. Select Bug Report
   4. Fill out form
   
   Severity: Low
   Component: CI/CD Pipeline
   Version: main
   Environment: Local Development
   ```

4. **Preview Issue:**
   - Click "Preview" tab
   - Verify formatting looks good
   - All sections visible
   - Labels should show: `bug`, `needs-triage`

5. **DO NOT Submit** (unless you want to create the test issue)
   - Close the tab or click Cancel

**Expected:** All fields render correctly, markdown preview works

---

### Test 3: Feature Request Template

1. **Select Feature Request:**
   - Go back to Issues → New Issue
   - Click "Get started" on Feature Request

2. **Verify Form Fields:**
   - [ ] Title pre-filled with "[Feature]: "
   - [ ] Problem Statement (required)
   - [ ] Proposed Solution (required)
   - [ ] Alternative Solutions
   - [ ] Priority dropdown
   - [ ] Feature Category dropdown
   - [ ] Use Cases
   - [ ] Examples from Other Projects
   - [ ] Mockups/Sketches upload
   - [ ] Technical Considerations
   - [ ] Impact Assessment checkboxes:
     - [ ] Breaking changes
     - [ ] API changes
     - [ ] Database migrations
     - [ ] Security impact
     - [ ] Performance impact
     - [ ] New dependencies
   - [ ] Pre-submission checklist

3. **Fill Out Test Feature:**
   ```
   Title: [Feature]: Test feature request template
   
   Problem: Testing if the feature request template works
   
   Solution: Template should render all fields correctly
   
   Priority: Low
   Category: Documentation
   
   Use Cases: For validation purposes only
   ```

4. **Preview:**
   - Check markdown rendering
   - Labels should show: `enhancement`, `needs-triage`

5. **DO NOT Submit** (test only)

**Expected:** Rich form with impact assessment options

---

### Test 4: Template Config Links

1. **Check External Links:**
   - At the bottom of template chooser, verify:
     - [ ] 📚 Documentation → Points to README.md
     - [ ] 💬 Discussions → Points to /discussions
     - [ ] 🔒 Security → Points to security advisories

2. **Verify "Blank Issues" Setting:**
   - Should NOT see "Open a blank issue" option
   - This is intentional (blank_issues_enabled: false)

**Expected:** Only templated issues allowed, plus external links

---

## 🔍 Advanced Testing (Optional)

### Test 5: Create Real Test Issue

If you want to fully test the workflow:

1. **Create Test Bug Report:**
   ```
   Title: [Bug]: CI test - please close
   Description: This is a test issue to verify templates work
   Severity: Low
   Component: CI/CD Pipeline
   ```

2. **Verify:**
   - [ ] Issue created successfully
   - [ ] Labels applied automatically (`bug`, `needs-triage`)
   - [ ] Assigned to ChrisLehnen (per template config)
   - [ ] All sections rendered correctly

3. **Close Test Issue:**
   - Add comment: "Template test successful ✅"
   - Close issue
   - Add label: `test`

### Test 6: Create Test Feature Request

Similar process but with Feature Request template.

---

## 📊 Validation Checklist

After testing, confirm:

### Bug Report Template
- [x] YAML syntax valid ✅
- [ ] Renders in GitHub UI
- [ ] All required fields present
- [ ] Dropdown options work
- [ ] File upload areas work
- [ ] Markdown preview works
- [ ] Labels auto-apply
- [ ] Auto-assigned to reviewer

### Feature Request Template
- [x] YAML syntax valid ✅
- [ ] Renders in GitHub UI
- [ ] All required fields present
- [ ] Impact assessment checkboxes work
- [ ] Priority dropdown works
- [ ] Category dropdown works
- [ ] Labels auto-apply
- [ ] Auto-assigned to reviewer

### Template Config
- [x] YAML syntax valid ✅
- [ ] Template chooser displays
- [ ] External links work
- [ ] Blank issues disabled
- [ ] Descriptions show correctly

---

## 🐛 Common Issues & Fixes

### Issue: Templates don't appear

**Cause:** GitHub hasn't synced yet

**Solution:** 
- Wait 1-5 minutes after push
- Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
- Check URL is correct: `/issues/new/choose`

### Issue: Dropdown options missing

**Cause:** YAML indentation error

**Solution:**
```bash
# Validate locally:
python3 -c "import yaml; print(yaml.safe_load(open('.github/ISSUE_TEMPLATE/bug_report.yml')))"
```

### Issue: Labels not auto-applying

**Cause:** Labels don't exist in repository

**Solution:**
```bash
# Run label setup script:
bash scripts/setup-github-labels.sh
```

### Issue: "Blank issue" still available

**Cause:** `config.yml` not in correct location

**Solution:**
- Verify: `.github/ISSUE_TEMPLATE/config.yml` exists
- Contains: `blank_issues_enabled: false`

---

## 🎯 Success Criteria

Templates are working correctly when:

1. ✅ Template chooser displays with 2 options
2. ✅ Bug Report renders with all fields
3. ✅ Feature Request renders with all fields
4. ✅ External links work (Documentation, Discussions, Security)
5. ✅ Blank issues are disabled
6. ✅ Labels auto-apply on issue creation
7. ✅ Issues auto-assign to ChrisLehnen
8. ✅ Markdown preview works correctly

---

## 📚 Template Features

### Bug Report Features
- **Structured input** - Guides users to provide all needed info
- **Severity classification** - Helps prioritize bugs
- **Component categorization** - Routes to right team/area
- **Environment context** - Helps reproduce issues
- **Required fields** - Prevents incomplete reports

### Feature Request Features
- **Impact assessment** - Helps evaluate effort/value
- **Priority classification** - Aids in roadmap planning
- **Use cases** - Validates real-world need
- **Technical considerations** - Identifies implementation challenges
- **Examples** - Provides reference implementations

---

## 🔄 Template Maintenance

### When to Update Templates

**Add new dropdown options when:**
- New components/areas added to codebase
- New priorities needed
- Project scope changes

**Update required fields when:**
- Consistently missing critical information
- Too much unnecessary info requested
- User feedback indicates confusion

### How to Update

1. Edit `.github/ISSUE_TEMPLATE/bug_report.yml` or `feature_request.yml`
2. Test locally: `python3 -c "import yaml; yaml.safe_load(open('file.yml'))"`
3. Commit changes: `git commit -m "chore(templates): update issue template"`
4. Push to main
5. Test in GitHub UI after 1-5 minutes

---

## 📝 Next Steps

After validating templates:

- [ ] Test in GitHub UI (follow Test 1-4)
- [ ] Create one real test issue (optional)
- [ ] Close test issue after validation
- [ ] Document any customization needs
- [ ] Train team on new templates (if applicable)
- [ ] Add template usage to contributing guide

---

## 🎉 Benefits

**For Reporters:**
- ✅ Clear guidance on what to provide
- ✅ No forgotten details
- ✅ Faster issue resolution

**For Maintainers:**
- ✅ Consistent issue format
- ✅ All needed info provided upfront
- ✅ Easy to categorize and prioritize
- ✅ Less back-and-forth for clarification

**For Project:**
- ✅ Better issue tracking
- ✅ Higher quality bug reports
- ✅ More actionable feature requests
- ✅ Professional appearance

---

**Last Updated:** 2025-10-19  
**Status:** Templates created and validated ✅  
**Next:** Manual UI testing recommended (5-10 minutes)

