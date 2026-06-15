# Fallback Audit — Reference

## Why most fallbacks are harmful

A fallback's job is to answer "what happens when this operation fails?" The answer should almost never be "pretend it didn't happen and return something plausible-looking."

### The cost equation

```
fallback_cost = (time to detect wrong behavior) × (blast radius)
              
Without fallback: crash immediately → stack trace → fix in 5 minutes
With fallback:     wrong data propagates through 3 layers → corrupts database → 
                   detected by customer → 3 hours to debug, blame, rollback, fix, replay
```

A crash is an immediate, visible signal with a clear cause. A silent fallback is a time bomb.

### The five questions

For every fallback found, ask:

1. **What real situation triggers this fallback?** Network timeout? Missing data? Invalid input? Null reference?
2. **Is that situation truly unrecoverable here?** If yes, don't hide it. Let it crash at the right abstraction level.
3. **Does the caller know the fallback happened?** If they can't tell, the fallback is indistinguishable from success. This is the most dangerous class.
4. **Does the fallback value look like real data?** An empty list that means "query failed" will be joined, rendered, cached, and counted. Zero that means "no price" will be displayed, summed, and stored.
5. **When will someone discover the underlying bug?** If the answer is "never until it corrupts production data," the fallback is a liability.

## Common anti-patterns by language

### Java

```java
// Anti-pattern: return null on any exception
public User findUser(String id) {
    try {
        return repository.findById(id);
    } catch (Exception e) {
        return null;  // Caller NPEs later, stack trace unrelated
    }
}

// Anti-pattern: orElse with expensive default
return cache.get(key).orElse(fetchFromDB(key));
// fetchFromDB runs every time — should be orElseGet
```

### Kotlin

```kotlin
// Anti-pattern: Elvis masking
val email = user?.email ?: ""  // Empty string is a valid email format?
                                 // Now you can't tell missing from empty

// Anti-pattern: runCatching as try-call-default
val result = runCatching { riskyOperation() }.getOrDefault(fallback)
// If riskyOperation throws for 10 different reasons, all produce the same fallback
```

### C#

```csharp
// Anti-pattern: silent catch with empty enumerable
try {
    return db.Query<Order>(sql);
} catch {
    return Enumerable.Empty<Order>();  // "No orders" looks real
}
```

### TypeScript

```typescript
// Anti-pattern: deep optional chain with fallback
const status = response?.data?.status?.code ?? "UNKNOWN";
// Every ?. can fail independently. When status is "UNKNOWN",
// was response null? data null? status null? code missing?

// Anti-pattern: default parameter that hides API changes
async function fetchUsers(apiKey = "default-key") {
    // Who knew this API key was hardcoded?
}
```

### Python

```python
# Anti-pattern: except: pass — the most dangerous two words
try:
    process(data)
except:  # Catches KeyboardInterrupt, SystemExit, everything
    pass

# Anti-pattern: dict.get with silent default
value = config.get("timeout", 30)  # Is 30 the real config or the fallback?
```

### Go

```go
// Anti-pattern: return nil, nil on error
func findUser(id string) (*User, error) {
    user, err := db.FindUser(id)
    if err != nil {
        return nil, nil  // Caller gets nil user, nil error — thinks "not found"
    }
    return user, nil
}

// Anti-pattern: ignoring error with _
func loadConfig() string {
    data, _ := readFile("config.json")  // File missing? Corrupt? Silent.
    return data
}

// Anti-pattern: silent recover without re-panic
defer func() {
    if r := recover(); r != nil {
        _ = r  // Panic swallowed. No trace.
    }
}()
```

### Rust

```rust
// Anti-pattern: unwrap_or_default on fallible operations
fn load_config() -> Config {
    parse_file("config.toml").unwrap_or_default()
    // If config is corrupted, you get a default with wrong values.
    // If file doesn't exist, you get a default that may not work.
}

// Anti-pattern: catch_all on unstable operations
fn process(items: Vec<Item>) {
    items.par_iter().try_for_each(|item| {
        catch_all(|| process_item(item))
    });
}
```

## Fix patterns

### Pattern A: Just let it crash

```diff
- try {
-     return lookup(id);
- } catch (Exception e) {
-     return null;
- }
+ return lookup(id);  // Let the caller handle the exception
```

Works when the caller is in a position to make a recovery decision. The exception propagates with full context.

### Pattern B: Convert to a typed error

```diff
- fun find(id: String): User? {
-     return try { repo.find(id) } catch (e: Exception) { null }
- }
+ fun find(id: String): Result<User> {
+     return try { Result.success(repo.find(id)) }
+            catch (e: Exception) { Result.failure(e) }
+ }
```

Works when the API must not throw. The caller chooses how to handle failure.

### Pattern C: Add an error boundary with logging

```diff
- for item in items:
-     try:
-         process(item)
-     except Exception:
-         pass  # Move on
+ for item in items:
+     try:
+         process(item)
+     except Exception as e:
+         logger.error("Failed to process item %s: %s", item.id, e)
+         raise  # Fail fast
```

If you must catch (e.g., in a batch processor), at minimum log at ERROR level and track failure counts. Better: catch at the batch level, collect errors, report them all at once.

### Pattern D: Replace boolean parameter with explicit path

```diff
- fun sendEmail(recipient: String, retry = true) {
+ fun sendEmailWithRetry(recipient: String) {
+     // Retry is the whole point
+ }
+ fun sendEmail(recipient: String) {
+     // No retry — caller chooses
+ }
```

Separate methods with different names make the caller's intent explicit.

## When to run this audit

- **During code review** — scan the diff for new fallback patterns
- **Before a release** — scan the changed modules
- **Refactoring sprint** — full codebase audit, prioritize `high` findings
- **Post-incident** — scan the affected area for fallbacks that hid the root cause
