# journey_classification

Multi-label customer-journey stage classification (after satisfaction labeling).

## Categories

| Code | Meaning |
|------|---------|
| `pre_visit` | Before coming to the shop (online, appointment, phone, transfer) |
| `sales` | Salesperson / buying-selling interaction |
| `contract` | Paperwork, financing, signing, registration docs |
| `after_sales` | Maintenance, warranty, service after purchase |

A review can have multiple labels (multi-label).

## Files in this folder

| File | Role |
|------|------|
| `reviews_manual_label_sample_800_labeled_fixed.csv` | Manual ground-truth labels (train/eval) |
| `reviews_with_journey_preds.csv` | Full-dataset predictions from the trained BiLSTM (Colab) |
| `model/` | Place `best_bilstm_model.pt` + `model_config.json` for local inference |

## How the pipeline uses this stage

Order:

```
raw_data → cleaning → labeling → journey_classification → validation → processed_data
```

`apply_journey_classification()`:

1. If `model/best_bilstm_model.pt` and `model/model_config.json` exist → run local BiLSTM inference (needs `torch`).
2. Else if `reviews_with_journey_preds.csv` exists → merge `*_prob` / `*_pred` columns onto the current frame.
3. Else → fail with a clear error.

Training stays in Colab for now (from-scratch BiLSTM). Copy the saved model artifacts into `model/` when you want fully local inference.

## Output columns added

- `pre_visit_prob`, `pre_visit_pred`
- `sales_prob`, `sales_pred`
- `contract_prob`, `contract_pred`
- `after_sales_prob`, `after_sales_pred`

Predictions are `0`/`1`. Probabilities are in `[0, 1]`.
