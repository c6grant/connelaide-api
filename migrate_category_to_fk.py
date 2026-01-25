"""
Migration script to convert connelaide_category from string to foreign key.

This script:
1. Adds the new connelaide_category_id column
2. Ensures all existing category strings exist in connalaide_categories
3. Maps existing string values to their category IDs
4. Adds a foreign key constraint

Run this script BEFORE deploying the updated API code.
"""

from sqlalchemy import text
from database import engine


def migrate():
    with engine.connect() as conn:
        # Step 1: Add new column
        print("Adding connelaide_category_id column...")
        conn.execute(text("""
            ALTER TABLE transactions
            ADD COLUMN IF NOT EXISTS connelaide_category_id INTEGER;
        """))
        conn.commit()

        # Step 2: Insert any missing categories from transactions
        print("Inserting missing categories...")
        conn.execute(text("""
            INSERT INTO connalaide_categories (name, created_at)
            SELECT DISTINCT t.connelaide_category, NOW()
            FROM transactions t
            WHERE t.connelaide_category IS NOT NULL
            AND t.connelaide_category NOT IN (SELECT name FROM connalaide_categories)
            ON CONFLICT (name) DO NOTHING;
        """))
        conn.commit()

        # Step 3: Map strings to IDs
        print("Mapping category strings to IDs...")
        result = conn.execute(text("""
            UPDATE transactions t
            SET connelaide_category_id = c.id
            FROM connalaide_categories c
            WHERE t.connelaide_category = c.name
            AND t.connelaide_category_id IS NULL;
        """))
        conn.commit()
        print(f"  Updated {result.rowcount} transactions with category IDs")

        # Step 4: Add foreign key constraint (check if it doesn't already exist)
        print("Adding foreign key constraint...")
        # Check if constraint exists first
        constraint_check = conn.execute(text("""
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_transactions_category';
        """))
        if constraint_check.fetchone() is None:
            conn.execute(text("""
                ALTER TABLE transactions
                ADD CONSTRAINT fk_transactions_category
                FOREIGN KEY (connelaide_category_id)
                REFERENCES connalaide_categories(id);
            """))
            conn.commit()
            print("  Foreign key constraint added")
        else:
            print("  Foreign key constraint already exists, skipping")

        print("\nMigration complete!")
        print("\nNext steps:")
        print("1. Deploy the updated API backend")
        print("2. Deploy the updated Lambda")
        print("3. Deploy the updated frontend")
        print("4. Later: Remove the old connelaide_category string column")


def rollback():
    """Rollback the migration if needed."""
    with engine.connect() as conn:
        print("Rolling back migration...")

        # Remove foreign key constraint
        conn.execute(text("""
            ALTER TABLE transactions
            DROP CONSTRAINT IF EXISTS fk_transactions_category;
        """))
        conn.commit()

        # Remove the new column
        conn.execute(text("""
            ALTER TABLE transactions
            DROP COLUMN IF EXISTS connelaide_category_id;
        """))
        conn.commit()

        print("Rollback complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback()
    else:
        migrate()
