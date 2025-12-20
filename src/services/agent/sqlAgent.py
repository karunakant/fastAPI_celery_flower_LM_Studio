from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_community.utilities import SQLDatabase
import json
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import END, MessageGraph
from langgraph.prebuilt.tool_node import ToolNode
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
import uuid
from logger.logger import get_logger
from services.llm import load_llm_service
from config.config import load_config
import atexit
import services.api.api_calls_model as api_calls_model
llm_service = load_llm_service()
conf = load_config("main")
logger = get_logger("services.agent.sqlAgent")

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

conn_str= conf.get_value(conf.environment.db.connection_string)


def setup_db():
    # Setup your database connection here
    # For example, using a PostgreSQL database
    logger.debug(f" Database connection string : {conn_str}")
    db = SQLDatabase.from_uri(conn_str)
    logger.debug(f"dialect: {db.dialect}")
    logger.debug(f"Usable Tables Names: {db.get_usable_table_names()}")
    return db

    
def get_llm():
    model = llm_service.get_model_name()
    temperature = llm_service.get_model_temp()
    llm = llm_service.get_chat_openai_client()
    return llm

# SQL toolkit
db = setup_db()
llm = get_llm()
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# Query checking
query_check_system = llm_service.prompt_template_conf.get_value(llm_service.prompt_template_conf.config.prompt_templates.sql_prompt.sql_query_check)
query_check_prompt = ChatPromptTemplate.from_messages([("system", query_check_system),("user", "{query}")])

query_check = query_check_prompt | llm

@tool
def check_query_tool(query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it.
    """
    return query_check.invoke({"query": query}).content

# Query result checking
query_result_check_system = f"""{llm_service.prompt_template_conf.get_value(llm_service.prompt_template_conf.config.prompt_templates.sql_prompt.query_result_check_system)}"""
query_result_check_prompt = ChatPromptTemplate.from_messages([("system", query_result_check_system),("user", "{query_result}")])
query_result_check = query_result_check_prompt | llm


@tool
def check_result(query_result: str) -> str:
    """
    Use this tool to check the query result from the database to confirm it is not empty and is relevant.
    """
    return query_result_check.invoke({"query_result": query_result}).content

tools.append(check_query_tool)
tools.append(check_result)

# Assistant
class Assistant:
    
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            # Append to state
            state = {**state}
            # Invoke the tool-calling LLM
            result = self.runnable.invoke(state)
            # If it is a tool call -> response is valid
            # If it has meaninful text -> response is valid
            # Otherwise, we re-prompt it b/c response is not meaninful
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

# Assistant runnable
query_gen_system = f"""
{llm_service.prompt_template_conf.get_value(llm_service.prompt_template_conf.config.prompt_templates.sql_prompt.query_gen_system)}"""

query_gen_prompt = ChatPromptTemplate.from_messages([("system", query_gen_system),("placeholder", "{messages}")])
assistant_runnable = query_gen_prompt | llm.bind_tools(tools)

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print(f"Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }



# Graph
builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(tools))

# Define edges: these determine how the control flow moves
builder.set_entry_point("assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition, 
    # "tools" calls one of our tools. END causes the graph to terminate (and respond to the user)
    {"tools": "tools", END: END},
)
builder.add_edge("tools", "assistant")


# The checkpointer lets the graph persist its state
# `from_conn_string` returns a context manager; enter it to get the actual saver
memory_cm = PostgresSaver.from_conn_string(conn_str)
memory = memory_cm.__enter__()
# ensure the saver is initialized (idempotent)
try:
    memory.setup()
except Exception:
    # ignore if already setup or if setup is not needed here
    pass
# register cleanup at program exit to call __exit__ on the context manager
atexit.register(memory_cm.__exit__, None, None, None)

graph = builder.compile(checkpointer=memory)

def sql_agent_query(query: str)->api_calls_model.llm_sql_agent_response:
    ''''
    questions = ["Which country's customers spent the most? And how much did they spend?",
             "How many albums does the artist Led Zeppelin have?",
             "What was the most purchased track of 2017?",
             "Which sales agent made the most in sales in 2009?"]

'''
    ## Invoke

    _printed = set()
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            # Checkpoints are accessed by thread_id
            "thread_id": thread_id,
        }
    }
    msg = {"messages": ("user", query)}
    messages = graph.invoke(msg, config)
    out = messages["messages"][-1].content
    logger.info(f"output of query is:{out}")
    # attempt to split thought vs message if agent uses <think>...</think>
    parts = out.split("</think>") if isinstance(out, str) else [",", out]
    thought = parts[0].replace("<think>", "") if parts else None
    message = parts[1] if len(parts) > 1 else out
    full_message = out
    response = api_calls_model.llm_sql_agent_response(
        message=message,
        thought=thought,
        full_message=full_message,
        status="success",
    )
    logger.info(f"output of query is:{response}")
    return response

if __name__ == "__main__":
    response = sql_agent_query("give me list of all tables")
    print (response)