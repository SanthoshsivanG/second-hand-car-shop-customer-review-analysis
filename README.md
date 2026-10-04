# Customer Review AI

AI-powered analysis of customer reviews for a second-hand car shop.  
Raw reviews become **satisfaction**, **journey stages**, **topics**, and **keep/improve ideas** for the business.

## How it works (big picture)

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ 1. Data preprocessing│     │ 2. Dashboard (app)   │     │ 3. Infra (optional)  │
│                      │     │                      │     │                      │
│  clean → label →     │────▶│  heatmap → topics →  │────▶│  Docker / AWS        │
│  journey → topics    │     │  AI ideas            │     │  Terraform + HTTPS   │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
         offline                      interactive                   deploy
```

| Layer | Folder | Job |
|-------|--------|-----|
| Preprocessing | `data_preprocessing/` | Turn raw CSV into analysis-ready data + topic catalog |
| App | `app/` | Explore insights in the browser; generate AI ideas |
| Infra | `infra/` | Host the app (local Docker or AWS) |

---

## 1) Data preprocessing (offline)

Runs once (or when data changes). Produces files the dashboard reads.

```
raw CSV
   │
   ▼
┌─────────────┐   stars ≥ 4 → positive
│  Cleaning   │   stars < 4 → negative
└──────┬──────┘
       ▼
┌─────────────┐
│ Satisfaction│  column: satisfaction
└──────┬──────┘
       ▼
┌─────────────┐   BiLSTM (multi-label)
│   Journey   │   pre_visit / sales / contract / after_sales
└──────┬──────┘   columns: *_pred
       ▼
┌─────────────┐   BERTopic per journey × satisfaction
│   Topics    │   + Gemini names the topics
└──────┬──────┘
       ▼
  reviews_processed.csv
  topics_by_journey.json
```

### Journey stages

Each review can touch more than one stage:

```
pre_visit  →  sales  →  contract  →  after_sales
 (research)   (buy)     (paperwork)   (service)
```

### BERTopic + Generative AI (topic names)

Topics are **discovered** by BERTopic (embeddings + clustering).  
**Names** are written by Gemini from a few sample reviews — polarity-aware:

```
                    ┌─────────────────────────┐
  reviews where     │  BERTopic               │
  journey = sales   │  find clusters          │
  AND sat = negative│  + keywords             │
                    └───────────┬─────────────┘
                                │
                                ▼  5 sample comments / topic
                    ┌─────────────────────────┐
                    │  Gemini                 │
                    │  short topic title      │
                    │  (negative wording)     │
                    └───────────┬─────────────┘
                                │
                                ▼
              e.g. "Service wait frustration"
```

Positive slices get strength-style titles; negative slices get complaint-style titles.  
Same idea for all 4 journeys × 2 sentiments (8 slices).

Details: `data_preprocessing/README.md` and `data_preprocessing/topic_modeling/README.md`.

---

## 2) Dashboard app (interactive)

```
Browser (React)
      │
      │  filters / click cell / click topic
      ▼
FastAPI backend
      │
      ├── reads reviews_processed.csv
      ├── reads topics_by_journey.json
      ├── Postgres: idea_policy + generated_ideas
      └── Gemini: keep / improve bullets
```

### What you see

```
┌──────────────────────────────────────────────────────────┐
│  Filters: store · satisfaction · journey · topic         │
├────────────────────────────┬─────────────────────────────┤
│  Heatmap                   │  Topic bubbles              │
│  journey × positive/neg    │  4 quadrants                │
│  (click a cell)            │  count × avg stars          │
│                            │  (click a bubble)           │
└────────────────────────────┴─────────────────────────────┘
                    │
                    ▼
         Idea modal (Gemini)
         · positive cell → "points to keep"
         · negative cell → "improvement ideas"
```

### AI ideas + Generative AI

When you click a topic bubble:

```
selected journey + topic + satisfaction
        │
        ▼
 pick 5 longest matching reviews
        │
        ▼
 load idea_policy from Postgres
        │
        ▼
┌───────────────────────────────┐
│  Gemini                       │
│  follow policy                │
│  return 4–6 bullet ideas      │
└───────────────┬───────────────┘
                │
                ▼
 show in modal + save to generated_ideas
```

You can edit the policy in the UI (**Edit policy**). That text is what Gemini follows next time.

Local run:

```bash
cd app
docker compose up --build
# UI http://localhost:3000
```

Needs `GEMINI_API_KEY` (see `data_preprocessing/.env.example` / `app/.env.example`).

Details: `app/README.md`.

---

## 3) Infra (optional deploy)

- **Local:** Docker Compose in `app/` (frontend + backend + Postgres)  
- **AWS:** Terraform in `infra/` (EC2 + Caddy HTTPS + DNS) — see `infra/README.md`  
  Secrets/domain only in local `terraform.tfvars` (gitignored).

---

## Repository map

```
.
├── data_preprocessing/   # offline ML / ETL pipeline
│   └── sample_data/      # small committed sample CSV
├── app/                  # FastAPI + React dashboard
└── infra/                # Terraform (AWS)
```

## Sample data

`data_preprocessing/sample_data/sample_reviews.csv` — small public sample.  
Full review CSVs are gitignored.

## Status

- `data_preprocessing/` — cleaning, journey labels, BERTopic (journey × satisfaction) + Gemini naming  
- `app/` — heatmap, topic bubbles, editable policy, Gemini keep/improve ideas  
- `infra/` — AWS Terraform (you run `apply`)
