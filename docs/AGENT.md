# Agent Workflow Documentation

## Database Model Changes Workflow

When making changes to SQLAlchemy models that require database migrations, follow this workflow:

### Step 1: Implement Model Changes
Make the necessary changes to the model files in `spo/models/`:
- Add/modify/remove columns
- Update relationships
- Modify constraints

**Example:** Added `rate_type` column to `ShopProgramRate` model in `spo/models/shops.py`

```python
rate_type = db.Column(db.String, default="shop", nullable=False)  # 'shop' or 'contract'
```

### Step 2: Restart the Container
Restart the Docker container to pick up the new code:

```powershell
docker compose restart app
```

Or for a full rebuild if needed:

```powershell
docker compose down
docker compose up -d
```

### Step 3: Generate Migration Automatically
Let Alembic detect the model changes and create the migration file automatically:

```powershell
docker compose exec app flask db migrate -m "Add rate_type to ShopProgramRate"
```

This will:
- Compare current database schema with SQLAlchemy models
- Detect differences automatically
- Generate a migration file in `migrations/versions/`
- Include proper upgrade() and downgrade() functions

### Step 4: Apply and Test Migration
Apply the migration to update the database schema:

```powershell
docker compose exec app flask db upgrade
```

Then restart the container to ensure everything works:

```powershell
docker compose restart app
```

Verify the application is running correctly:

```powershell
docker compose logs app --tail=50
```

### Step 5: Verify Migration File
Check the generated migration file in `migrations/versions/` to ensure:
- Column types are correct
- Nullable/default values are appropriate
- Foreign keys are properly defined
- Downgrade function is complete
- **Handle existing data properly** when adding NOT NULL columns

**Important:** When adding a NOT NULL column to a table with existing data:
1. Add the column as nullable first
2. Update existing rows with a default value
3. Then alter the column to be non-nullable

Example:
```python
def upgrade() -> None:
    # Add column as nullable first
    op.add_column('table_name', sa.Column('new_column', sa.String(), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE table_name SET new_column = 'default_value' WHERE new_column IS NULL")
    # Now make it non-nullable
    op.alter_column('table_name', 'new_column', nullable=False)
```

### Important Notes

1. **Always review auto-generated migrations** - Alembic might not detect all edge cases
2. **Test migrations in development first** before applying to production
3. **Keep migration messages descriptive** for easier tracking
4. **Don't manually edit model and database** - always use migrations
5. **Commit migration files to git** along with model changes

### Common Alembic Commands

```powershell
# Check current migration status
docker compose exec app flask db current

# View migration history
docker compose exec app flask db history

# Downgrade one revision
docker compose exec app flask db downgrade

# Upgrade to specific revision
docker compose exec app flask db upgrade <revision>

# Show SQL without executing
docker compose exec app flask db upgrade --sql
```

## Recent Changes Log

### 2026-01-21: Added rate_type to ShopProgramRate
- **Model Changes:** Added `rate_type` column to distinguish between 'shop' and 'contract' rates
- **Scraper Updates:** Modified `base.py` to extract and store rate_type from scraper data
- **Route Updates:** Updated contract evaluation logic in `public.py` to filter by rate_type
- **Template Updates:** Enhanced contract results display in `result.html`
- **Migration:** Auto-generated via `flask db migrate -m "Add rate_type to ShopProgramRate"`
