# validation

Final quality gate before writing `processed_data/`.

## Checks

- Required columns: `store_name`, `stars`, `review`, `satisfaction`
- Journey columns: `pre_visit_*`, `sales_*`, `contract_*`, `after_sales_*` (`prob` + `pred`)
- `satisfaction` in `{positive, negative}`
- Journey `*_pred` in `{0, 1}`; `*_prob` in `[0, 1]`
- Non-empty reviews; numeric stars
- Logs row counts, satisfaction counts, unique stores, journey positive counts
