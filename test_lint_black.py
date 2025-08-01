Below is a **drop-in linting toolkit** that leaves **`main_auth.py` untouched** while giving you repeatable, one-command code-quality checks and auto-formatting.

---

## 1. Dev-only dependencies

Create `requirements-dev.txt` next to your existing `requirements.txt`:

```text
black==24.2.0          # opinionated code formatter
flake8==7.0.0          # style / bug‐prone pattern checker
flake8-bugbear==24.2.6 # extra “gotcha” rules (B-series codes)
isort==5.13.0          # import-sorting to keep Black happy
```

Install them into your venv:

```bash
pip install -r requirements-dev.txt
```

---

## 2. Black & isort config (PEP 518 style)

Put a minimal **`pyproject.toml`** at repo root:

```toml
[tool.black]
line-length = 88
target-version = ["py311"]   # adjust if you’re on Py 3.10/3.12
exclude = '\.venv|\.mypy_cache|\.git|build|dist'

[tool.isort]
profile = "black"
line_length = 88
combine_as_imports = true
skip = [".venv", "build", "dist"]
```

Black and isort now share the same wrap width and won’t fight each other.

---

## 3. Flake8 rules

Add **`.flake8`**:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503   # Black’s own deviations from PEP 8
select = B,C,E,F,W  # include bugbear (B…) plus core rules
exclude = .git,__pycache__,.venv,build,dist
```

---

## 4. One-touch commands

Create a tiny **`Makefile`** (optional but convenient):

```Makefile
.PHONY: format check

# Auto-format everything in place
format:
	black .
	isort .

# Lint without modifying files (CI-friendly)
check:
	black --check .
	isort --check-only .
	flake8 .
```

Usage:

```bash
make format  # re-formats imports & whitespace
make check   # fails if anything is mis-formatted or violates Flake8
```

---

## 5. Pre-commit hook (zero-click local enforcement)

If you use [pre-commit](https://pre-commit.com):

1. `pip install pre-commit`

2. Create **`.pre-commit-config.yaml`**:

   ```yaml
   repos:
     - repo: https://github.com/psf/black
       rev: 24.2.0
       hooks: [id: black]

     - repo: https://github.com/PyCQA/isort
       rev: 5.13.0
       hooks: [id: isort]

     - repo: https://github.com/pycqa/flake8
       rev: 7.0.0
       hooks:
         - id: flake8
           additional_dependencies: ["flake8-bugbear==24.2.6"]
   ```

3. Activate once:

   ```bash
   pre-commit install
   ```

Now every `git commit` auto-runs Black, isort, and Flake8; the commit aborts if anything fails.

---

## 6. CI snippet (GitHub Actions)

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: make check
```

---

### What happens to `main_auth.py`?

* **No manual edits required**.
* Running `make format` will only re-wrap long strings or reorder imports—functionality stays identical.
* Style issues (unused imports, shadowed variables, etc.) will show up in Flake8’s output so you can fix them consciously.

You can now enforce consistent formatting, catch common mistakes early, and keep your API-key-protected FastAPI app squeaky clean.
