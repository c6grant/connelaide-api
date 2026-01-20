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
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
