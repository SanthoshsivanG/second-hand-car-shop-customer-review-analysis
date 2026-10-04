# Customer Review AI

AI-powered analysis of customer reviews for a second-hand car shop. The project turns raw review text into structured insights—sentiment, themes, and actionable signals—to support service and sales decisions.

## Architecture

Three independent layers with clear boundaries:

| Layer | Role |
|-------|------|
| `data_preprocessing/` | Data cleaning, normalization, and feature preparation |
| `app/` | Analysis logic and user-facing application |
| `infra/` | Deployment, runtime, and environment configuration |

Raw reviews flow through preprocessing into analysis in `app/`. `infra/` packages and runs those components so the pipeline can be reproduced locally or in the cloud.

## Directory purpose

### `data_preprocessing/`

Ingest and prepare review data: cleaning, language/text normalization, labeling helpers, and train/eval-ready datasets. No serving or UI concerns.

### `app/`

Dashboard UI and API that consume preprocessed reviews:

- `app/frontend/` — React + Vite + TypeScript dashboard
- `app/backend/` — FastAPI (`/api/filters`, `/api/heatmap`, `/api/topics`)
- Run from `app/`: `docker compose up --build` → UI at http://localhost:3000

See `app/README.md` for details.

### `infra/`

Terraform modules for a simple AWS host (EC2 + Postgres via Docker + Caddy HTTPS + Route 53).  
See `infra/README.md`. Domain/secrets stay in local `terraform.tfvars` (gitignored).

## Technology stack

- **Language:** Python, TypeScript
- **Data / ML:** pandas; journey BiLSTM classification + BERTopic topic modeling in `data_preprocessing/`
- **App:** FastAPI + React (Vite) dashboard under `app/`
- **Infra:** Docker Compose locally; Terraform on AWS for portfolio deploy

## How the parts interact

```
reviews (raw)
    → data_preprocessing/   # clean & prepare
    → app/                 # analyze & present
    → infra/               # build, run, deploy the above
```

1. `data_preprocessing/` produces cleaned datasets and artifacts.
2. `app/` loads those artifacts and serves the dashboard (heatmap, topics, AI ideas).
3. `infra/` deploys the app stack to AWS when you run Terraform.

## Sample data

A small committed sample lives at `data_preprocessing/sample_data/sample_reviews.csv`.  
Full review CSVs are gitignored.

## Status

- `data_preprocessing/` — cleaning, journey labels, BERTopic (journey × satisfaction)
- `app/` — dashboard (heatmap + topic bubbles + idea modal) via Docker Compose
- `infra/` — AWS Terraform (manual `apply`)
