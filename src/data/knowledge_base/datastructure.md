# Data Structure

All sample data are located here, now data is available for 2 project: `telburger` , `telmart`, both follow a same structure, here is a breakdown for `telmart` :

This directory contains 2 folder: `initial_data` and `test_data`, `initial_data`  is used for inital context for retrieval , `test_data` is used for evaluating.

## `initial_data`
contains subdirectories, which considered as a `category` for creating documents, inside each `category` there is a `txt` file which is considered as a `Document` object for django model.

```
├── checkout_support
│   ├── cashier_help.txt
│   ├── payment_issues.txt
│   ├── receipt_questions.txt
│   └── self_checkout_help.txt
├── complaints_and_feedback
│   ├── delivery_complaints.txt
│   ├── employee_feedback.txt
│   ├── product_complaints.txt
│   └── store_experience.txt
├── customer_service_desk
│   ├── exchanges.txt
│   ├── general_questions.txt
│   ├── price_adjustments.txt
│   ├── refunds.txt
│   └── returns.txt
├── membership_and_account
│   ├── gift_cards.txt
│   ├── login_issues.txt
│   ├── walmart_account_help.txt
│   └── walmart_support.txt
├── money_services
│   ├── bill_payment.txt
│   ├── check_cashing.txt
│   ├── money_orders.txt
│   └── money_transfers.txt
├── online_orders
│   ├── delivery_orders.txt
│   ├── missing_items.txt
│   ├── order_status.txt
│   ├── pickup_orders.txt
│   └── substitutions.txt
├── pharmacy_support
│   ├── insurance_questions.txt
│   ├── prescription_pickup.txt
│   ├── refill_questions.txt
│   └── vaccine_appointments.txt
├── privacy_and_security
│   ├── account_security.txt
│   ├── fraud_concerns.txt
│   ├── payment_security.txt
│   └── personal_information.txt
└── product_help
    ├── damaged_items.txt
    ├── item_location.txt
    ├── product_availability.txt
    └── warranty_questions.txt
```

## `test_data`

It is for evaluating RAG system, it contains 2 directory : `raw` and `jsonl`.

### `raw`
`raw` data has a structure like `inital_data` , there are some subdirectories as `category` and txt files, the reason for having the same structure is, different txt files can be added to this subdirectories and be considered for evaluating RAG system. `raw` directory is not used for creating any Django object or saving in the database, its just used for creating `jsonl` file and validating `jsonl` file.

### `jsonl`
it contains this files:

```
query_declerative.jsonl
query_question.jsonl
```

with this format, example:
```json
{"query": "Does the staff throw away my food or refund my card if I completely forget to show up?", "category": "online_orders", "file_name": "pickup_orders.txt"}
```

data inside this file is for evaluating RAG system.

file | description
-- | --
query_declerative.jsonl | queries in declerative tone of voice extracted from raw data
query_question.jsonl | queries in question tone of voice , made from declerative data (to have more similarity the way user asking question)
