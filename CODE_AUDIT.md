# Code Audit Report - Propongo

**Date:** 2026-07-17  
**Files Audited:** app/main.py, app/models.py, app/export.py, app/snippets.py, run.py

---

## 🔴 Critical Issues

### 1. **Security: Hardcoded Secret Key**
**Location:** `app/main.py:95`
```python
app.secret_key = "propongo-dev-key-change-in-production"
```
**Issue:** Secret key is hardcoded and includes a reminder to change it, but there's no mechanism to do so.  
**Impact:** Security vulnerability if deployed to production  
**Fix:** Use environment variable
```python
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
```

### 2. **Memory Leak: Unbounded Lock Dictionary**
**Location:** `app/main.py:12-13`
```python
_proposal_locks = {}
_proposal_locks_lock = threading.Lock()
```
**Issue:** Locks are created for each proposal but never cleaned up  
**Impact:** Memory usage grows indefinitely with proposal access  
**Fix:** Implement lock cleanup or use WeakValueDictionary
```python
from weakref import WeakValueDictionary
_proposal_locks = WeakValueDictionary()
```

---

## 🟡 High Priority Issues

### 3. **Code Duplication: Export Context Building**
**Location:** `app/export.py:15-49` and `app/main.py:453-491`
```python
# Identical code in two places (70+ lines)
indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
indirect_amount = proposal.total_budget * (indirect_percent / 100)
# ... etc
```
**Issue:** Exact same logic duplicated in two files  
**Impact:** Maintenance burden, risk of divergence  
**Fix:** Create shared utility function
```python
# In app/utils.py
def build_proposal_context(proposal):
    # Move shared logic here
    pass

# Use in both files
from .utils import build_proposal_context
ctx = build_proposal_context(proposal)
```

### 4. **Inconsistent UUID Generation**
**Location:** Multiple files
- `app/main.py:1` uses `import uuid as _uuid`
- `app/main.py:507,536` uses `__import__("uuid")`
- `app/snippets.py:57,124` uses `__import__("uuid")`

**Issue:** Mix of import styles is confusing and inefficient  
**Fix:** Use consistent import at top of file
```python
# Remove __import__("uuid") calls
# Use: str(uuid.uuid4()) or uuid.uuid4().hex[:8]
```

### 5. **Repeated Code Pattern: Proposal Loading**
**Location:** 21 functions in `app/main.py`
```python
# This pattern repeated 21 times:
proposal = Proposal.load(proposal_id)
if not proposal:
    return jsonify({"error": "Not found"}), 404
```
**Issue:** Violates DRY principle  
**Fix:** Create decorator or helper function
```python
from functools import wraps

def require_proposal(f):
    @wraps(f)
    def decorated_function(proposal_id, *args, **kwargs):
        proposal = Proposal.load(proposal_id)
        if not proposal:
            return jsonify({"error": "Not found"}), 404
        return f(proposal, *args, **kwargs)
    return decorated_function

@app.route("/scope/<proposal_id>")
@require_proposal
def scope_tab(proposal):  # Now receives proposal object
    return render_template("scope.html", proposal=proposal, tasks=proposal.tasks)
```

---

## 🟢 Medium Priority Issues

### 6. **Inefficient Repeated getattr Calls**
**Location:** `app/main.py:315-382`
```python
# Called 4 times in same function scope:
getattr(proposal, 'custom_sections', [])
```
**Issue:** Repeated function calls for same value  
**Fix:** Store in variable
```python
custom_sections = getattr(proposal, 'custom_sections', [])
# Use custom_sections throughout
```

### 7. **Unused Data Classes**
**Location:** `app/models.py:16-35`
```python
@dataclass
class Task:
    # Never instantiated - tasks stored as dicts

@dataclass
class BudgetItem:
    # Never instantiated - budget items stored as dicts
```
**Issue:** Defined but never used, causing confusion  
**Impact:** Code maintenance, false expectations  
**Fix:** Either use them or remove them
```python
# Option 1: Use the dataclasses
task = Task(name="Survey", description="Field survey")
proposal.tasks.append(asdict(task))

# Option 2: Remove them and document dict structure
# tasks: list[dict] where each dict has: {id, name, description, ...}
```

