# Pre-commit Hooks Setup

This project uses `pre-commit` to automatically enforce code quality and security standards before commits.

## What's Included

- **Trailing Whitespace & EOF**: Automatically fixes trailing whitespace and ensures files end with a newline
- **Ruff**: Fast Python linter with auto-fix capabilities
- **Black**: Python code formatter (100 char line length)
- **isort**: Automatic import sorting (Black-compatible)
- **Prettier**: Formats YAML, JSON, Markdown, HTML, CSS
- **yamllint**: Strict YAML linting
- **Detect Secrets**: Detects accidentally committed secrets/credentials

## Installation

### First-time Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install git hooks**:
   ```bash
   pre-commit install
   ```

3. **Optional: Run on all existing files**:
   ```bash
   pre-commit run --all-files
   ```

### Manual Execution

To run pre-commit checks manually (without committing):

```bash
# Run on staged files only
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run black --all-files
pre-commit run prettier --all-files
```

## Configuration

Configuration is defined in:
- [`.pre-commit-config.yaml`](.pre-commit-config.yaml) — Hook definitions
- [`pyproject.toml`](pyproject.toml) — Tool-specific settings (black, isort, ruff)

### Adjusting Rules

**Line length**: Currently set to **100 characters** across all tools. To change:
1. Update `pyproject.toml`: `line-length = 100`
2. Update `.pre-commit-config.yaml`: `args: [--line-length=100]`

**Skip specific checks**: Add them to `.pre-commit-config.yaml` under `exclude` patterns.

## Troubleshooting

### Pre-commit Hangs or Runs Slowly

First-time hook installation downloads dependencies. This is normal and takes a few minutes. Subsequent runs are much faster.

If a hook consistently hangs:
```bash
# Clear pre-commit cache
rm -rf ~/.cache/pre-commit

# Reinstall
pre-commit clean
pre-commit install
```

### Black / isort / ruff Conflicts

These tools are configured to work together (`black` profile in isort). If conflicts occur:
1. Run manually: `black . && isort . --profile=black`
2. Ensure `pyproject.toml` settings match `.pre-commit-config.yaml`

### "detect-secrets" Baseline Issues

If you need to update the baseline:
```bash
detect-secrets scan --baseline .secrets.baseline
```

### Disabling a Hook Temporarily

To skip a specific hook for a single commit:
```bash
SKIP=ruff git commit -m "..."
```

To disable permanently, remove the hook from `.pre-commit-config.yaml` and reinstall:
```bash
pre-commit install
```

## Best Practices

1. **Commit frequently**: Pre-commit runs on staged files; small, focused commits are faster
2. **Review changes**: Pre-commit auto-fixes some issues. Review them before committing
3. **Run locally first**: Catch issues before pushing; matches CI requirements
4. **Keep hooks updated**: Periodically run `pre-commit autoupdate`

## CI Integration

GitHub Actions CI (`.github/workflows/ci.yml`) runs pre-commit checks on every push/PR. If your local hooks pass, the CI will also pass.

## Further Reading

- [pre-commit Documentation](https://pre-commit.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
