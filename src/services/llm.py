from openai import OpenAI
from langchain_openai import ChatOpenAI
import os
import dotenv
from config.config import load_config
from logger.logger import get_logger

dotenv.load_dotenv()

class LLMService:
    main_config = load_config("main")
    llm_config = load_config("llm")
    logger = get_logger("llm_service")
    prompt_template_conf = load_config(type_config="prompt") 
    ai_url: str
    ai_key: str
    llm_num:int = 0
    llm_model_num:int = 0
    

    def __init__(self, llm:int = 0, model:int=0):
            self.llm_num  = llm
            self.llm_model_num = model
            self.ai_url = self.llm_config.get_value(self.llm_config.config.types.llms[llm].server.base_url)
            self.ai_key = self.llm_config.get_value(self.llm_config.config.types.llms[llm].server.api_key)

    def get_openai_client(self):
        
        # Initialize OpenAI client for LM Studio
        self.logger.debug(f" LM Studio API Base URL: {self.ai_url}")
        self.logger.debug(f" LM Studio API Key: {self.ai_key}")
        client = OpenAI(base_url=self.ai_url, api_key=self.ai_key)
        self.logger.debug(f" OpenAI client for LM Studio initialized successfully.{client}")
        return client
    
    def get_chat_openai_client(self):
        self.logger.debug(f" LM Studio API Base URL: {self.ai_url}")
        self.logger.debug(f" LM Studio API Key: {self.ai_key}")
        chat_client = ChatOpenAI(api_key=self.ai_key,base_url=self.ai_url)
        self.logger.debug(f" LM Studio chat object setup: {chat_client}")
        return chat_client

    def get_model_name(self):
        model_name = self.llm_config.get_value(self.llm_config.config.types.llms[self.llm_num].models[self.llm_model_num].name)
        self.logger.debug(f" LM Studio Model Name: {model_name}")
        return model_name
    
    def get_model_temp(self):
        model_temp = self.llm_config.get_value(self.llm_config.config.types.llms[self.llm_num].params.temperature)
        self.logger.debug(f" LM Studio Model Temperature: {model_temp}")
        return model_temp
    
    def get_model_max_new_tokens(self):
        model_max_new_tokens = self.llm_config.get_value(self.llm_config.config.types.llms[self.llm_num].params.max_new_tokens)
        self.logger.debug(f" LM Studio Model Temperature: {model_max_new_tokens}")
        return model_max_new_tokens
    

    def get_model_max_new_tokens(self):
        model_max_new_tokens = self.llm_config.get_value(self.llm_config.config.types.llms[0].params.max_new_tokens)
        self.logger.debug(f" LM Studio Model Temperature: {model_max_new_tokens}")
        return model_max_new_tokens


    def get_model_max_new_tokens(self):
        model_max_new_tokens = self.llm_config.get_value(self.llm_config.config.types.llms[0].params.max_new_tokens)
        self.logger.debug(f" LM Studio Model Temperature: {model_max_new_tokens}")
        return model_max_new_tokens
    
def load_llm_service(llm_num:int=0, llm_model_num:int=0):
    llm_service = LLMService(llm=llm_num, model=llm_model_num)
    return llm_service

if __name__ == "__main__":
    llm_service = load_llm_service(llm_num=0, llm_model_num=0)
    client = llm_service.get_openai_client()
    model_name = llm_service.get_model_name()
    model_temp = llm_service.get_model_temp()
    response = client.chat.completions.create(
        model=model_name,
        temperature=model_temp,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "who is president of india"}
        ]
    )

    llm_service.logger.info(f"Response from LM Studio: {response}")
    print (response)

    chat_client = llm_service.get_chat_openai_client()
    response = chat_client.invoke("Hello, how are you?")
    print(response.content)
    llm_service.logger.info(f"Response from LM Studio: {response}")
    print (response)