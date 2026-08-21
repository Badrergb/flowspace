from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.db.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/overview")
def get_finance_overview(
    days: int = 30,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Fetch all transactions from Firestore
    txn_docs = (
        db.collection("users")
        .document(uid)
        .collection("transactions")
        .stream()
    )

    transactions = [doc.to_dict() for doc in txn_docs]

    total_spent = 0.0
    total_income = 0.0
    daily_spending = {}
    category_spending = {}

    for i in range(days):
        d = (end_date - timedelta(days=i)).date().isoformat()
        daily_spending[d] = 0.0

    for t in transactions:
        txn_date = t.get("date")
        if hasattr(txn_date, "date"):
            d = txn_date.date().isoformat()
        elif isinstance(txn_date, str):
            d = txn_date[:10]
        else:
            continue

        amount = float(t.get("amount", 0))
        txn_type = t.get("type", "")

        if txn_type == "expense":
            total_spent += amount
            if d in daily_spending:
                daily_spending[d] += amount
            cat_id = t.get("category_id")
            if cat_id:
                category_spending[cat_id] = category_spending.get(cat_id, 0.0) + amount
        elif txn_type == "income":
            total_income += amount

    sparkline_data = [daily_spending[k] for k in sorted(daily_spending.keys())]

    top_categories = [
        {"id": k, "name": k, "amount": v}
        for k, v in category_spending.items()
    ]
    top_categories.sort(key=lambda x: x["amount"], reverse=True)

    return {
        "total_spent": total_spent,
        "total_income": total_income,
        "sparkline_data": sparkline_data,
        "top_categories": top_categories[:5],
    }
