from celery import Celery
import os
import dotenv
import time
from functools import wraps
import asyncio
from asgiref.sync import AsyncToSync
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar
from pydantic import BaseModel
from config.config import load_config

dotenv.load_dotenv()

_P = ParamSpec("_P")
_R = TypeVar("_R")
conf = load_config()
# Configure Celery with Redis as broker and backend
celery_app = Celery(
    "llm_worker",
    broker= f"{conf.get_value(conf.environment.celery.broker_url)}",   # Redis broker
    backend=f"{conf.get_value(conf.environment.celery.result_backend)}",  # Redis result backend
)

# Optional: Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")

def async_task(*args: Any, **kwargs: Any):
    def _decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        #sync_call = AsyncToSync(func)

        @celery_app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args, **kwargs):
            return func(*args, **kwargs)

        return _decorated
    return _decorator