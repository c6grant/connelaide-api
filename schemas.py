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
    connelaide_category_id: Optional[int] = None
    connelaide_category: Optional[str] = None  # Populated from joined relationship
    edited_amount: Optional[float] = None
    note: Optional[str] = None
    impacts_checking_balance: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TransactionUpdateRequest(BaseModel):
    connelaide_category_id: Optional[int] = None
    edited_amount: Optional[float] = None
    note: Optional[str] = None
    impacts_checking_balance: Optional[str] = None


class RefreshStatusResponse(BaseModel):
    """Response for refresh status endpoint"""
    last_refreshed_at: Optional[datetime] = None


class RefreshResponse(BaseModel):
    """Response for refresh endpoint"""
    success: bool
    message: str
    transactions_fetched: Optional[int] = None
    last_refreshed_at: Optional[datetime] = None


class ConnalaideCategoryBase(BaseModel):
    """Base schema for Connelaide Category"""
    name: str
    target_budget: Optional[float] = None


class ConnalaideCategoryCreate(ConnalaideCategoryBase):
    """Schema for creating a new category"""
    pass


class ConnalaideCategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = None
    target_budget: Optional[float] = None


class ConnalaideCategoryResponse(BaseModel):
    """Response schema for category"""
    id: int
    name: str
    target_budget: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Projected Expense Schemas
# ============================================

class ProjectedExpenseBase(BaseModel):
    """Base schema for Projected Expense"""
    name: str
    amount: float
    date: str
    connelaide_category_id: Optional[int] = None
    note: Optional[str] = None


class ProjectedExpenseCreate(ProjectedExpenseBase):
    """Schema for creating a new projected expense"""
    pass


class ProjectedExpenseUpdate(BaseModel):
    """Schema for updating a projected expense"""
    name: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    connelaide_category_id: Optional[int] = None
    note: Optional[str] = None
    is_struck_out: Optional[bool] = None
    merged_transaction_id: Optional[int] = None


class ProjectedExpenseResponse(BaseModel):
    """Response schema for projected expense"""
    id: int
    name: str
    amount: float
    date: str
    connelaide_category_id: Optional[int] = None
    connelaide_category: Optional[str] = None  # Populated from join
    note: Optional[str] = None
    is_struck_out: bool = False
    merged_transaction_id: Optional[int] = None
    recurring_expense_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Pay Period Schemas
# ============================================

class PayPeriodBase(BaseModel):
    """Base schema for PayPeriod"""
    start_date: str
    end_date: str
    checking_budget: Optional[float] = None


class PayPeriodCreate(PayPeriodBase):
    """Schema for creating a new pay period"""
    pass


class PayPeriodUpdate(BaseModel):
    """Schema for updating a pay period"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    checking_budget: Optional[float] = None


class PayPeriodResponse(BaseModel):
    """Response schema for pay period"""
    id: int
    start_date: str
    end_date: str
    checking_budget: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Recurring Expense Schemas
# ============================================

class RecurringExpenseBase(BaseModel):
    name: str
    amount: float
    frequency: str  # 'monthly' or 'yearly'
    day_of_month: int  # 1-31
    month_of_year: Optional[int] = None  # 1-12, required if frequency='yearly'
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None
    connelaide_category_id: Optional[int] = None
    note: Optional[str] = None

class RecurringExpenseCreate(RecurringExpenseBase):
    pass

class RecurringExpenseUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    connelaide_category_id: Optional[int] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None

class RecurringExpenseResponse(BaseModel):
    id: int
    name: str
    amount: float
    frequency: str
    day_of_month: int
    month_of_year: Optional[int] = None
    start_date: str
    end_date: Optional[str] = None
    connelaide_category_id: Optional[int] = None
    connelaide_category: Optional[str] = None
    note: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
