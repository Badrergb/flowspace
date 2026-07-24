import uuid
import time
from app.models.entities import Task

def test_get_tasks(auth_client, test_db, test_user_and_token):
    user, _, _ = test_user_and_token
    
    # Create two tasks, one soft-deleted
    task1 = Task(id=uuid.uuid4(), user_id=user.id, title="Active Task", version=int(time.time_ns()))
    task2 = Task(id=uuid.uuid4(), user_id=user.id, title="Deleted Task", version=int(time.time_ns()))
    import datetime
    task2.deleted_at = datetime.datetime.utcnow()
    
    test_db.add_all([task1, task2])
    test_db.commit()
    
    response = auth_client.get("/api/v1/entities/tasks")
    assert response.status_code == 200
    data = response.json()
    
    # Verify soft-deleted task is hidden
    ids = [t["id"] for t in data]
    assert str(task1.id) in ids
    assert str(task2.id) not in ids

def test_get_tasks_pagination(auth_client, test_db, test_user_and_token):
    user, _, _ = test_user_and_token
    
    # Create 15 tasks
    tasks = []
    for i in range(15):
        tasks.append(Task(id=uuid.uuid4(), user_id=user.id, title=f"Task {i}", version=int(time.time_ns())))
    
    test_db.add_all(tasks)
    test_db.commit()
    
    response = auth_client.get("/api/v1/entities/tasks?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 10
    
    response2 = auth_client.get("/api/v1/entities/tasks?skip=10&limit=10")
    assert response2.status_code == 200
    assert len(response2.json()) >= 5

def test_get_child_entities(auth_client, test_db, test_user_and_token):
    user, _, _ = test_user_and_token
    from app.models.entities import Habit, HabitLog, WorkoutSession, WorkoutSet
    
    habit = Habit(id=uuid.uuid4(), user_id=user.id, title="Test Habit", frequency="daily", version=int(time.time_ns()))
    test_db.add(habit)
    test_db.commit()
    
    import datetime
    hlog = HabitLog(id=uuid.uuid4(), habit_id=habit.id, completed_at=datetime.datetime.utcnow(), version=int(time.time_ns()))
    test_db.add(hlog)
    test_db.commit()
    
    response = auth_client.get("/api/v1/entities/habit-logs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert str(hlog.id) in [h["id"] for h in data]
    
    session = WorkoutSession(id=uuid.uuid4(), user_id=user.id, title="Test Session", started_at=datetime.datetime.utcnow(), version=int(time.time_ns()))
    test_db.add(session)
    test_db.commit()
    
    wset = WorkoutSet(id=uuid.uuid4(), workout_session_id=session.id, exercise_name="Bench Press", set_number=1, reps=10, weight_kg=100.0, version=int(time.time_ns()))
    test_db.add(wset)
    test_db.commit()
    
    response2 = auth_client.get("/api/v1/entities/workout-sets")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) >= 1
    assert str(wset.id) in [w["id"] for w in data2]
    
    test_db.delete(wset)
    test_db.delete(hlog)
    test_db.commit()
    test_db.delete(session)
    test_db.delete(habit)
    test_db.commit()
