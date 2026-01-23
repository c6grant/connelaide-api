import json
import os
from datetime import datetime, timedelta, timezone
from typing import List

import boto3
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Transaction, RefreshMetadata, ConnalaideCategory
from schemas import (
    TransactionResponse, RefreshStatusResponse, RefreshResponse, TransactionUpdateRequest,
    ConnalaideCategoryCreate, ConnalaideCategoryUpdate, ConnalaideCategoryResponse
)

app = FastAPI(
    title="Connelaide API",
    description="Backend API for Connelaide",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://connelaide.com",
        "http://localhost:4200"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Connelaide API is running"}

@app.get("/health")
async def health():
    """Health check endpoint for ALB"""
    return {"status": "healthy"}

@app.get("/api/v1/example")
async def example_endpoint():
    """Example API endpoint - Public"""
    return {"message": "This is an example endpoint.. howdy", "data": {"key": "value"}}

@app.get("/api/v1/protected")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    """Protected endpoint - Requires authentication"""
    return {
        "message": "This is a protected endpoint",
        "user": current_user
    }

@app.get("/api/v1/user/profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's profile"""
    return {
        "profile": current_user,
        "message": "Successfully retrieved user profile"
    }

@app.get("/api/v1/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions within a date range (inclusive)"""
    transactions = db.query(Transaction)\
        .filter(Transaction.date >= start_date)\
        .filter(Transaction.date <= end_date)\
        .order_by(Transaction.date.desc())\
        .all()
    return transactions

@app.get("/api/v1/transactions/first", response_model=TransactionResponse)
async def get_first_transaction(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the first transaction from the database - Protected endpoint"""
    transaction = db.query(Transaction).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found"
        )

    return transaction


@app.get("/api/v1/transactions/refresh-status", response_model=RefreshStatusResponse)
async def get_refresh_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the last refresh timestamp for transactions"""
    metadata = db.query(RefreshMetadata).filter(
        RefreshMetadata.key == "plaid_transactions"
    ).first()

    return RefreshStatusResponse(
        last_refreshed_at=metadata.last_refreshed_at if metadata else None
    )


@app.post("/api/v1/transactions/refresh", response_model=RefreshResponse)
async def refresh_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invoke Lambda to fetch new transactions from Plaid"""
    # Get last refresh date
    metadata = db.query(RefreshMetadata).filter(
        RefreshMetadata.key == "plaid_transactions"
    ).first()

    now = datetime.now(timezone.utc)

    if metadata and metadata.last_refreshed_at:
        # Start from 14 days before last refresh to catch late-clearing pending transactions,
        # backfilled transactions, and date corrections from Plaid
        start_date = (metadata.last_refreshed_at - timedelta(days=14)).strftime("%Y-%m-%d")
    else:
        # First refresh: go back 30 days
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    end_date = now.strftime("%Y-%m-%d")

    # Invoke Lambda
    try:
        lambda_client = boto3.client(
            "lambda",
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

        payload = {
            "start_date": start_date,
            "end_date": end_date
        }

        response = lambda_client.invoke(
            FunctionName="plaid-fetcher-v2-production",
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        # Parse Lambda response
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        if response.get("FunctionError"):
            return RefreshResponse(
                success=False,
                message=f"Lambda error: {response_payload.get('errorMessage', 'Unknown error')}"
            )

        # Check if Lambda returned a body (API Gateway format)
        if "body" in response_payload:
            body = json.loads(response_payload["body"]) if isinstance(response_payload["body"], str) else response_payload["body"]
            transactions_count = body.get("transactions_count", 0)
        else:
            transactions_count = response_payload.get("transactions_count", 0)

        # Update refresh metadata
        if metadata:
            metadata.last_refreshed_at = now
        else:
            metadata = RefreshMetadata(
                key="plaid_transactions",
                last_refreshed_at=now
            )
            db.add(metadata)

        db.commit()

        return RefreshResponse(
            success=True,
            message=f"Successfully refreshed transactions",
            transactions_fetched=transactions_count,
            last_refreshed_at=now
        )

    except Exception as e:
        return RefreshResponse(
            success=False,
            message=f"Failed to refresh transactions: {str(e)}"
        )


@app.patch("/api/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    updates: TransactionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user-editable fields on a transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


# ============================================
# Connelaide Categories Endpoints
# ============================================

@app.get("/api/v1/connalaide-categories", response_model=List[ConnalaideCategoryResponse])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all Connelaide categories"""
    categories = db.query(ConnalaideCategory).order_by(ConnalaideCategory.name).all()
    return categories


@app.get("/api/v1/connalaide-categories/{category_id}", response_model=ConnalaideCategoryResponse)
async def get_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single category by ID"""
    category = db.query(ConnalaideCategory).filter(ConnalaideCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.post("/api/v1/connalaide-categories", response_model=ConnalaideCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: ConnalaideCategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # Check if category with same name exists
    existing = db.query(ConnalaideCategory).filter(ConnalaideCategory.name == category_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    category = ConnalaideCategory(name=category_data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@app.patch("/api/v1/connalaide-categories/{category_id}", response_model=ConnalaideCategoryResponse)
async def update_category(
    category_id: int,
    updates: ConnalaideCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a category"""
    category = db.query(ConnalaideCategory).filter(ConnalaideCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = updates.model_dump(exclude_unset=True)

    # Check for duplicate name if name is being updated
    if "name" in update_data:
        existing = db.query(ConnalaideCategory).filter(
            ConnalaideCategory.name == update_data["name"],
            ConnalaideCategory.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@app.delete("/api/v1/connalaide-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a category"""
    category = db.query(ConnalaideCategory).filter(ConnalaideCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return None