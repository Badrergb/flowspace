from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.entities import Transaction, Category

router = APIRouter()

@router.get("/overview")
def get_finance_overview(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get transactions in range
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    total_spent = sum([float(t.amount) for t in transactions if t.type == 'expense'])
    total_income = sum([float(t.amount) for t in transactions if t.type == 'income'])

    # Aggregate by date for sparkline
    daily_spending = {}
    for i in range(days):
        d = (end_date - timedelta(days=i)).date()
        daily_spending[d] = 0.0
        
    for t in transactions:
        if t.type == 'expense':
            d = t.date.date()
            if d in daily_spending:
                daily_spending[d] += float(t.amount)

    sparkline_data = [daily_spending[k] for k in sorted(daily_spending.keys())]

    # Aggregate by category
    category_spending = {}
    for t in transactions:
        if t.type == 'expense' and t.category_id:
            cat_id = str(t.category_id)
            category_spending[cat_id] = category_spending.get(cat_id, 0.0) + float(t.amount)

    # Fetch categories
    categories = db.query(Category).filter(
        Category.id.in_(list(category_spending.keys()))
    ).all()
    
    cat_map = {str(c.id): c.name for c in categories}
    
    top_categories = [
        {"id": k, "name": cat_map.get(k, "Unknown"), "amount": v}
        for k, v in category_spending.items()
    ]
    top_categories.sort(key=lambda x: x['amount'], reverse=True)

    return {
        "total_spent": total_spent,
        "total_income": total_income,
        "sparkline_data": sparkline_data,
        "top_categories": top_categories[:5]
    }
