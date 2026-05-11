# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

MyDinDin is a Django REST Framework backend for personal finance management. It supports recurring transactions, installment plans, and credit card invoice tracking. Authentication is JWT (Bearer) over a custom `accounts.User` model that uses email instead of username. Periodic automation (recurring transactions, installment generation, overdue status, invoice creation) runs through Celery Beat against a Redis broker.

The project is in Brazilian Portuguese — model verbose names, docstrings, comments, and ad-hoc docs (`*.md` at the root) are all in pt-BR. Match that tone when writing new code or docs.

## Environment

- Python 3.12 in a pyenv virtualenv named `mydindin`. Activate with `eval "$(pyenv init -)" && pyenv shell mydindin` before running any commands.
- PostgreSQL is the database (see `config/settings.py`); `.env` holds credentials via `python-decouple`. The committed `.env` only has DB vars — other settings fall back to defaults in `settings.py`.
- Redis broker on `redis://localhost:6379/0` is required for Celery worker/beat.

## Common commands

```bash
# Setup
./init_project.sh                        # full bootstrap (deps + migrate + load_default_categories + optional superuser)
python manage.py migrate
python manage.py load_default_categories  # seeds default Category rows (is_default=True, user=NULL)
python manage.py createsuperuser          # prompts for email (USERNAME_FIELD), first_name, last_name, password

# Run
python manage.py runserver
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Shell (django-extensions shell_plus with IPython, auto-imports all models)
python manage.py shell_plus

# Tests
python manage.py test                            # all Django TestCase tests
python manage.py test finances                   # one app
python manage.py test finances.tests.ClassName   # one class
python manage.py test finances.tests.ClassName.test_method  # one test

# Standalone test scripts at repo root (NOT Django TestCase — they call django.setup() and mutate the real DB)
python test_cascade_delete.py
python test_installment_sync.py
python test_installment_transactions.py
python test_invoices.py
python test_signals_bulk.py
python populate_data.py                          # seeds demo data into the configured DB
```

## Architecture

### Apps

- `accounts/` — custom `User` model (email as `USERNAME_FIELD`), `EmailBackend` for auth, JWT register/login/logout/profile views. Mounted at `/api/auth/`.
- `finances/` — domain models, services, signals, Celery tasks, DRF viewsets. Mounted at `/api/`.
- `config/` — Django settings, root URLConf, Celery app, ASGI/WSGI entrypoints.

### Domain model relationships (`finances/models.py`)

```
User ─┬─ Category (is_default=True with user=NULL are system-wide; user-owned otherwise)
      ├─ Transaction ──── Category (PROTECT)
      │     │
      │     ├─ CreditCard (SET_NULL, optional)
      │     ├─ CreditCardInvoice (SET_NULL, optional)  ← auto-linked via signals
      │     └─ Installment (reverse OneToOne — `transaction.installment`)
      │
      ├─ RecurringTemplate          (Celery materializes monthly Transactions from these)
      ├─ InstallmentPlan ── Installment (1..N, created in `InstallmentPlan._create_installments`)
      │     └─ each Installment owns a Transaction (OneToOne, cascade)
      └─ CreditCard ── CreditCardInvoice (one per `reference_month`)
```

Key invariants enforced in `Model.save()`/`clean()`:
- `Category.type` must match the `type` of any `Transaction`, `RecurringTemplate`, or `InstallmentPlan` referencing it.
- `Transaction.save()` propagates `status` to its linked `Installment` (try/except on the reverse OneToOne).
- `CreditCard.due_day` must be > `closing_day`.
- `CreditCardInvoice.paid_amount <= total_amount`.
- `InstallmentPlan.save()` on first save calls `_create_installments()` inside an atomic block. This creates each `Installment` and its `Transaction` **individually** (not bulk) so that `post_save` signals fire — bulk_create would skip the invoice-linking signals. Do not "optimize" this loop to `bulk_create`.

### Signals (`finances/signals.py`)

