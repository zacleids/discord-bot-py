# Database Migrations

This project uses [peewee-migrate](https://github.com/klen/peewee_migrate) to manage database schema changes. All migration commands must be run from inside an active `.venv`.

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# Install dependencies (includes peewee-migrate)
pip install -r requirements.txt
```

## Common Commands

All commands below assume the virtual environment is active and are run from the project root.

### Run All Pending Migrations

```bash
pw_migrate migrate --database sqlite:///shared/db/bot_orm.db --directory migrations
```

### List Migrations

Shows which migrations have been applied and which are pending:

```bash
pw_migrate list --database sqlite:///shared/db/bot_orm.db --directory migrations
```

Example output:

```
List of migrations:

- [x] 001_initial_schema
- [ ] 002_add_notes_column

Done: 1, Pending: 1
```

### Create a New Migration

Create an empty migration file to fill in manually:

```bash
pw_migrate create my_migration_name --directory migrations
```

Auto-generate a migration by scanning model changes:

```bash
pw_migrate create my_migration_name --auto --auto-source=shared --database sqlite:///shared/db/bot_orm.db --directory migrations
```

### Rollback Migrations

Rollback the last migration:

```bash
pw_migrate rollback --count 1 --database sqlite:///shared/db/bot_orm.db --directory migrations
```

Rollback the last N migrations:

```bash
pw_migrate rollback --count 3 --database sqlite:///shared/db/bot_orm.db --directory migrations
```

### Run a Specific Migration

```bash
pw_migrate migrate --name 002_add_notes_column --database sqlite:///shared/db/bot_orm.db --directory migrations
```

### Verbose Output

Add `-v` to any command for detailed output:

```bash
pw_migrate migrate --database sqlite:///shared/db/bot_orm.db --directory migrations -v
```

---

## Migration File Structure

Migration files live in the `migrations/` directory and are executed in filename order. Each file contains a `migrate()` function and optionally a `rollback()` function:

```python
import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Apply the migration."""
    pass


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Reverse the migration."""
    pass
```

---

## Migration Examples

### Adding a New Column

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_fields("info", notes=pw.TextField(null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_fields("info", "notes")
```

### Removing a Column

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_fields("info", "notes")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_fields("info", notes=pw.TextField(null=True))
```

### Adding an Index

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_index("info", "notes", "item_id")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.drop_index("info", "notes", "item_id")
```

### Adding a Unique Index

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_index("info", "notes", "timestamp", unique=True)


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.drop_index("info", "notes", "timestamp")
```

### Renaming a Column

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.rename_field("info", "notes", "observations")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.rename_field("info", "observations", "notes")
```

### Changing a Column Type

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.change_fields("info", notes=pw.CharField(max_length=500, null=True))


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.change_fields("info", notes=pw.TextField(null=True))
```

### Renaming a Table

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.rename_table("info", "info_keeping")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.rename_table("info_keeping", "info")
```

### Adding a NOT NULL Constraint

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_not_null("info", "owner_id")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.drop_not_null("info", "owner_id")
```

### Creating a New Table

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    @migrator.create_model
    class Alert(pw.Model):
        id = pw.AutoField()
        notes = pw.CharField(index=True, max_length=255)
        message = pw.TextField()
        created_at = pw.DateTimeField()

        class Meta:
            table_name = "alert"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_model("alert")
```

### Dropping a Table

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_model("alert")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    @migrator.create_model
    class Alert(pw.Model):
        id = pw.AutoField()
        notes = pw.CharField(index=True, max_length=255)
        message = pw.TextField()
        created_at = pw.DateTimeField()

        class Meta:
            table_name = "alert"
```

### Running Custom SQL

```python
def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.sql("UPDATE info SET status = 'locked' WHERE status = 'expired'")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.sql("UPDATE trade SET status = 'expired' WHERE status = 'locked'")
```

---

## Available Migrator Methods

| Method | Description |
| --- | --- |
| `migrator.create_model(Model)` | Create a new table from a model class |
| `migrator.remove_model(name)` | Drop a table |
| `migrator.add_fields(model, **fields)` | Add columns to a table |
| `migrator.remove_fields(model, *names)` | Remove columns from a table |
| `migrator.change_fields(model, **fields)` | Change column type or constraints |
| `migrator.rename_field(model, old, new)` | Rename a column |
| `migrator.rename_table(model, new_name)` | Rename a table |
| `migrator.add_index(model, *cols, unique=False)` | Add an index |
| `migrator.drop_index(model, *cols)` | Drop an index |
| `migrator.add_not_null(model, *fields)` | Add NOT NULL constraint |
| `migrator.drop_not_null(model, *fields)` | Remove NOT NULL constraint |
| `migrator.add_default(model, field, default)` | Set a default value |
| `migrator.add_constraint(model, name, sql)` | Add a constraint |
| `migrator.drop_constraints(model, *names)` | Drop constraints |
| `migrator.sql(sql)` | Execute raw SQL |

---

## Tips

- **Always test migrations** on a copy of your database before running on production.
- **Keep rollbacks up to date** — every `migrate()` should have a corresponding `rollback()`.
- **One logical change per migration** — don't mix unrelated schema changes in a single file.
- Migration files are executed in filename order. The numeric prefix (e.g., `001_`, `002_`) controls ordering.
- For the test database (`local.test.db`), migrations are not used — `create_dbs.py` recreates all tables from scratch on each test run.
