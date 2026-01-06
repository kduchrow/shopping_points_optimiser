# Build Scripts

This directory contains utility scripts for building and managing the application.

## Version Management

### `check_version.py`

Validates version consistency across all files.

**Usage:**

```bash
python scripts/check_version.py
```

**What it checks:**

- ✅ `spo/version.py` - Main version source
- ✅ `package.json` - NPM package version
- ✅ `migrations/versions/vX_Y_Z_*.py` - Migration revision

## Docker Build Scripts

### `docker-build.ps1` (Windows/PowerShell)

Builds Docker image with automatic version tagging and metadata.

**Usage:**

```powershell
# Build only
.\scripts\docker-build.ps1

# Build and push to registry
.\scripts\docker-build.ps1 -Push
```

### `docker-build.sh` (Linux/Mac/Bash)

Same functionality for Unix-based systems.

**Usage:**

```bash
# Build only
./scripts/docker-build.sh

# Build and push to registry
./scripts/docker-build.sh --push
```

## What the Build Scripts Do

1. **Extract Version** from `spo/version.py`
2. **Get Git Info**: Commit SHA and build timestamp
3. **Build Image** with build arguments:

   - `APP_VERSION` - Application version
   - `BUILD_DATE` - ISO 8601 timestamp
   - `VCS_REF` - Git commit SHA
   - `FLASK_ENV` - Environment (dev/prod)

4. **Tag Image**:

   - `shopping-points-optimiser:X.Y.Z` (specific version)
   - `shopping-points-optimiser:latest`

5. **Add OCI Labels** ([Open Container Initiative](https://github.com/opencontainers/image-spec/blob/main/annotations.md)):
   - `org.opencontainers.image.version`
   - `org.opencontainers.image.created`
   - `org.opencontainers.image.revision`
   - `org.opencontainers.image.title`
   - `org.opencontainers.image.description`
   - `org.opencontainers.image.vendor`
   - `org.opencontainers.image.source`
   - `org.opencontainers.image.licenses`

## Inspect Image Metadata

```bash
# View all labels
docker inspect shopping-points-optimiser:0.2.0 --format='{{json .Config.Labels}}'

# View specific label
docker inspect shopping-points-optimiser:0.2.0 --format='{{index .Config.Labels "org.opencontainers.image.version"}}'
```

## Using with docker-compose

Set environment variables in `.env`:

```bash
APP_VERSION=0.2.0
BUILD_DATE=2026-01-06T12:00:00Z
VCS_REF=abc1234
```

Then build:

```bash
docker-compose build
```

## CI/CD Integration

The build scripts can be integrated into CI/CD pipelines:

**GitHub Actions:**

```yaml
- name: Build Docker Image
  run: |
    ./scripts/docker-build.sh --push
  env:
    DOCKER_REGISTRY: ghcr.io/username
```

**GitLab CI:**

```yaml
build:
  script:
    - ./scripts/docker-build.sh --push
  only:
    - main
    - tags
```

## Notes

- **Version must match** across `spo/version.py`, `package.json`, and migration files
- **Git repository required** for VCS_REF (uses `git rev-parse`)
- **jq required** for bash script (JSON parsing)
- **PowerShell 7+** recommended for PS script
