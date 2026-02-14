# Consolidated Import Format (JSON)

This document defines the consolidated JSON format used to manually import bonus-program rates via the admin upload.

## Top-level structure

```json
{
  "program": "ExampleProgram",
  "source": "ExampleSource",
  "extracted_at": "2026-02-08T12:34:56Z",
  "shops": [
    {
      "name": "Example Shop",
      "source_id": "12345",
      "logo": "https://example.com/logo.png",
      "rates": [
        {
          "program": "ExampleProgram",
          "points_per_eur": 0.0,
          "cashback_pct": 3.5,
          "cashback_absolute": 0.0,
          "points_absolute": 0.0,
          "point_value_eur": 0.0,
          "category": "Elektronik",
          "rate_note": "bis zu 3,5%"
        }
      ]
    }
  ]
}
```

## Field definitions

### Top-level

- `program` (string, required): Bonus program name (e.g., `Dealwise`, `Payback`, `CorporateBenefit`).
- `source` (string, required): Source identifier (e.g., `Dealwise`, `CorporateBenefit`).
- `extracted_at` (string, required): ISO-8601 timestamp of the extract.
- `shops` (array, required): List of shop objects.

### Shop object

- `name` (string, required): Shop/merchant name.
- `source_id` (string, optional): Unique ID from the source system.
- `logo` (string, optional): Logo URL.
- `rates` (array, required): List of rate objects.

### Rate object

- `program` (string, required): Bonus program name.
- `points_per_eur` (number, optional, default `0.0`): Points per 1 EUR spent.
- `cashback_pct` (number, optional, default `0.0`): Cashback percentage.
- `cashback_absolute` (number, optional, default `0.0`): Absolute cashback per transaction.
- `points_absolute` (number, optional, default `0.0`): Absolute points per transaction.
- `point_value_eur` (number, optional, default `0.0`): EUR value per point (if applicable).
- `category` (string, optional): Rate category.
- `rate_note` (string, optional): Free-text note (e.g., “bis zu 3,5%”).

## Import flow (rates)

1. Transform the raw extract into this consolidated JSON format.
2. Upload the consolidated JSON on the first admin page (import section).

## Tooling

Use the transformer script:

```bash
python debug/transform_dealwise_extract.py --input import/source_extract.json --output import/consolidated_rates.json --program ExampleProgram
```

## Coupon import module (sketch)

Some sources (e.g., corporate benefit portals) are better handled via manual JSON import rather than scrapers. The proposed coupon import module mirrors the consolidated rates flow but targets coupon data.

### Proposed coupon JSON format

```json
{
  "program": "CorporateBenefit",
  "source": "CorporateBenefit",
  "extracted_at": "2026-02-08T12:34:56Z",
  "coupons": [
    {
      "title": "10% Rabatt",
      "merchant": "Example Shop",
      "code": "SAVE10",
      "discount_text": "10%",
      "valid_from": "2026-02-01",
      "valid_to": "2026-03-01",
      "url": "https://example.com/coupon",
      "category": "Elektronik",
      "note": "Nur online"
    }
  ]
}
```

### Coupon import flow (sketch)

1. Admin uploads a consolidated coupon JSON.
2. UI shows preview (program + number of coupons).
3. On confirmation, a worker job is enqueued to import coupons.
4. Worker posts to a new API endpoint (e.g., `/api/coupon-import`) in batches.

### Required backend pieces (sketch)

- New data model/table for coupons (if not present).
- Admin endpoints:
  - `POST /admin/import_coupons/preview`
  - `POST /admin/import_coupons/confirm`
- Worker task:
  - `run_coupon_import_job(import_payload, run_id, requested_by)`
- API endpoint to ingest coupon batches:
  - `POST /api/coupon-import`

If you want, I can implement the coupon import module next.
