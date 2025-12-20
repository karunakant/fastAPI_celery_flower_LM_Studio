
from fastapi.responses import JSONResponse
import uvicorn
from config.config import load_config
from pydantic import BaseModel
from celery_service.celery_worker import celery_app
from typing import Optional
from logger.logger import get_logger
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request,Depends,Response
from uuid import UUID, uuid4
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
import services.api.api_calls as api_call
import services.api.api_calls_model as api_calls_model



logger = get_logger("fast_api.main")

class SessionData(BaseModel):
    username: str


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

app = FastAPI()


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    try:
        logger.info(f"Creating session for user: {name}")
        session = uuid4()
        data = SessionData(username=name)

        await backend.create(session, data)
        cookie.attach_to_response(response, session)
        return f"created session for {name}"
    except Exception as e:
        logger.error(f"Error creating session for user {name}: {e}")
        return f"Failed to create session for {name}"
    
    


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    try:
    
        logger.info(f"Whoami called for user: {session_data.username}")
        return session_data
    
    except Exception as e:
        logger.error(f"Error in whoami: {e}")
        return {"status": "error", "message": str(e)}



@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    try:
        logger.info(f"Deleting session: {session_id}")
        await backend.delete(session_id)
        cookie.delete_from_response(response)
        return "deleted session"
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return f"Failed to delete session"


@app.get("/health")
async def health_check():
    try:
        logger.info("Health check endpoint called.")
        status = await api_call.health_check()
        return status
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/info")
async def info():
    try:
        logger.info("Info endpoint called.")
        info = await api_call.info()
        return info
    except Exception as e:
        logger.error(f"Error in info: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    try:
        logger.info("Root endpoint called.")
        message = await api_call.root()
        return message
    except Exception as e:
        logger.error(f"Error in root: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/process_task", dependencies=[Depends(cookie)])
async def process_task(item: api_calls_model.Item,session_id: UUID = Depends(cookie),session_data: SessionData = Depends(verifier)):
    try:
        logger.info(f"Process endpoint called with item: {item}")
        val = await api_call.process_task(item,session_data)
        return val
    except Exception as e:
        logger.error(f"Error in process: {e}")
        return {"status": "error","original":item.text, "processed":str(e)}

@app.post("/process_data",dependencies=[Depends(cookie)])
async def process_data(item: api_calls_model.Item,session_id: UUID = Depends(cookie),session_data: SessionData = Depends(verifier)):
    try:
        logger.info(f"Process Data endpoint called with item: {item}")
        processed_data = await  api_call.process_data(item,session_data)
        return processed_data
    except Exception as e:
        logger.error(f"Error in process_data: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/gen_ai_chat",dependencies=[Depends(cookie)])
async def get_ai_chat(llm_request: api_calls_model.llm_request,session_id: UUID = Depends(cookie),session_data: SessionData = Depends(verifier)):
    try:
        logger.info(f"Process Data endpoint called with item: {llm_request}")
        reason = await  api_call.gen_ai_chat(llm_request,session_data)
        return reason
    except Exception as e:
        logger.error(f"Error in process_data: {e}")
        response =api_calls_model.llm_response(response=str(e),status="error")
        return response
    

@app.post("/gen_ai_db_call",dependencies=[Depends(cookie)])
async def gen_ai_db_call(llm_sql_agent_request: api_calls_model.llm_sql_agent_request,session_id: UUID = Depends(cookie),session_data: SessionData = Depends(verifier)):
    try:
        logger.info(f"Process Data endpoint called with item: {llm_sql_agent_request}")
        reason = await  api_call.gen_ai_db_call(llm_sql_agent_request,session_data)
        return reason
    except Exception as e:
        logger.error(f"Error in process_data: {e}")
        response =api_calls_model.llm_sql_agent_response(response=str(e),status="error")
        return response
    


@app.get("/celery_status")
async def get_celery_status(item: api_calls_model.Item):
    try:
        logger.info(f"Status endpoint called with item: {item}")
        celery_status = await api_call.get_celery_status(item)
        return celery_status
    except Exception as e:
        logger.error(f"Error in get_celery_status: {e}")
        return {"status": "error", "message": str(e)}
    






if __name__ == "__main__":
    conf=load_config()
    uvicorn.run(
        "fast_api.main:app",
        host=conf.get_value(conf.environment.fast_api.server),
        port=conf.get_value(conf.environment.fast_api.port),
        reload=True)

