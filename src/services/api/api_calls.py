import services.api.api_calls_model as api_calls_model
import os
import dotenv
from services.llm import load_llm_service
from logger.logger import get_logger
from config.config import load_config
from services.agent.sqlAgent import sql_agent_query
from celery_service.celery_worker import async_task

llm_service = load_llm_service()
conf = load_config("main")
prompt_conf = load_config("prompt")
logger = get_logger("services.api.api_calls")

def __init__(self):
    pass

async def health_check(self):
    logger.info("Health check endpoint called.")
    status = {"status": "ok"}
    return status

async def info(self):
    logger.info("Info endpoint called.")
    info = {"app": "FastAPI with Celery", "version": "1.0.0"}
    return info

async def root(self):
    logger.info("Root endpoint called.")
    message = {"message": "Welcome to the FastAPI with Celery service."}
    return message


async def process_task( item: api_calls_model.Item, session_data: api_calls_model.SessionData):
    logger.info(f"Process endpoint called with item: {item} from session: {session_data.username}")
    processed = item.text[::-1]
    val = api_calls_model.ProcessResponse(original=item.text, processed=processed, status="completed")
    logger.info(f"original: {item.text} processed: {processed}") 
    return val


async def process_data( item: api_calls_model.Item, session_data: api_calls_model.SessionData):
    logger.info(f"Process Data endpoint called with item: {item}")
    processed_data = (f"{item.text} - processed by {session_data.username}")
    logger.info(f"original: {item.text} processed: {processed_data}")
    return processed_data

@async_task(name="api_calls.gen_ai_chat")
async def gen_ai_chat( item: api_calls_model.llm_request, session_data: api_calls_model.SessionData):
    logger.info(f"gen_ai_chat endpoint called with item: {item}")
    chat_client = llm_service.get_chat_openai_client()
    output = chat_client.invoke(
        item.prompt
    )
    return output

@async_task(name="api_calls.gen_ai_db_call")
async def gen_ai_db_call( item: api_calls_model.llm_sql_agent_request, session_data: api_calls_model.SessionData):
    logger.info(f"gen_ai_db_call endpoint called with item: {item}")
    output = sql_agent_query(item.query)
    logger.info(f"original: {item.query} processed: {output}")
    return output

async def get_celery_status(item: api_calls_model.Item):
    logger.info(f"Status endpoint called with item: {item}")
    celery_status = {"status": "running"}
    return celery_status



if __name__ == "__main__":
    item = api_calls_model.genAIRequest(prompt="What is capital of india")
    session_data = api_calls_model.SessionData(username="mishra")
    res = gen_ai_chat(item=item,session_data = session_data)
    print(res)
