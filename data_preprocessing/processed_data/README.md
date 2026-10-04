# processed_data

Final CSV after validation.

## Default output

`reviews_processed.csv`

## Output schema

| Column | Description |
|--------|-------------|
| `store_name` | Store identifier |
| `stars` | Star rating |
| `review` | Cleaned review text |
| `satisfaction` | `positive` / `negative` (from stars) |
| `pre_visit_prob` / `pre_visit_pred` | Journey stage |
| `sales_prob` / `sales_pred` | Journey stage |
| `contract_prob` / `contract_pred` | Journey stage |
| `after_sales_prob` / `after_sales_pred` | Journey stage |
