# labeling

Logic-based labeling from structured fields (not NLP models).

## Current logic: rating-based satisfaction

Derives `satisfaction` from `stars` only:

| Rule | Label |
|------|--------|
| `stars < 4` | `negative` |
| `stars >= 4` | `positive` |

This is a **rating-based satisfaction label**, not NLP sentiment analysis. Review text tone is ignored.

## Code

| File | Role |
|------|------|
| `satisfaction.py` | Star → positive/negative mapping |

## Position in pipeline

```
raw_data → cleaning → labeling → (future stages) → validation → processed_data
```

Additional labeling or feature stages may be added **after this folder and before `validation/`** in later prompts.
