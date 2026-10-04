# topic_modeling

BERTopic topic discovery **per customer-journey stage × satisfaction**, then short category names from Gemini.

## Goal

For each of the 4 journeys (`pre_visit`, `sales`, `contract`, `after_sales`) **and** each satisfaction (`positive`, `negative`):

1. Take reviews where that journey `*_pred == 1` **and** `satisfaction` matches
2. Run BERTopic with a strong sentence embedding model
3. Keep **at least 10 topics** per slice (default 10, max 15 → ≤ 120 topics total)
4. Send **5 sample reviews** per topic to Gemini with a polarity-aware naming prompt
5. Save results as JSON

Positive slices get strength-style titles; negative slices get complaint-style titles.

## Files

| Path | Role |
|------|------|
| `bertopic_topics.py` | BERTopic + Gemini naming logic |
| `run_topics.py` | CLI entry point |
| `output/topics_by_journey.json` | Generated category JSON |

## Setup

```bash
cd data_preprocessing
source .venv/bin/activate
pip install -r requirements-topics.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY=...
```

## Run

```bash
# On processed reviews (preferred)
python -m topic_modeling.run_topics --input processed_data/reviews_processed.csv

# Or as part of the main pipeline
python run_pipeline.py --input raw_data/combined_reviews.csv --topics
```

## Embedding model

Default: `sentence-transformers/all-mpnet-base-v2`  
Override with `TOPIC_EMBEDDING_MODEL` in `.env`.

## JSON shape

See `output/topics_by_journey.json` after a run. Each journey has `by_satisfaction.positive|negative` with:

- `topic_id`
- `name` (Gemini; polarity-matched)
- `satisfaction`
- `keywords` (BERTopic)
- `document_count`
- `sample_reviews` (≤ 5, used for naming)

A flat `topics` list (same items) is also written for simpler consumers.

## Cost control

Up to **5 sample comments × ≤ 10–15 topics × 4 journeys × 2 sentiments** are sent to Gemini.
