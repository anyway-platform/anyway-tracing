# Traceloop to Anyway SDK Migration Guide

This document describes the changes made to rebrand the SDK from `traceloop-sdk` to `anyway-sdk`.

## Summary of Changes

The SDK has been renamed from `traceloop-sdk` to `anyway-sdk`. This affects:
- Package name (PyPI)
- Python import paths
- Directory structure
- Configuration files
- Environment variables (`TRACELOOP_*` → `ANYWAY_*`)
- Semantic convention attribute names (`traceloop.*` → `anyway.*`)

## Import Path Changes

### Before (Traceloop)
```python
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, task, agent
from traceloop.sdk.tracing import set_association_properties
```

### After (Anyway)
```python
from anyway.sdk import Traceloop
from anyway.sdk.decorators import workflow, task, agent
from anyway.sdk.tracing import set_association_properties
```

## Installation

### Before
```bash
pip install traceloop-sdk
```

### After
```bash
pip install anyway-sdk
```

## Environment Variables

All environment variables have been renamed from `TRACELOOP_*` to `ANYWAY_*`:

| Old Name | New Name |
|----------|----------|
| `TRACELOOP_API_KEY` | `ANYWAY_API_KEY` |
| `TRACELOOP_BASE_URL` | `ANYWAY_BASE_URL` |
| `TRACELOOP_API_ENDPOINT` | `ANYWAY_API_ENDPOINT` |
| `TRACELOOP_HEADERS` | `ANYWAY_HEADERS` |
| `TRACELOOP_METRICS_ENDPOINT` | `ANYWAY_METRICS_ENDPOINT` |
| `TRACELOOP_METRICS_HEADERS` | `ANYWAY_METRICS_HEADERS` |
| `TRACELOOP_LOGGING_ENDPOINT` | `ANYWAY_LOGGING_ENDPOINT` |
| `TRACELOOP_LOGGING_HEADERS` | `ANYWAY_LOGGING_HEADERS` |
| `TRACELOOP_PROMPT_MANAGER_MAX_RETRIES` | `ANYWAY_PROMPT_MANAGER_MAX_RETRIES` |
| `TRACELOOP_PROMPT_MANAGER_POLLING_INTERVAL` | `ANYWAY_PROMPT_MANAGER_POLLING_INTERVAL` |
| `TRACELOOP_TRACING_ENABLED` | `ANYWAY_TRACING_ENABLED` |
| `TRACELOOP_TRACE_CONTENT` | `ANYWAY_TRACE_CONTENT` |
| `TRACELOOP_METRICS_ENABLED` | `ANYWAY_METRICS_ENABLED` |
| `TRACELOOP_LOGGING_ENABLED` | `ANYWAY_LOGGING_ENABLED` |
| `TRACELOOP_SUPPRESS_WARNINGS` | `ANYWAY_SUPPRESS_WARNINGS` |
| `TRACELOOP_EXP_SLUG` | `ANYWAY_EXP_SLUG` |

## Semantic Convention Attributes

Telemetry attribute names have been updated:

| Old Attribute | New Attribute |
|---------------|---------------|
| `traceloop.span.kind` | `anyway.span.kind` |
| `traceloop.workflow.name` | `anyway.workflow.name` |
| `traceloop.entity.name` | `anyway.entity.name` |
| `traceloop.entity.path` | `anyway.entity.path` |
| `traceloop.entity.version` | `anyway.entity.version` |
| `traceloop.entity.input` | `anyway.entity.input` |
| `traceloop.entity.output` | `anyway.entity.output` |
| `traceloop.association.properties` | `anyway.association.properties` |
| `traceloop.prompt.*` | `anyway.prompt.*` |
| `traceloop.correlation.id` | `anyway.correlation.id` |

## Files Changed

### Directory Renames
- `packages/traceloop-sdk/` → `packages/anyway-sdk/`
- `packages/traceloop-sdk/traceloop/` → `packages/anyway-sdk/anyway/`

