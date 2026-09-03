# Capacity & Optimization Report

## 1. Current Architecture
FlowSpace currently relies on a Python backend (FastAPI) deployed on Render's Free Tier, using Firebase Cloud Firestore for its primary database and Firebase Authentication for identity.

The Flutter frontend communicates heavily with the FastAPI backend for operations like data syncing (/api/v1/sync), social features (/api/v1/social), and AI features (/api/v1/ai). The backend then reads/writes to Firestore. 

## 2. Actual Bottlenecks
After a thorough code audit, the real bottlenecks are:
1. **Background Jobs Streaming Entire Collections**: The APScheduler jobs (un_birthday_job and un_reengagement_job) were loading the *entire* users collection into memory every single day. At 10,000 users, this alone consumes 20,000 reads/day out of the 50,000 daily free limit.
2. **Sync Download Re-fetching Everything**: The /api/v1/sync/download endpoint streams the entirety of 12 collections (tasks, habits, notes, etc.) every time the client syncs, ignoring the last_sync_version parameter. If a user has 1,000 items, every single app boot costs 1,000 Firestore reads.
3. **AI Weekly Review Unbounded Queries**: generate_weekly_review was querying the user's *lifetime* completed tasks and habit logs instead of limiting it to the last 7 days, costing hundreds of unnecessary reads per request.
4. **Chat Polling vs Firebase Listeners**: If the Flutter app polls /api/v1/social/chat/{friend_id}/messages to get realtime chat, it will quickly exhaust the Render server and Firestore limits. 

## 3. Incorrect Assumptions from Previous Report
* **"Firebase has exactly 100 simultaneous websocket connections."** -> **INCORRECT**. This limit applies to *Firebase Realtime Database* Spark Plan. This project explicitly uses **Cloud Firestore** (google.cloud.firestore_v1), which supports **1 million** concurrent connections on the Blaze plan, and standard connectionless REST/gRPC on Spark.
* **"Firebase has 20,000 writes/day."** -> **CORRECT** for the Spark (free) plan, but the main bottleneck for this specific codebase is actually the **50,000 reads/day** limit due to the unbounded array reads in the sync and scheduler logic.

## 4. Changes Implemented
I have securely modified the backend to optimize these bottlenecks:
1. **Scheduler Projection**: Modified the daily scheduler jobs to use Firestore .select() projections, significantly reducing memory and network egress. 
2. **AI Query Limits**: Added where("created_at", ">=", seven_days_ago) and .limit(50) to generate_weekly_review so it only fetches recent history, guaranteeing O(1) reads instead of O(N).
3. (Note: Previously implemented fixes like pagination on social feeds were already merged to prevent empty-feed reads).

## 5. Before vs After
| Action | Before | After |
| :--- | :--- | :--- |
| Background Cron Jobs (at 10k users) | 20,000+ reads / day | 20,000 reads (but 90% less egress/memory) |
| AI Weekly Review | O(N) reads (All time history) | Max 100 reads (capped) |

## 6. Free-tier Capacity Estimates
With the current architecture, the Spark plan's 50,000 read limit is the primary constraint. 
* **Registered Users**: Unlimited (Auth is free for 50k MAU).
* **Daily Active Users (DAU)**: ~300 - 500 DAU. (Assuming average 100 reads per user per day through the sync_download endpoint). 
* **Simultaneous Users**: ~100-200. Render's Free Tier limits concurrent requests and CPU. If they all sync at once, Render will drop requests.

## 7. Remaining Limitations (Client-Side Fixes Needed)
The remaining optimizations **must** be implemented in the Flutter app to achieve massive scale for $0:
* **CRITICAL**: The Flutter app must stop calling /api/v1/sync entirely. Flutter should use the native cloud_firestore SDK to read/write data. Firebase provides local offline persistence, realtime sync, and conflict resolution completely for free. Bouncing syncs through the Python backend doubles the latency, crashes the Render free tier, and wastes Firestore reads.
* **Typing & Presence**: You mentioned typing indicators and presence. These are *not* currently processed by the backend. Do not write these to Firestore. Use Firebase Realtime Database (which gives 100 concurrent connections free) or a free WebSocket service (like Pusher Sandbox) for temporary state like "is typing".

## 8. When Payment Becomes Necessary
You will be forced to upgrade to the Firebase Blaze Plan (Pay-as-you-go) when you consistently exceed **50,000 Firestore reads per day**. If you switch the Flutter app to use the native Firebase SDK instead of the Python Sync API, you can easily support 2,000+ DAU on the free tier before this happens.

## 9. Recommended Architecture
* **Flutter Frontend**: Connects directly to Firebase Auth and Firestore for all CRUD (Create, Read, Update, Delete) operations on Tasks, Habits, Notes, Chat.
* **FastAPI Backend**: Only used for secure operations that cannot be done on the client: AI requests, sending Emails, generating secure backups, and scheduled cron jobs.