### 8. **Inconsistent Error Messages**
**Location:** Multiple routes
```python
# Some use:
return jsonify({"error": "Not found"}), 404
# Others use:
return jsonify({"error": "Proposal not found"}), 404
```
**Fix:** Standardize error messages
```python
ERRORS = {
    'PROPOSAL_NOT_FOUND': {"error": "Proposal not found"},
    'NO_DATA': {"error": "No data provided"},
    # etc.
}
```

### 9. **Excel Import: Weak Error Handling**
**Location:** `app/main.py:395-428`
```python
try:
    import pandas as pd
    # ... code ...
except ImportError:
    return jsonify({"error": "Excel support not installed..."}), 500
except Exception as e:
    return jsonify({"error": f"Failed to import Excel: {str(e)}"}), 500
```
**Issue:** Catches all exceptions too broadly, returns 500 for user errors  
**Fix:** Specific exception handling
```python
try:
    import pandas as pd
except ImportError:
    return jsonify({"error": "Excel support not installed..."}), 500

try:
    df = pd.read_excel(excel_file, ...)
except ValueError as e:
    return jsonify({"error": f"Invalid Excel file: {str(e)}"}), 400
except Exception as e:
    app.logger.error(f"Excel import failed: {e}")
    return jsonify({"error": "Failed to process Excel file"}), 500
```

### 10. **Missing Type Hints**
**Location:** All Python files
```python
def markdown_to_html(text):  # No type hints
    return ""
```
**Fix:** Add type hints for better IDE support and error detection
```python
def markdown_to_html(text: str) -> str:
    if not text:
        return ""
    # ...
```

---

## 🔵 Low Priority Issues

### 11. **Inefficient Markdown Parsing**
**Location:** `app/main.py:16-81`
**Issue:** Custom markdown parser reinvents the wheel  
**Fix:** Use existing library (already have `markdown` in requirements)
```python
import markdown
from markdown.extensions import tables, nl2br

def markdown_to_html(text: str) -> str:
    if not text:
        return ""
    return markdown.markdown(
        text,
        extensions=['tables', 'nl2br', 'fenced_code']
    )
```

### 12. **Hardcoded Values**
**Location:** Multiple places
- Port 5000 hardcoded in `run.py`
- Host "0.0.0.0" implicit
- Debug=True in production code

**Fix:** Use configuration
```python
# config.py
class Config:
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
```

### 13. **No Input Validation**
**Location:** Budget item endpoints
```python
item["cost_per_unit"] = float(data.get("cost_per_unit", 0))
item["units"] = float(data.get("units", 1))
```
**Issue:** No validation for negative numbers, NaN, infinity  
**Fix:** Add validation
```python
def validate_numeric(value, name, min_val=0):
    try:
        num = float(value)
        if num < min_val or not math.isfinite(num):
            raise ValueError(f"{name} must be a valid positive number")
        return num
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {name}")
```

### 14. **File I/O Without Context Managers (Minor)**
**Location:** All file operations use context managers ✓
**Status:** Actually already correct - no issue here!

### 15. **Missing Logging**
**Issue:** No logging for errors, warnings, or important operations  
**Fix:** Add logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usage
logger.info(f"Proposal {proposal_id} created")
logger.error(f"Failed to load proposal {proposal_id}: {e}")
```

---

## Summary

| Priority | Count | Category |
|----------|-------|----------|
| 🔴 Critical | 2 | Security, Memory |
| 🟡 High | 4 | DRY, Consistency |
| 🟢 Medium | 5 | Efficiency, Clarity |
| 🔵 Low | 6 | Enhancement, Best Practice |

**Total Issues:** 17

### Immediate Actions Recommended:
1. Fix hardcoded secret key (security)
2. Fix memory leak in locks dictionary
3. Consolidate duplicate export context code
4. Standardize UUID generation
5. Add proposal loading decorator

### Next Steps:
1. Add type hints incrementally
2. Improve error handling
3. Add logging
4. Add input validation
5. Consider using markdown library instead of custom parser

---

## Testing Coverage

**Current Test Files:**
- `tests/test_main.py` - Good coverage of basic routes
- `tests/test_export.py` - Good coverage of export functionality

**Missing Tests:**
- Custom sections CRUD operations
- Excel import functionality
- Error cases (404s, invalid data)
- Snippet operations
- Lock contention scenarios

**Recommendation:** Add tests for new custom sections feature before deploying.