- `post_save` on `Transaction`: when it has a `credit_card` but no `invoice`, `InvoiceService.link_transaction_to_invoice` finds/creates the right `CreditCardInvoice` based on `closing_day` and links it, then recomputes the invoice total.
- `post_save` on `Installment`: same flow for installments whose plan has a `credit_card`.
- `pre_delete` on `Installment`: deletes the linked `Transaction` so that deleting an `InstallmentPlan` cascades cleanly through `Installment → Transaction`.

Signals are wired in `FinancesConfig.ready()`. Anything that creates Transactions/Installments programmatically (services, admin, tests) must go through `.save()` / `.objects.create()` to trigger this — never `bulk_create`.

### Services (`finances/services/`)

Business logic lives here, not in views:

- `recurring_service.RecurringService` — walks `RecurringTemplate`s and materializes `Transaction`s for the current month if not already generated. Tracks `last_generated_date` to avoid duplicates.
- `installment_service.InstallmentService` — generates transactions for upcoming installments, marks overdue ones.
- `invoice_service.InvoiceService` — computes which `reference_month` a transaction belongs to (transactions on/before `closing_day` go to the current month, after go to the next), creates/looks up the matching `CreditCardInvoice`, and recomputes totals via `get_declared_expenses()`.

Celery tasks in `finances/tasks.py` are thin wrappers that delegate to these services. Beat schedule lives in `config/celery.py`:

| Time  | Task                                       | What it does                                       |
|-------|--------------------------------------------|----------------------------------------------------|
| 00:01 | `finances.create_recurring_transactions`   | RecurringTemplate → Transaction                    |
| 00:05 | `finances.create_installment_transactions` | Installment → Transaction                          |
| 00:10 | `finances.update_overdue_status`           | pending past `due_date` → overdue                  |
| 00:15 | `finances.create_credit_card_invoices`     | Materializes invoices once `closing_date` passed   |
| 00:20 | `finances.update_overdue_invoices`         | Invoice overdue status                             |
| 03:00 day 1 | `finances.cleanup_old_data`          | Monthly placeholder                                |

### API surface (`finances/urls.py`)

DRF `DefaultRouter` exposes ViewSets at `/api/{categories,transactions,recurring-templates,installment-plans,installments,credit-cards,invoices}/`. All require JWT auth (`DEFAULT_PERMISSION_CLASSES = IsAuthenticated`). Most ViewSets scope `get_queryset()` to `request.user` and override `perform_create` to inject the user — preserve that pattern when adding endpoints.

Custom actions follow the `@action(detail=False/True)` pattern: `transactions/by_period/`, `transactions/by_month/`, `transactions/summary/`, `transactions/by_category/`, `recurring-templates/{id}/generate_now/`, etc. See `finances/views.py` for the full list.

DRF defaults from `config/settings.py`: pagination = 20, date format `%d/%m/%Y`, datetime `%d/%m/%Y %H:%M:%S`.

### JWT auth

`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME = 10 days`, refresh = 30 days, `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`. Auth header is `Authorization: Bearer <token>`. Login uses email + password (no `username` field anywhere).

## Conventions worth knowing

- **Language**: model fields, verbose names, docstrings, and inline comments are in Brazilian Portuguese. Keep new code consistent.
- **Decimal money**: amounts are `DecimalField(max_digits=12, decimal_places=2)` with `MinValueValidator(Decimal('0.01'))`. Always operate on `Decimal`, not float.
- **Timezone**: `TIME_ZONE = 'America/Sao_Paulo'`, `USE_TZ = True`. `CELERY_TIMEZONE` matches. Beat crontabs are in São Paulo local time.
- **Service-first**: new domain logic (invoice math, installment generation, recurrence) goes into `finances/services/`, not into views or models. Signals and tasks are thin.
- **Don't bypass signals**: `bulk_create`/`update` skip `post_save` and break invoice linking — see `_create_installments` comment above.

## Reference docs at the repo root

Many `*.md` files at the repo root (e.g. `MOTOR_RECORRENCIA.md`, `FATURAS_AUTOMATICAS.md`, `IMPLEMENTACAO_FATURAS.md`, `CARTOES_CREDITO_API.md`, `API_EXAMPLES.md`) document specific subsystems in depth. They were written during feature implementation and are pt-BR. Treat them as design notes — if behavior in code disagrees with a doc, trust the code and update the doc.
