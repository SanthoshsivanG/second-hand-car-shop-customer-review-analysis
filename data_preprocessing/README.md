# Data Preprocessing

Cleans raw English customer reviews and produces satisfaction labels, journey stages, and optional BERTopic themes.

## Folder layout

```
data_preprocessing/
├── sample_data/              # small committed sample CSV for demos
├── raw_data/                 # full CSVs gitignored
├── cleaning/
├── labeling/
├── journey_classification/
├── topic_modeling/           # BERTopic per journey × satisfaction + Gemini names
├── validation/
├── processed_data/           # full CSVs gitignored
├── .env.example              # copy to .env for GEMINI_API_KEY
├── config.py
├── pipeline.py
├── run_pipeline.py
├── requirements.txt
└── requirements-topics.txt
```

## Pipeline flow

```
raw_data → cleaning → labeling → journey_classification
        → validation → processed_data → (optional) topic_modeling
```

## Setup

```bash
cd data_preprocessing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For BERTopic + Gemini naming:
pip install -r requirements-topics.txt
cp .env.example .env
# put your Gemini API key in .env
```

## Run

```bash
# Core pipeline
python run_pipeline.py --input raw_data/combined_reviews.csv

# Core pipeline + BERTopic topics
python run_pipeline.py --input raw_data/combined_reviews.csv --topics

# Topics only (uses existing processed CSV)
python -m topic_modeling.run_topics --input processed_data/reviews_processed.csv
```

Topic JSON is written to `topic_modeling/output/topics_by_journey.json`.

## Topic modeling notes

- Embedding model: `sentence-transformers/all-mpnet-base-v2`
- At least 10 topics × 4 journeys × 2 sentiments (default 10, max 15 per slice)
- Gemini names topics with polarity (positive vs negative titles)
- Gemini sees only 5 sample reviews per topic (cost control)
- Never commit `.env`
