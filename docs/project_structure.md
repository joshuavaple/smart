# Recommended Project Structure & Import Reference

## 1. Structure

```
.
├── src/
│   ├── smart_agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── utils.py
│   │   └── utils_memory.py
│   └── smart_tools/
│       ├── __init__.py
│       └── tools.py
├── agent_server/
│   └── start_server.py
├── config/
│   └── lakebase.yaml
├── tests/
│   └── test_agent.py
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

Notes:
- `__init__.py` in each package folder is optional under modern setuptools (implicit
  namespace packages work), but include it explicitly — it's what makes a folder
  unambiguously "a package" rather than "a directory that happens to contain `.py` files,"
  and it's where you'd put package-level exports (Section 3).
- `agent_server/` stays outside `src/` — it's the runnable entrypoint, not library code.
  Nothing else should import *from* it.
- `smart_tools` is a sibling package to `smart_agent`, not nested inside it — use this if
  `tools.py` is meant to be reusable/independent of the agent package. If it's tightly
  coupled to `smart_agent` only, nest it instead: `src/smart_agent/tools/tools.py`.

---

## 2. `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "smart-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]
```

Install (from repo root, into your conda/venv env):

```bash
pip install -e .
```

`-e` (editable) means any edit you made to `src/smart_agent/*.py` during development take effect immediately — no
reinstall needed. `where = ["src"]` tells setuptools to discover packages inside `src/`
(it finds both `smart_agent` and `smart_tools` automatically, since both have
`__init__.py`).

If you want `pyproject.toml` to also declare a CLI entrypoint (so `agent_server`'s job
could instead just be `smart-agent-serve` from anywhere):

```toml
[project.scripts]
smart-agent-serve = "smart_agent.agent:main"
```

---

## 3. Imports *within* the package (`smart_agent` code importing its own siblings)

Inside `src/smart_agent/agent.py`, importing `utils.py` (same folder):

```python
from .utils import something          # relative — preferred inside a package
# or
from smart_agent.utils import something   # absolute — also valid, works identically
```

Prefer the relative form (`.utils`) inside library code — it doesn't hardcode the
top-level package name, so renaming `smart_agent` later doesn't require touching every
internal import.

Importing across sibling packages, e.g. `smart_agent/agent.py` using
`smart_tools/tools.py`:

```python
from smart_tools.tools import some_tool
```

Relative imports can't cross package boundaries with a single `.` — `smart_tools` isn't
part of `smart_agent`'s package tree, so this must be an absolute import.

**Constraint to remember:** relative imports (`.utils`) only resolve when the module is
*loaded through the import system* (via `-m`, via another module importing it, via
pytest) — never when the file is executed directly by path (`python agent.py`). See the
companion doc (`python_import_system_concepts.md`) for the full mechanism.

---

## 4. Imports *from outside* the package

Once `pip install -e .` has been run, `smart_agent` and `smart_tools` are both importable
from anywhere in the environment without any relative import juggling or messing with `sys.path`.

From `agent_server/start_server.py`:

```python
from smart_agent import agent
from smart_agent.utils_memory import (
    lakebase_context,
    set_lakebase_resources,
)

...

```

From a test file (`tests/test_agent.py`):

```python
from smart_agent import agent

def test_agent_loads():
    assert agent is not None
```

From an interactive shell / notebook / another unrelated project in the same env:

```python
import smart_agent
from smart_agent.agent import SomeClass
```

All of these are absolute imports — always use the top-level package name
(`smart_agent`, `smart_tools`), never a relative `.` (relative imports are only legal
*inside* the package they're relative to).

---

## 5. Quick decision rule

| You're writing code... | Use |
|---|---|
| Inside `smart_agent/`, importing another file in `smart_agent/` | `from .module import x` |
| Inside `smart_agent/`, importing from `smart_tools/` | `from smart_tools.module import x` |
| Inside `agent_server/`, `tests/`, or anywhere outside `src/` | `from smart_agent.module import x` |
| Running a file to test it manually | `python -m smart_agent.agent`, never `python agent.py` |