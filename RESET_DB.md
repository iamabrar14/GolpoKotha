# Reset / Recreate the SQLite DB (to apply CASCADE FKs and NOCASE usernames)

SQLite only enforces `ondelete=CASCADE` when foreign keys are turned **ON** and the schema
was created with those constraints. Also, to enforce case-insensitive UNIQUE(username),
the `username` column uses `collation='NOCASE'`, which requires recreating the unique index.

Do this once after pulling the fix:

```bash
# Stop the app
# Delete the existing dev DB file (adjust the path/name if different)
rm app/site.db  # or your configured path

python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
...
```
