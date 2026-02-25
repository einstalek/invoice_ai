# Inflow

A web platform for companies (big and very small) and accountants, simplifying booking and invoice processing using modern LLM tools.


## Overview

Inflow is a system simplifying work of accountants and booking for business owners. Right now we are working on a MVP version of the product. Business owners register their company on our platform, providing basic information about their business, and add their accountant(s) to the created organization structure where accountants and business owner oversee the whole invoice understanding and logging (booking) flow. The whole flow is built to make the booking easy and fast.

## Users and roles
All platform users come in two categories, accountants and owners. 
One organization can have multiple owners and multiple accountants. Owner is usually (but not necessary) the one uploading invoice(s) to be processed by our system. Our system uses LLM models to understand the invoice and extract specific fields from it, logging this invoice and those fields in the platform for the accountants later to verify or manually edit some things about those invoices and fields. Later the owner (usually, but not necessary) can log these invoices into an ERP system of their choice (which is in our MVP include either google sheet or quick books).

## Core Features

System uses an LLM run over text extracted from pdf invoices to extract information, returning a json, kinda like this:
"""
Example format:
{ 
  /// Invoice data
  "general_info_reasoning": "<value>",
  "invoice_date": {"value": "<value>", "confidence": "strong confidence"}, /// When the invoice was created, in "dd.mm.yyyy" format
  "invoice_due_date": {"value": "<value>", "confidence": "strong confidence"}, /// When the invoice is due, in "dd.mm.yyyy" format
  "invoice_number": {"value": "<value>", "confidence": "strong confidence"}, /// A unique ID for tracking each bill 
  "invoice_total_amounts": {"value": "<value>", "confidence": "medium confidence"}, /// numeric amount including VAT (no currency symbols)
  "invoice_currency": {"value": "<value>", "confidence": "strong confidence"},
  "description_keyword": {"value": "<value>", "confidence": "medium confidence"}, ///  e.g., software, hosting, legal, medical, rent, etc, (type of service provided, if can be deduced),
  "vat_rates": {"value": "<value>", "confidence": "medium confidence"}, /// (0, 9, 13, 24, ...), if VAT rate(s) shown, no percent sign
  "supply_type": {"value": "<value>", "confidence": "medium confidence"},  /// one of: GOODS, SERVICES,
  "service_category": {"value": "<value>", "confidence": "medium confidence"}, /// one of: SERV_9, SERV_13, SERV_24, SERV_0, SERV_EX

  /// Supplier data
  "supplier_info_reasoning": "<value>",
  "supplier_name": {"value": "<value>", "confidence": "strong confidence"},
  "supplier_address": {"value": "<value>", "confidence": "medium confidence"},
  "supplier_country": {"value": "<value>", "confidence": "medium confidence"},  /// Should be a proper country name
  "supplier_country_group": {"value": "<value>", "confidence": "medium confidence"}, /// one of: EE, EU_OTHER, NON_EU
  "supplier_vat_id": {"value": "<value>", "confidence": "medium confidence"},
  "supplier_email": {"value": "<value>", "confidence": "medium confidence"},

  /// Buyer data
  "buyer_info_reasoning": "<value>",
  "buyer_name": {"value": "<value>", "confidence": "strong confidence"},
  "buyer_address": {"value": "<value>", "confidence": "medium confidence"},
  "buyer_country": {"value": "<value>", "confidence": "medium confidence"},  /// Should be a proper country name
  "buyer_country_group": {"value": "<value>", "confidence": "medium confidence"}, /// one of: EE, EU_OTHER, NON_EU
  "buyer_vat_id": {"value": "<value>", "confidence": "medium confidence"},
  "buyer_email": {"value": "<value>", "confidence": "medium confidence"},
}
"""

This allows the accountants of organization quickly approve or edit invoice submissions before booking them.

All the submissions and their statuses are accessible as a table in our platform. Accountants or owners can filter invoices by different fields and access pdfs and extracted fields from old submissions if needed.

Users see notifications on the platform, letting them know of invites, requests for edits and things like that.

## User Flow example

1. Owner (Max) registering and then creating his org on platform
Max owns his company called DFlow. He registers on our platform using his google account. He then creates an organization entity of his company, filling some form with fields like company name, vat number etc -- all the usual things. Now Max has access to our smart tools allowing him to upload his invoices, review parsed information, edit if needed, and book into his ERP system, for which he uses google sheet.

