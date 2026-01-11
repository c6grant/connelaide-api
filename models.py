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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, name={self.name}, amount={self.amount})>"