### Configuration Files Updated
| File | Changes |
|------|---------|
| `packages/anyway-sdk/pyproject.toml` | Package name, paths, coverage config |
| `packages/anyway-sdk/project.json` | Nx project configuration |
| `packages/anyway-sdk/.python-version` | Updated from `3.9.5` to `3.11` |
| `packages/anyway-sdk/poetry.lock` | Regenerated for new package structure |
| `packages/sample-app/pyproject.toml` | SDK dependency reference |
| `packages/sample-app/poetry.lock` | Regenerated for new SDK reference |
| `.github/workflows/release.yml` | Build and publish targets |
| `.github/dependabot.yml` | Package directory |
| `.cz.toml` | Version file paths |
| `CLAUDE.md` | Example import paths |
| `README.md` | Example import paths |

### Source Files Updated
All Python files in the following directories had their imports updated:
- `packages/anyway-sdk/anyway/sdk/**/*.py`
- `packages/anyway-sdk/tests/**/*.py`
- `packages/sample-app/sample_app/**/*.py`
- `packages/opentelemetry-instrumentation-openai-agents/opentelemetry/instrumentation/openai_agents/_hooks.py`

## What Remains Unchanged

The following were intentionally left unchanged:
- **Class name `Traceloop`**: The main SDK class is still called `Traceloop` for backward compatibility
- **Test cassettes**: YAML files containing recorded API responses were not modified
- **CHANGELOG.md**: Historical changelog entries reference the original project
- **Instrumentation package names**: Package names like `opentelemetry-instrumentation-openai` remain unchanged (only internal env var references updated)

## Migration Steps for Existing Users

1. **Update your dependencies**:
   ```bash
   pip uninstall traceloop-sdk
   pip install anyway-sdk
   ```

2. **Update imports in your code**:
   ```python
   # Replace all occurrences of:
   from traceloop.sdk import ...
   # With:
   from anyway.sdk import ...
   ```

3. **Update environment variables**:
   ```bash
   # Rename your environment variables from TRACELOOP_* to ANYWAY_*
   # Example:
   export ANYWAY_API_KEY="your-api-key"      # was TRACELOOP_API_KEY
   export ANYWAY_TRACE_CONTENT="true"        # was TRACELOOP_TRACE_CONTENT
   ```

4. **Search and replace** (if needed):
   ```bash
   # Find files with old imports
   grep -r "from traceloop\." --include="*.py" .
   grep -r "import traceloop\." --include="*.py" .

   # Replace (use sed, IDE find/replace, or similar)
   sed -i 's/from traceloop\./from anyway./g' your_file.py
   sed -i 's/import traceloop\./import anyway./g' your_file.py
   ```

## Post-Migration: Regenerating Lock Files

After the migration, the `poetry.lock` files were regenerated to reflect the new package structure:

```bash
# Install Poetry if not already installed
brew install poetry

# Regenerate lock files
cd packages/anyway-sdk && poetry lock
cd packages/sample-app && poetry lock
```

Or using Nx (after running `npm install`):
```bash
npx nx run anyway-sdk:lock
npx nx run sample-app:lock
```

## Publishing to PyPI

### Prerequisites

1. **PyPI Account**: Create at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **Poetry**: Install via `brew install poetry`

### Configure PyPI Credentials

```bash
poetry config pypi-token.pypi <your-api-token>
```

