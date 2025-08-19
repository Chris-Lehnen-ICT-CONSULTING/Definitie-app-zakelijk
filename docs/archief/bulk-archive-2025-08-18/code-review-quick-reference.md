# 🚀 Code Review Quick Reference Card

## Review Priority Order

### 🔴 CRITICAL (Block Merge)
1. **Security vulnerabilities**
   - SQL injection, XSS, CSRF
   - Authentication/authorization flaws
   - Exposed secrets/credentials
   - Unsafe deserialization

2. **Data corruption risks**
   - Missing transaction boundaries
   - Race conditions
   - Incorrect cascade deletes
   - Schema migration issues

### 🟡 HIGH (Should Fix)
3. **Performance regressions**
   - N+1 query problems
   - Memory leaks
   - Missing indexes
   - Synchronous blocking operations

4. **Business logic errors**
   - Incorrect calculations
   - Wrong validation rules
   - Missing edge cases
   - State machine violations

### 🟢 MEDIUM (Consider)
5. **Code maintainability**
   - High cyclomatic complexity (>10)
   - Code duplication (DRY violations)
   - Long methods (>50 lines)
   - Poor naming conventions

6. **Style consistency**
   - Import organization
   - Formatting issues
   - Comment style
   - File organization

## Python Red Flags Checklist

### 🚨 Security Anti-patterns
```python
# ❌ NEVER DO THIS
eval(user_input)                          # Code injection
exec(dynamic_code)                        # Code injection
os.system(f"command {user_input}")        # Command injection
f"SELECT * WHERE id = {user_input}"       # SQL injection
pickle.loads(untrusted_data)              # Unsafe deserialization

# ✅ DO THIS INSTEAD
ast.literal_eval(user_input)              # Safe evaluation
subprocess.run(["command", user_input])   # Safe command execution
"SELECT * WHERE id = ?", (user_input,)    # Parameterized query
json.loads(untrusted_data)                # Safe deserialization
```

### ⚠️ Common Python Gotchas
```python
# ❌ Mutable default arguments
def append_to_list(item, target=[]):  # BUG: Shared between calls
    target.append(item)
    return target

# ✅ Correct approach
def append_to_list(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target

# ❌ Late binding closures
funcs = []
for i in range(5):
    funcs.append(lambda: i)  # All will return 4

# ✅ Correct approach
funcs = []
for i in range(5):
    funcs.append(lambda i=i: i)  # Capture current value
```

### 🐛 Error Handling Issues
```python
# ❌ Bare except
try:
    risky_operation()
except:  # Catches EVERYTHING including SystemExit
    pass

# ✅ Specific exceptions
try:
    risky_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Operation failed: {e}")
    raise

# ❌ Ignoring exceptions
try:
    important_operation()
except Exception:
    pass  # Silent failure

# ✅ Proper handling
try:
    important_operation()
except SpecificException as e:
    logger.error(f"Failed: {e}", exc_info=True)
    # Fallback behavior or re-raise
```

## Performance Quick Checks

### 🏃‍♂️ Database Queries
```python
# ❌ N+1 Query Problem
for user in users:
    print(user.profile.bio)  # Query per user

# ✅ Eager Loading
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No extra queries

# ❌ Loading unnecessary data
User.objects.all()  # Loads all columns

# ✅ Select only needed fields
User.objects.values('id', 'email')
```

### 💾 Memory Management
```python
# ❌ Loading entire file
content = open('large_file.txt').read()

# ✅ Streaming approach
with open('large_file.txt') as f:
    for line in f:
        process(line)

# ❌ Accumulating in memory
results = []
for item in huge_dataset:
    results.append(transform(item))

# ✅ Generator approach
def process_items(dataset):
    for item in dataset:
        yield transform(item)
```

## Code Smell Indicators

### 📏 Complexity Metrics
- **Method length**: > 50 lines → Split into smaller functions
- **Class length**: > 300 lines → Consider splitting
- **Cyclomatic complexity**: > 10 → Simplify logic
- **Nesting depth**: > 4 levels → Extract methods
- **Parameters**: > 5 → Use configuration object

### 🔄 Duplication Patterns
- **Copy-paste code**: Extract to shared function
- **Similar classes**: Use inheritance/composition
- **Repeated strings**: Define constants
- **Similar tests**: Use parameterized tests

## Review Comment Templates

### 🔴 BLOCKING Issues
```python
# 🔴 BLOCKING: SQL Injection vulnerability
# User input directly interpolated into query
query = f"SELECT * FROM users WHERE email = '{email}'"  # UNSAFE

# Must use parameterized queries:
query = "SELECT * FROM users WHERE email = ?"
cursor.execute(query, (email,))
```

### 🟡 IMPORTANT Concerns
```python
# 🟡 IMPORTANT: Performance issue
# This loads all users into memory at once
all_users = list(User.objects.all())  # Could be millions

# Consider pagination or streaming:
for user in User.objects.iterator(chunk_size=1000):
    process(user)
```

### 🟢 SUGGESTIONS
```python
# 🟢 SUGGESTION: Improve readability
# Consider extracting magic numbers to constants
if retry_count > 3 and timeout > 30:  # What do these mean?

# Better:
MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30
if retry_count > MAX_RETRIES and timeout > DEFAULT_TIMEOUT_SECONDS:
```

## Quick Decision Tree

```
Is it a security issue?
├─ YES → 🔴 BLOCK merge
└─ NO → Could it corrupt data?
    ├─ YES → 🔴 BLOCK merge
    └─ NO → Performance regression?
        ├─ YES → 🟡 Should fix
        └─ NO → Maintainability issue?
            ├─ YES → 🟢 Consider fixing
            └─ NO → Style issue → Optional
```

## Final Checklist

Before approving:
- [ ] No security vulnerabilities
- [ ] No data integrity risks
- [ ] Tests are passing
- [ ] Performance acceptable
- [ ] Error handling present
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Logging appropriate

---

*Keep this card handy during reviews for quick reference!*
