"""
Seed script for local development.
Populates the database with dummy data. Idempotent — safe to run multiple times.
"""
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Load local env before any database imports
load_dotenv(".env.local")

from database import SessionLocal
from models import (
    ConnalaideCategory,
    PayPeriod,
    ProjectedExpense,
    RecurringExpense,
    RefreshMetadata,
    Transaction,
)

CATEGORIES = [
    {"name": "Groceries", "target_budget": 400.0},
    {"name": "Rent", "target_budget": 1500.0},
    {"name": "Utilities", "target_budget": 200.0},
    {"name": "Entertainment", "target_budget": 150.0},
    {"name": "Transportation", "target_budget": 100.0},
]

def _today():
    return datetime.now().date()


def seed():
    db = SessionLocal()
    try:
        # --- Categories ---
        existing_cats = {c.name for c in db.query(ConnalaideCategory).all()}
        cat_map: dict[str, int] = {}
        for cat in CATEGORIES:
            if cat["name"] not in existing_cats:
                obj = ConnalaideCategory(**cat)
                db.add(obj)
                db.flush()
                cat_map[obj.name] = obj.id
                print(f"  + Category: {cat['name']}")
            else:
                obj = db.query(ConnalaideCategory).filter_by(name=cat["name"]).first()
                cat_map[obj.name] = obj.id

        # --- Transactions ---
        if db.query(Transaction).count() == 0:
            today = _today()
            txns = [
                # (name, amount, category, days_ago, impacts_checking_balance)
                ("Whole Foods", -85.32, "Groceries", 1, "true"),
                ("Kroger", -62.18, "Groceries", 3, "true"),
                ("Trader Joe's", -47.90, "Groceries", 7, "true"),
                ("Aldi", -33.55, "Groceries", 12, "review_required"),
                ("Costco", -128.40, "Groceries", 18, "true"),
                ("Rent Payment", -1500.00, "Rent", 1, "true"),
                ("Electric Company", -95.00, "Utilities", 5, "true"),
                ("Water Bill", -45.00, "Utilities", 10, "true"),
                ("Internet Service", -59.99, "Utilities", 8, "true"),
                ("Netflix", -15.99, "Entertainment", 2, "false"),
                ("Movie Theater", -24.00, "Entertainment", 14, "true"),
                ("Concert Tickets", -75.00, "Entertainment", 20, "review_required"),
                ("Spotify", -10.99, "Entertainment", 2, "false"),
                ("Gas Station", -42.50, "Transportation", 4, "true"),
                ("Uber Ride", -18.75, "Transportation", 9, "true"),
                ("Parking Garage", -12.00, "Transportation", 15, "true"),
                ("Oil Change", -55.00, "Transportation", 22, "true"),
            ]
            for name, amount, cat_name, days_ago, impacts in txns:
                txn_date = today - timedelta(days=days_ago)
                db.add(Transaction(
                    transaction_id=f"seed-{uuid.uuid4().hex[:12]}",
                    account_name="Checking",
                    account_id="seed-checking-001",
                    date=txn_date.isoformat(),
                    name=name,
                    amount=amount,
                    pending=False,
                    merchant_name=name,
                    plaid_generated_category=cat_name,
                    connelaide_category_id=cat_map.get(cat_name),
                    impacts_checking_balance=impacts,
                ))
            print(f"  + {len(txns)} transactions")
        else:
            print("  ~ Transactions already exist, skipping")

        # --- Pay Period ---
        if db.query(PayPeriod).count() == 0:
            today = _today()
            # Current bi-weekly pay period: starts on most recent 1st or 15th
            if today.day >= 15:
                start = today.replace(day=15)
                end_month = today.month + 1 if today.month < 12 else 1
                end_year = today.year if today.month < 12 else today.year + 1
                end = today.replace(year=end_year, month=end_month, day=1) - timedelta(days=1)
            else:
                start = today.replace(day=1)
                end = today.replace(day=14)
            db.add(PayPeriod(
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                checking_budget=2000.0,
            ))
            print(f"  + Pay period: {start} to {end}")
        else:
            print("  ~ Pay periods already exist, skipping")

        # --- Recurring Expenses ---
        if db.query(RecurringExpense).count() == 0:
            today = _today()
            recurrings = [
                {"name": "Rent", "amount": 1500.0, "frequency": "monthly", "day_of_month": 1,
                 "start_date": (today.replace(day=1) - timedelta(days=60)).isoformat(),
                 "connelaide_category_id": cat_map.get("Rent"), "is_active": True},
                {"name": "Netflix", "amount": 15.99, "frequency": "monthly", "day_of_month": 2,
                 "start_date": (today.replace(day=1) - timedelta(days=90)).isoformat(),
                 "connelaide_category_id": cat_map.get("Entertainment"), "is_active": True},
                {"name": "Internet", "amount": 59.99, "frequency": "monthly", "day_of_month": 8,
                 "start_date": (today.replace(day=1) - timedelta(days=120)).isoformat(),
                 "connelaide_category_id": cat_map.get("Utilities"), "is_active": True},
            ]
            for rec in recurrings:
                db.add(RecurringExpense(**rec))
            print(f"  + {len(recurrings)} recurring expenses")
        else:
            print("  ~ Recurring expenses already exist, skipping")

        # --- Projected Expenses ---
        if db.query(ProjectedExpense).count() == 0:
            today = _today()
            projected = [
                {"name": "Car Insurance", "amount": 120.0,
                 "date": (today + timedelta(days=5)).isoformat(),
                 "connelaide_category_id": cat_map.get("Transportation")},
                {"name": "Dentist Appointment", "amount": 80.0,
                 "date": (today + timedelta(days=10)).isoformat(),
                 "note": "Co-pay after insurance"},
                {"name": "Grocery Restock", "amount": 100.0,
                 "date": (today + timedelta(days=3)).isoformat(),
                 "connelaide_category_id": cat_map.get("Groceries")},
            ]
            for proj in projected:
                db.add(ProjectedExpense(**proj))
            print(f"  + {len(projected)} projected expenses")
        else:
            print("  ~ Projected expenses already exist, skipping")

        # --- Refresh Metadata ---
        if db.query(RefreshMetadata).filter_by(key="plaid_transactions").count() == 0:
            db.add(RefreshMetadata(
                key="plaid_transactions",
                last_refreshed_at=datetime.now(),
            ))
            print("  + Refresh metadata entry")
        else:
            print("  ~ Refresh metadata already exists, skipping")

        db.commit()
        print("Seed complete!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
