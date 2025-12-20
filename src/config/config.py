import jsoncfg
import os
import dotenv
from logger.logger import get_logger
import sys

dotenv.load_dotenv()

class ConfigData:
    
    dev_server = None
    qa_server = None
    uat_server = None
    prod_server = None
    environment = None
    config = None
    type_config = "main"
    logger = None
    cwd = os.getcwd()

    def __init__(self,type_config="main"):
        self.logger = get_logger("config/config.py")
        
        self.type_config = type_config
        self.logger.debug(f" Configuration type : {self.type_config}")
        is_full_path = os.environ.get("IS_FULL_PATH","False").lower() in ("true", "1", "t")
        self.logger.debug(f" Is Full Path : {is_full_path}")
        if(type_config.lower()=="main"):
            config_file = os.environ.get("MAIN_CONFIG_FILE","main.json")
        elif(type_config.lower()=="prompt"):
            config_file = os.environ.get("PROMPT_CONFIG_FILE","prompt.json")
        elif(type_config.lower()=="llm"):
            config_file = os.environ.get("LLM_CONFIG_FILE","llm.json")
        
        
        self.logger.debug(f" Main Configuration file from env : {config_file}")
        config_file = self.getFullPath(config_file,is_full_path)
        self.logger.debug(f" Loading configuration file : {config_file}")    
        self.config = jsoncfg.load_config(config_file)
        self.environment = self.get_environment() if(type_config.lower()=="main") else "dev"

        
    def getFullPath(self,file_name,is_full_path):
        
        file_path = ""
        try:
            self.logger.debug(f" Getting full path for file : {file_name} with is_full_path : {is_full_path}")
            file_path = file_name if is_full_path else os.path.join(self.cwd, file_name)    
            self.logger.debug(f" Full path for file : {file_path}")
        except Exception as e:
            self.logger.error(f" Error getting full path for file : {file_name} with error : {e}")
            sys.exit(1)
        return file_path
    
    
    def get_environment(self):
        env = os.environ.get("ENV","dev")
        for current_env in self.config.servers:
            self.logger.info(f" loading current environment : {current_env.name.value}")
            if(current_env.name.value == "dev"):
                self.dev_server = current_env

            if(current_env.name.value == "qa"):
                self.qa_server = current_env
            
            if(current_env.name.value == "uat"):
                self.uat_server = current_env

            if(current_env.name.value == "prod"):
                self.prod_server = current_env

            if(current_env.name.value == env):
                self.environment = current_env
        self.logger.debug(f" Loaded environment : {self.environment.name.value}")
        return self.environment

    def get_value(self,attrib):
        self.logger.debug(f" Getting value for attribute : {attrib}")
        try:
            self.logger.debug(f" Value for attribute : {attrib} is {attrib.value}")
            return attrib.value
        except Exception as e:
            self.logger.error(f" Error getting value for attribute : {attrib} with error : {e}")
            return None
    

def load_config(type_config="main"):
    conf = ConfigData(type_config)
    print(f" Configuration loaded for type : {conf}")
    return conf

def main():
    conf = load_config()
    print(conf.get_value(conf.environment.name))
    print(conf.get_value(conf.environment.fast_api.server)) 
    print(conf.get_value(conf.environment.fast_api.port)) 
    conf_prompt = load_config("prompt")
    print(conf_prompt.get_value(conf_prompt.config.prompt_templates.sql_query_check))


if __name__=="__main__":
    main()