Or create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-<your-token>
```

### Build the Package

**Important:** The `pyproject.toml` uses local path dependencies for development (e.g., `{ path = "../opentelemetry-instrumentation-openai", develop = true }`). PyPI rejects packages with local path dependencies, so these must be converted to version pins before publishing.

**Option 1: Use the build-release script (recommended)**

The `scripts/build-release.sh` script automatically converts path dependencies to version pins:

```bash
cd packages/anyway-sdk
chmod +x ../../scripts/build-release.sh
../../scripts/build-release.sh
```

This script:
1. Converts path dependencies to `"^0.50.1"` (existing packages on PyPI published by Traceloop)
2. Runs `poetry build`

**After publishing**, restore the original pyproject.toml for local development:
```bash
git checkout pyproject.toml
```

**Option 2: Manual build**

```bash
cd packages/anyway-sdk
poetry build
```

This creates distribution files in `packages/anyway-sdk/dist/`:
- `anyway_sdk-<version>.tar.gz` (source distribution)
- `anyway_sdk-<version>-py3-none-any.whl` (wheel)

### Dependency Strategy

The SDK depends on `opentelemetry-instrumentation-*` packages. These are:
- **Already published on PyPI** by Traceloop (version 0.50.1)
- **Not renamed** in this fork (only the SDK was rebranded)
- **Compatible** with anyway-sdk since the instrumentation packages are independent

When publishing anyway-sdk, it will depend on the existing instrumentation packages from PyPI. Users install:
```bash
pip install anyway-sdk  # Pulls opentelemetry-instrumentation-* from PyPI
```

### Testing with TestPyPI (Recommended)

Before publishing to production PyPI, test with TestPyPI first:

**1. Configure TestPyPI repository:**
```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
```

**2. Get a TestPyPI token:**
- Create account at https://test.pypi.org/account/register/
- Generate token at https://test.pypi.org/manage/account/token/

**3. Configure the token:**
```bash
poetry config pypi-token.testpypi pypi-<your-testpypi-token>
```

**4. Publish to TestPyPI:**
```bash
poetry publish -r testpypi
```

**5. Test installation from TestPyPI:**
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ anyway-sdk
```

The `--extra-index-url` is needed because TestPyPI won't have all dependencies (like opentelemetry packages), so pip falls back to real PyPI for those.

### Publish to Production PyPI

Once TestPyPI testing is successful:

```bash
poetry publish
```

### Verify Installation

```bash
pip install anyway-sdk
python -c "from anyway.sdk import Traceloop; print('Success!')"
```

### Automated Releases (GitHub Actions)

The project includes automated release workflow at `.github/workflows/release.yml`:
- Triggered manually via GitHub Actions UI
- Uses Commitizen for semantic versioning
- Publishes instrumentation packages first, then SDK
- Uses OIDC authentication (no hardcoded tokens)

To use automated releases:
1. Configure OIDC trusted publisher on PyPI
2. Set `GH_ACCESS_TOKEN` secret in GitHub repository
3. Trigger workflow from Actions tab

## Version Management

The project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) for version management, configured in `.cz.toml`.

### Bump Version (All Packages)

To bump the version across all packages:

```bash
# Patch version (0.0.1 -> 0.0.2)
cz bump --increment PATCH

# Minor version (0.0.1 -> 0.1.0)
cz bump --increment MINOR

# Major version (0.0.1 -> 1.0.0)
cz bump --increment MAJOR
```

This automatically updates ~70 files listed in `.cz.toml`, including all instrumentation packages and anyway-sdk.

### Manual Version Bump (anyway-sdk only)

If you only need to update the anyway-sdk version:

1. **`.cz.toml`** (line 7):
   ```toml
   version = "0.0.5"
   ```

2. **`packages/anyway-sdk/pyproject.toml`**:
   ```toml
   version = "0.0.5"
   ```

3. **`packages/anyway-sdk/anyway/sdk/version.py`**:
   ```python
   __version__ = "0.0.5"
   ```

## Notes

- The SDK class is still named `Traceloop` to minimize code changes for users who only need to update their imports
- All telemetry and tracing functionality remains the same
- OpenTelemetry semantic conventions are unchanged
- The `.python-version` file was updated to `3.11` to match commonly available Python versions

## Attribution

This project is forked from [Traceloop's OpenLLMetry](https://github.com/traceloop/openllmetry) and is licensed under Apache 2.0.
