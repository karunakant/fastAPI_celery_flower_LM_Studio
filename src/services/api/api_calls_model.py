from pydantic import BaseModel
from typing import Optional
import json


# Request body model
class Item(BaseModel):
    text: Optional[str]= ""
    seconds: Optional[int]= 0
    task_id: Optional[int] = 0
    result: Optional[str] =""


class SessionData(BaseModel):
    username: str

class llm_request(BaseModel):
    prompt:str
    system_prompt:str=""

class llm_response(BaseModel):
    full_answer:str=None
    answer:str=None
    reasoning:str =None
    status: str = "success"


class llm_sql_agent_response(BaseModel):
    message: Optional[str] = None
    thought: Optional[str] = None
    full_message: Optional[str] = None
    status: str = "success"

class llm_sql_agent_request(BaseModel):
    query:str
