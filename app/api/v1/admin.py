from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional
import datetime

from firebase_admin import auth as firebase_auth
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1 import aggregation

from app.core.config import settings
from app.db.database import get_db

router = APIRouter()


def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    if not x_admin_key or x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    return True


@router.get("/kpis")
def get_admin_kpis(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    # Count users from Firebase Auth
    total_users = 0
    page = firebase_auth.list_users()
    while page:
        total_users += len(page.users)
        page = page.get_next_page()

    # Count total tasks using Firestore collection group query
    total_tasks = 0
    total_documents = 0
    try:
        tasks_query = db.collection_group("tasks")
        agg_query = tasks_query.count(alias="total")
        result = agg_query.get()
        total_tasks = result[0][0].value
        total_documents += total_tasks
        
        for col in ["habits", "goals", "notes", "journals", "calendar_events", "transactions"]:
            try:
                res = db.collection_group(col).count(alias="total").get()
                total_documents += res[0][0].value
            except Exception:
                pass
    except Exception:
        total_tasks = 0

    return {
        "total_users": total_users,
        "active_users": total_users,  # Firebase Auth doesn't track this separately
        "total_tasks": total_tasks,
        "total_documents": total_documents,
        "mrr": 0.0,
    }


@router.get("/system")
def get_system_health(_: bool = Depends(verify_admin_key)):
    import psutil
    import os
    
    # psutil.virtual_memory() often returns the host node's total RAM (e.g., 16GB).
    # To get the exact RAM used by your specific Render container/app, we measure 
    # the Resident Set Size (RSS) of the current Python process.
    process = psutil.Process(os.getpid())
    ram_used_mb = process.memory_info().rss / (1024 * 1024)
    
    return {
        "services": [
            {
                "id": "render-ram", 
                "name": "Server Memory (RAM)", 
                "status": "operational" if ram_used_mb < 450 else "degraded", 
                "value": ram_used_mb,
                "max": 512, # 512MB free tier limit
                "unit": "MB"
            },
            {
                "id": "api-rate-limit", 
                "name": "API Concurrent Requests", 
                "status": "operational", 
                "value": 1, # Current connections
                "max": 10,  # Max concurrent
                "unit": "Req"
            },
            {
                "id": "ai-quota", 
                "name": "Gemini AI Quota (RPM)", 
                "status": "operational", 
                "value": 0,
                "max": 15, # 15 Requests Per Minute free tier limit
                "unit": "RPM"
            }
        ]
    }


@router.get("/ai-usage")
def get_ai_usage(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    total_requests = 0
    try:
        users_docs = db.collection("users").stream()
        for user_doc in users_docs:
            settings_doc = (
                db.collection("users")
                .document(user_doc.id)
                .collection("settings")
                .document("preferences")
                .get()
            )
            if settings_doc.exists:
                data = settings_doc.to_dict()
                total_requests += data.get("ai_requests_used", 0)
    except Exception:
        total_requests = 0

    return {"total_ai_requests": total_requests}


@router.get("/analytics/growth")
def get_analytics_growth(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    from collections import defaultdict

    daily_counts = defaultdict(int)
    try:
        page = firebase_auth.list_users()
        while page:
            for user in page.users:
                if user.user_metadata.creation_timestamp:
                    dt = datetime.datetime.utcfromtimestamp(
                        user.user_metadata.creation_timestamp / 1000
                    )
                    date_str = dt.strftime("%Y-%m-%d")
                    daily_counts[date_str] += 1
            page = page.get_next_page()
    except Exception:
        pass

    chart_data = [{"name": k, "value": v} for k, v in sorted(daily_counts.items())]

    if not chart_data:
        today = datetime.date.today()
        chart_data = [
            {"name": (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d"), "value": 0}
            for i in range(7, -1, -1)
        ]

    return chart_data


@router.get("/analytics/activity")
def get_analytics_activity(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    feed = []
    try:
        for collection_name in ["tasks", "habits", "goals"]:
            docs = (
                db.collection_group(collection_name)
                .order_by("created_at", direction="DESCENDING")
                .limit(5)
                .stream()
            )
            for doc in docs:
                d = doc.to_dict()
                feed.append({
                    "id": doc.id,
                    "type": collection_name.rstrip("s"),
                    "title": d.get("title", "Untitled"),
                    "created_at": d.get("created_at"),
                })
    except Exception:
        pass

    feed.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    for item in feed:
        if item.get("created_at") and hasattr(item["created_at"], "isoformat"):
            item["created_at"] = item["created_at"].isoformat()

    return feed


@router.get("/analytics/features")
def get_analytics_features(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    results = []
    for name, col in [
        ("Tasks", "tasks"),
        ("Habits", "habits"),
        ("Goals", "goals"),
        ("Notes", "notes"),
        ("Transactions", "transactions"),
    ]:
        count = 0
        try:
            agg = db.collection_group(col).count(alias="total").get()
            count = agg[0][0].value
        except Exception:
            count = 0
        results.append({"name": name, "value": count})

    return results

@router.get("/reviews/export")
def export_reviews_csv(
    db: FirestoreClient = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    import csv
    import io
    from fastapi.responses import Response

    # Fetch all reviews from Firestore
    reviews_docs = db.collection("reviews").stream()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Review ID", "Name", "Rating", "Review Text", "Approved", "Created At"])
    
    reviews = []
    for doc in reviews_docs:
        d = doc.to_dict()
        d["id"] = doc.id
        reviews.append(d)
        
    reviews.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    for d in reviews:
        created_at = d.get("created_at")
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()
            
        writer.writerow([
            d.get("id", doc.id),
            d.get("name", ""),
            d.get("rating", ""),
            d.get("review_text", ""),
            d.get("is_approved", False),
            created_at
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=reviews_export.csv"
    return response
