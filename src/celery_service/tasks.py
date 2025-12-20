import time
from celery_worker import celery_app

@celery_app.task(name="tasks.long_running_task")
def long_running_task(duration: int):
    """Simulates a long-running process."""
    time.sleep(duration)
    return {"status": "Task completed", "duration": duration}
