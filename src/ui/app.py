import streamlit as st
from openai import OpenAI
import os
import dotenv
from services.llm import load_llm_service
from logger.logger import get_logger
from config.config import load_config

dotenv.load_dotenv()
 
llm_service= load_llm_service()
# Initialize OpenAI client for LM Studio
logger = get_logger("streamlit")
main_conf = load_config("main")
prompt_conf = load_config("prompt")
llm_conf = load_config("llm")
client = llm_service.get_openai_client()
# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="Local LLM with CoT", page_icon="🤖", layout="centered")
st.title("🤖 Local LLM via LM Studio + CoT Display")

# User input
user_prompt = st.text_area("Enter your question:", height=100)

# Define the expected response structure
character_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "characters",
        "schema": {
            "type": "object",
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "occupation": {"type": "string"},
                            "personality": {"type": "string"},
                            "background": {"type": "string"}
                        },
                        "required": ["name", "occupation", "personality", "background"]
                    },
                    "minItems": 1,
                }
            },
            "required": ["characters"]
        },
    }
}


if st.button("Generate Answer"):
    if not user_prompt.strip():
        st.warning("Please enter a question.")
    else:
        try:
            # Prompt engineering to request reasoning
            system_prompt = prompt_conf.get_value(prompt_conf.config.prompt_templates.general_prompts.chat_system_prompt)
            logger.debug(f" System Prompt: {system_prompt}")
            logger.debug(f" User Prompt: {user_prompt}")
            # Call LM Studio local API
            response = client.chat.completions.create(
                model=llm_service.get_model_name()  ,  # LM Studio will use the loaded model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                #response_format=character_schema,
                temperature=0.1,
                max_tokens=500
            )
            logger.debug(f" LM Studio Response: {response}")

            # Extract text
            full_output = response.choices[0].message.content.strip()

            # Split reasoning and final answer if possible
            reasoning_text = ""
            final_answer_text = full_output
            print (final_answer_text)

            if "Final Answer:" in full_output:
                parts = full_output.split("Final Answer:")
                reasoning_text = parts[0].replace("Reasoning:", "").strip()
                final_answer_text = parts[1].strip()

            # Display results
            if reasoning_text:
                st.subheader("🧠 Chain of Thought (Model-Generated)")
                st.markdown(f"```\n{reasoning_text}\n```")

            st.subheader("✅ Final Answer")
            st.write(final_answer_text)

        except Exception as e:
            st.error(f"Error: {e}")
