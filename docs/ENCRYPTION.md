# Database encryption (Task 5.1)

`db/careerops.db` is plain SQLite until you opt into SQLCipher:

## Enable SQLCipher

1. Install with the `[crypto]` extra (needs `libsqlcipher` headers):
   ```bash
   uv sync --extra crypto
   ```
2. Generate and store a passphrase:
   ```bash
   openssl rand -hex 32 | \
     xargs -I{} security add-generic-password -U \
       -s careerops.db -a encryption_key -w {} && echo stored
   ```
3. Set env var:
   ```bash
   export CAREEROPS_SQLCIPHER=1
   ```
4. Run migration to re-encrypt existing DB:
   ```bash
   uv run python -m db.migrate
   ```

## Verify

```bash
CAREEROPS_SQLCIPHER=1 uv run python -c "from agents.tools.db import get_connection; c=get_connection(); print(c.execute('SELECT count(*) FROM runs').fetchone())"
```
