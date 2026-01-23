from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from database import Base

class Transaction(Base):
    """Model for storing financial transactions from Plaid"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False, index=True)
    account_id = Column(String(255), nullable=False, index=True)
    date = Column(String(50), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    pending = Column(Boolean, default=False)
    merchant_name = Column(String(255))
    plaid_generated_category = Column(String(255))
    connelaide_category = Column(String(300))
    edited_amount = Column(Float)
    note = Column(String(700))
    impacts_checking_balance = Column(String(20), default='review_required')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, name={self.name}, amount={self.amount})>"


class RefreshMetadata(Base):
    """Model for tracking when Plaid data was last fetched"""
    __tablename__ = "refresh_metadata"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # "plaid_transactions"
    last_refreshed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<RefreshMetadata(key={self.key}, last_refreshed_at={self.last_refreshed_at})>"


class ConnalaideCategory(Base):
    """Model for storing custom Connelaide categories"""
    __tablename__ = "connalaide_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ConnalaideCategory(id={self.id}, name={self.name})>"
