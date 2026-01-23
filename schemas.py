from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    transaction_id: str
    account_name: str
    account_id: str
    date: str
    name: str
    amount: float
    pending: bool
    merchant_name: Optional[str] = None
    plaid_generated_category: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    account_name: str
    account_id: str
    date: str
    description: str = Field(validation_alias="name")
    amount: float
    pending: bool
    merchant_name: Optional[str] = None
    category: Optional[str] = Field(default=None, validation_alias="plaid_generated_category")
    connelaide_category: Optional[str] = None
    edited_amount: Optional[float] = None
    note: Optional[str] = None
    impacts_checking_balance: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RefreshStatusResponse(BaseModel):
    """Response for refresh status endpoint"""
    last_refreshed_at: Optional[datetime] = None


class RefreshResponse(BaseModel):
    """Response for refresh endpoint"""
    success: bool
    message: str
    transactions_fetched: Optional[int] = None
    last_refreshed_at: Optional[datetime] = None
