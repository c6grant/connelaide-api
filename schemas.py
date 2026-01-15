from pydantic import BaseModel, ConfigDict
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

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
