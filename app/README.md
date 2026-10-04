# Review dashboard (`app/`)

Web dashboard for exploring processed customer reviews: journey × sentiment heatmap and a 4-quadrant BERTopic bubble chart (count × average stars).

## Layout

```
app/
  frontend/   # React + Vite + TypeScript (Recharts)
  backend/    # FastAPI
    postgres/ # init.sql + seed policy
  docker-compose.yml
```

## AWS (Terraform)

Infrastructure lives in `../infra/` (modules for IAM, security group, EC2, DNS).  
Copy `infra/terraform.tfvars.example` → `infra/terraform.tfvars` (gitignored), then you run `terraform plan` / `terraform apply` yourself. Domain values must stay only in `terraform.tfvars`.

## Run with Docker (recommended)

Requires Docker Desktop (or another Docker engine) running. Host ports **8000**, **3000**, and **5432** must be free.

From this directory:

```bash
cd app
docker compose up --build
```

Then open:

- UI: http://localhost:3000
- API: http://localhost:8000/api/health

Stop with `Ctrl+C` or `docker compose down`.

If port 8000 is already in use, remap for a one-off run, e.g. publish backend as `8001:8000` via a Compose override file.

Data is mounted read-only from:

- `../data_preprocessing/processed_data/reviews_processed.csv`
- `../data_preprocessing/topic_modeling/output/topics_by_journey.json`

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/filters` | Distinct `store_name`, `satisfaction`, `journey`, `topic` (linked via query params) |
| GET | `/api/heatmap` | Journey × sentiment cell counts |
| GET | `/api/topics?journey=` | Topic bubble sizes for a journey (optional filters) |
| GET | `/api/ideas` | AI keep/improve ideas from 5 longest topic comments (also saved to DB) |
| GET | `/api/policy` | Read idea-generation policy from Postgres |
| PUT | `/api/policy` | Update policy (`{"content": "..."}`) |

Shared optional query params (repeatable): `store_name`, `satisfaction`, `journey`, `topic`.

## Postgres

Compose starts a `db` service (Postgres 16). Schema: `app/backend/postgres/init.sql`.

| Table | Purpose |
|-------|---------|
| `idea_policy` | Single editable AI policy row (`id = 1`) |
| `generated_ideas` | Saved idea generations + source comments |

Edit policy in the UI (**Edit policy**) or via `PUT /api/policy`.
Uses `GEMINI_API_KEY` from `data_preprocessing/.env`.

Reset DB volume (re-runs `init.sql`):

```bash
docker compose down -v
docker compose up --build
```

## Local development (optional)

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend (proxies `/api` to `:8000`):

```bash
cd frontend
npm install
npm run dev
```

## Topic filter note

Topics are built per **journey × satisfaction**. The bubble chart for a heatmap cell only shows topics for that sentiment. Matching reviews to a topic is still approximate: journey `*_pred == 1` plus distinctive keyword overlap (BERTopic JSON does not store per-review membership for all rows).
