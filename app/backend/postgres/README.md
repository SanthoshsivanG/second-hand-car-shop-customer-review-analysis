# Postgres (app database)

Stores:

1. `idea_policy` — editable AI generation rules (single row, `id = 1`)
2. `generated_ideas` — saved idea generations + source comments

## Files

| File | Role |
|------|------|
| `init.sql` | Creates tables on first container start |
| `seed_policy.md` | Default policy text seeded into DB if empty |

## Connection

Set by Docker Compose:

```text
DATABASE_URL=postgresql://review:review@db:5432/review_dashboard
```

## Reset DB (dev)

```bash
cd app
docker compose down -v
docker compose up --build
```

`-v` removes the volume so `init.sql` runs again.
