from openai import OpenAI
import os
import dotenv
from services.llm import load_llm_service
from logger.logger import get_logger
from config.config import load_config
import services.api.api_calls_model as api_calls_model

dotenv.load_dotenv()
 
class llm_agent:
 
    llm_service= load_llm_service()
    # Initialize OpenAI client for LM Studio
    logger = get_logger("streamlit")
    main_conf = load_config("main")
    prompt_conf = load_config("prompt")
    llm_conf = load_config("llm")
    client = llm_service.get_openai_client()
    system_prompt :str
    
    def __init__(self):
        self.system_prompt = self.prompt_conf.get_value(self.prompt_conf.config.prompt_templates.general_prompts.chat_system_prompt)
        self.logger.debug(f" System Prompt: {self.system_prompt}")


    def get_answer(self,request:api_calls_model.llm_request):
        try:
            model=self.llm_service.get_model_name()
            system_prompt= request.system_prompt if(request.system_prompt.strip()!="") else self.system_prompt
            self.logger(f"using system prompt {system_prompt}")

            llm_response = self.client.chat.completions.create(
                model=self.llm_service.get_model_name()  ,  # LM Studio will use the loaded model
                
                
                messages=[
                    system_prompt,
                    request.user_prompt
                ],
                
                #response_format=character_schema,
                temperature=self.llm_service.get_model_temp(),
                max_tokens=self.llm_service.max_new_tokens()
            )
            
            self.logger.debug(f" LM Studio Response: {llm_response}")

            # Extract text
            full_output = llm_response.choices[0].message.content.strip()
            return  full_output

        except Exception as e:
            return (f"Error: {e}")

    def get_formatted_answer(self, user_prompt:str):
            full_output = self.get_answer(user_prompt)
            # Split reasoning and final answer if possible
            reasoning_text = ""
            final_answer_text = full_output

            if "Final Answer:" in full_output:
                parts = full_output.split("Final Answer:")
                reasoning_text = parts[0].replace("Reasoning:", "").strip()
                final_answer_text = parts[1].strip()

            

def load():
    api = llm_agent()
    return api

if __name__ == "__main__":
    api = load()
    print(api.example_method())