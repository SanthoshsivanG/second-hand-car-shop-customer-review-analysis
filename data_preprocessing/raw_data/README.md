# raw_data

Holds the **raw input CSV** before any preprocessing.

## Expected file

Place your reviews CSV in this folder (e.g. `combined_reviews.csv` or `reviews.csv`).

## Expected columns

Exactly these three:

| Column | Required | Notes |
|--------|----------|--------|
| `store_name` | yes | Store identifier |
| `stars` | yes | Numeric rating |
| `review` | yes | English review text |

## Notes

- Do not put cleaned or labeled files here.
- Paths are configured via `config.py`, CLI `--input`, or `REVIEW_RAW_CSV`.
