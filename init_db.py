"""
Database initialization script.
Run this to create all tables in your PostgreSQL database.
"""
from database import engine, Base
from models import Transaction, RefreshMetadata, ConnalaideCategory, PayPeriod, ProjectedExpense, RecurringExpense

def init_db():
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