2. Owner (Max) gets an accountant (Tom).
Max can invite Tom (by email) to join his organization on our platform. Tom registers and joins (in a non-owner role) and now he also sees all the invoice submissions which he will be reviewing. Usually it will be Tom who edits extracted fields in invoices when he sees some errors or some problems and eventually approving invoices. Max can see the same submissions (with less metadata info displayed for him since he doesn't really need that) and log into ERP approved invoices. He can also request edits to already approved submissions so that Tom attends to that.

3. Owner (Max) now has a whole team of accountants. Now he can require so that invoice submissions would need more than 1 approval to be able to logged to ERP. The flow is similar to the one before, with flexible going back and forth between editing and approving/requesting edits.

## Data model

8 entities total.

### User
Platform-level identity, independent of orgs.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | string | unique, login identifier |
| full_name | string | |
| google_oauth_id | string | unique, nullable |
| is_active | bool | default true |
| created_at | datetime | |

Roles live on OrganizationMembership, not here. A person can be an owner in one org, accountant in another.

### Organization

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | string | |
| vat_number | string | nullable |
| address | text | nullable |
| country | string | nullable |
| erp_type | enum | NONE / GOOGLE_SHEETS / QUICKBOOKS, default NONE |
| erp_config | JSON | nullable, credentials + config for the selected ERP |
| required_approvals | int | default 1, minimum 1 |
| created_at | datetime | |

ERP config lives here, not on User — the org picks its ERP, not the individual.

### OrganizationMembership
Doubles as the invite mechanism — no separate invite table.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user | FK(User) | nullable — null while invite is pending (user hasn't registered yet) |
| organization | FK(Org) | |
| role | enum | OWNER / ACCOUNTANT |
| status | enum | PENDING / ACTIVE / DEACTIVATED |
| invited_email | string | always populated, used to match when user registers |
| invited_by | FK(User) | nullable |
| created_at | datetime | |

Constraints: unique(user, organization) where user is not null; unique(invited_email, organization).

### Supplier
Normalized per-org supplier directory. Grows organically from invoices.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization | FK(Org) | scoped per org |
| name | string | |
| vat_id | string | nullable |
| address | text | nullable |
| country | string | nullable |
| country_group | enum | EE / EU_OTHER / NON_EU, nullable |
| email | string | nullable |
| created_at | datetime | |
| updated_at | datetime | |

Constraint: unique(organization, vat_id) where vat_id is not null.

After LLM extraction, system can auto-match by supplier_vat_id against existing Supplier records for that org. If no match, accountant can link manually or create a new Supplier during review.

### Invoice
The central entity.

**Lifecycle & ownership fields:**

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization | FK(Org) | |
| uploaded_by | FK(User) | |
| pdf_file | file path | the original PDF |
| status | enum | see lifecycle below |
| supplier | FK(Supplier) | nullable, linked after extraction or manually by accountant |
| current_approval_round | int | default 1, increments on edit-request |
| approvals_obtained | int | default 0, resets on round change |
| booked_at | datetime | nullable |
| booked_by | FK(User) | nullable |
| created_at | datetime | |
| updated_at | datetime | |

**Extracted / edited fields — typed columns for querying and filtering:**

| Field | Type |
|---|---|
| invoice_number | string, nullable |
| invoice_date | date, nullable |
| invoice_due_date | date, nullable |
| total_amount | decimal, nullable |
| currency | string, nullable |
| description_keyword | string, nullable |
| vat_rates | string, nullable |
| supply_type | enum (GOODS/SERVICES), nullable |
| service_category | enum (SERV_0/SERV_9/SERV_13/SERV_24/SERV_EX), nullable |
| supplier_name | string, nullable |
| supplier_address | string, nullable |
| supplier_country | string, nullable |
| supplier_country_group | enum (EE/EU_OTHER/NON_EU), nullable |
| supplier_vat_id | string, nullable |
| supplier_email | string, nullable |
| buyer_name | string, nullable |
| buyer_address | string, nullable |
| buyer_country | string, nullable |
| buyer_country_group | enum (EE/EU_OTHER/NON_EU), nullable |
| buyer_vat_id | string, nullable |
| buyer_email | string, nullable |

**LLM output fields:**

| Field | Type | Notes |
|---|---|---|
| llm_raw_response | JSON | nullable, the complete LLM output — immutable after extraction |
| extracted_text | text | nullable, the text pulled from the PDF before LLM |
| extraction_error | text | nullable, populated if extraction fails |

Confidence scores are NOT separate columns. They live inside llm_raw_response. The frontend reads them from there for display. No one filters by confidence. This eliminates 18 columns of bloat.

LLM vs human edit tracking: compare current column values against corresponding values in llm_raw_response. InvoiceActivity captures each individual edit with a diff.

The extracted supplier fields (supplier_name, etc.) on Invoice are the point-in-time data from that specific PDF. The Supplier FK is the link to the canonical entity for filtering ("show all invoices from this supplier").

### InvoiceApproval

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| invoice | FK(Invoice) | |
| user | FK(User) | the reviewer |
| round | int | matches invoice.current_approval_round |
| decision | enum | APPROVED / EDIT_REQUESTED |
| comment | text | nullable, required for EDIT_REQUESTED |
| created_at | datetime | |

Constraint: unique(invoice, user, round) — one decision per reviewer per round.

How multi-approval works:
1. Accountant approves → record created with decision=APPROVED, invoice.approvals_obtained increments.
2. If approvals_obtained >= organization.required_approvals → invoice status becomes APPROVED.
3. If anyone submits EDIT_REQUESTED → current_approval_round increments, approvals_obtained resets to 0, status goes back to PENDING_REVIEW.
4. Old round approvals stay in the database — full history preserved.

### InvoiceActivity
Append-only audit log.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| invoice | FK(Invoice) | |
| user | FK(User) | nullable (null for system events) |
| action | enum | UPLOADED / EXTRACTION_COMPLETED / EXTRACTION_FAILED / FIELDS_EDITED / APPROVED / EDIT_REQUESTED / BOOKED / COMMENTED |
| comment | text | nullable |
| changes | JSON | nullable, field-level diffs for FIELDS_EDITED actions |
| created_at | datetime | |

The changes JSON for FIELDS_EDITED actions: {"total_amount": {"old": "1500.00", "new": "1650.00"}, "supplier_name": {"old": "Acme", "new": "Acme OY"}}

### Notification

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user | FK(User) | recipient |
| organization | FK(Org) | nullable |
| invoice | FK(Invoice) | nullable |
| type | enum | INVITE_RECEIVED / APPROVAL_NEEDED / EDIT_REQUESTED / INVOICE_APPROVED / INVOICE_BOOKED |
| title | string | display text |
| is_read | bool | default false |
| created_at | datetime | |

### Invoice Lifecycle

```
PROCESSING ──→ PENDING_REVIEW ──→ APPROVED ──→ BOOKED
    │               ↑                  │
    │               └── edit request ──┘
    │                   (round increments, approvals reset)
    ↓
EXTRACTION_FAILED ──→ PENDING_REVIEW
                      (accountant fills fields manually)
```

5 statuses: PROCESSING, EXTRACTION_FAILED, PENDING_REVIEW, APPROVED, BOOKED.

### Relationships

```
User ──< OrganizationMembership >── Organization
                                        │
                                    Supplier (per org)
                                        │
                                    Invoice ──→ Supplier (nullable FK)
                                   /   |   \
                                  /    |    \
                    InvoiceApproval  Activity  Notification
```

### Design choices
1. Extracted fields as typed columns, not JSON — enables filtering/querying
2. Confidence scores inside llm_raw_response JSON, not as separate columns — display-only concern
3. ERP config on Organization, not User — cleaner for multi-user orgs
4. Membership doubles as invite (PENDING status) — no separate invite table
5. Approval rounds tracked with a round integer — history preserved, not deleted on re-review
6. Single activity log table — all workflow history in one place
7. Supplier as normalized per-org entity, with denormalized copy on Invoice — canonical record for filtering, point-in-time data per invoice


## API design
/// to be created

## Tech stack

**Backend:**
- Django + Django REST Framework
- PostgreSQL — supports JSON fields, enums, partial unique constraints needed by the data model
- Celery + Redis — async task processing (LLM extraction after PDF upload, ERP export)

**Auth:**
- django-allauth — Google OAuth

**PDF / LLM:**
- pdfplumber or PyMuPDF — text extraction from PDFs
- Replicate API — LLM extraction calls

**File storage:**
- S3 (or compatible) + django-storages — PDF storage

**ERP integration:**
- Google Sheets API (google-api-python-client)
- QuickBooks REST API

**Frontend:**
- React / Next.js — separate app

