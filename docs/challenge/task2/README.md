# Task 2: Document Extraction

`POST /extract`

Given an FDA drug label (plain text or base64 PDF), pull out structured JSON that a downstream system can use directly. The scoring cares about getting the right fields with the right structure — not about how pretty your output reads.

Read the background:

- [customer_brief.md](customer_brief.md) — what the customer needs
- [field_guide.md](field_guide.md) — practical extraction tips
- [engineering_review.md](engineering_review.md) — what judges look for

## Request Contract

Input fields:

- `document_id`
- `document_type`
- `content`
- `content_format`
- `metadata`

`content_format` can be either `text` or `pdf_base64`.

See [../../../py/data/task2/input_schema.json](../../../py/data/task2/input_schema.json) for the formal schema.

## Response Contract

Required output fields:

- `document_id`
- `drug_name`
- `generic_name`
- `manufacturer`
- `indications`
- `dosage_forms`
- `warnings`
- `contraindications`
- `adverse_reactions`
- `active_ingredients`
- `storage`

See [../../../py/data/task2/output_schema.json](../../../py/data/task2/output_schema.json) for the formal schema.

## Resolution Scoring

```
resolution = (0.15 x drug_name + 0.15 x indications + 0.15 x dosage + 0.05 x warnings + 0.15 x contraindications + 0.20 x adverse_reactions + 0.10 x ingredients + 0.05 x metadata) x 100
```

| Dimension | Weight | Metric |
|---|---|---|
| `drug_name` | 15% | Exact match after normalization |
| `indications` | 15% | Soft set F1 |
| `dosage_forms` | 15% | Set F1 |
| `warnings` | 5% | Set F1 |
| `contraindications` | 15% | Soft set F1 |
| `adverse_reactions` | 20% | Token overlap + exact frequency |
| `active_ingredients` | 10% | Token overlap + exact strength/unit |
| `metadata` | 5% | Token F1 |

## What's Hard

Long unstructured documents. Table-like content flattened into prose. Inconsistent wording. PDFs on ~30% of the eval set. Deeply nested output with arrays of objects.

## Tips

- Get the schema right first. Downstream consumers expect stable shape.
- Don't hallucinate missing structure — return null if it's not there.
- PDFs are a reliability problem, not a separate feature.
- `adverse_reactions` and `dosage_forms` carry the most weight — focus there.