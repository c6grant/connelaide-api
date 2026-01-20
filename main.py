from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Transaction
from schemas import TransactionResponse

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
    }
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