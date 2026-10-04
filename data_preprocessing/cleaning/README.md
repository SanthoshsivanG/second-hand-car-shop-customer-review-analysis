# cleaning

First transform stage: validate raw columns and clean review text.

## Responsibilities

- Require raw columns: `store_name`, `stars`, `review`
- Clean the `review` column:
  - remove null / empty / whitespace-only reviews
  - normalize excessive whitespace
  - remove emojis
  - remove unwanted special characters
  - keep English letters, useful numbers, and normal NLP punctuation

## Code

| File | Role |
|------|------|
| `clean_reviews.py` | Cleaning helpers and stage entrypoint |

## Position in pipeline

```
raw_data → cleaning → labeling → (future stages) → validation → processed_data
```
