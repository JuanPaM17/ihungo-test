import os
import logging
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model

load_dotenv(verbose=True)

logger = logging.getLogger(__name__)
tenants_llm = {}

def init_llm(tenant_id: str, version: str):
    try:
        # Inicializar LLM
        llm = init_chat_model(
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL"),
            model_provider=os.getenv("MODEL_PROVIDER"),
            temperature=float(os.getenv("LLM_TEMPERATURE", 0.1)),
        )
        tenants_llm[f"{tenant_id}-{version}"] = llm
        return llm
    except (KeyError, TypeError) as e:
        logger.error(f"Error in LLM configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error initializing LLM: {e}")
        raise

def get_llm(tenant_id: str, version: str):
    return tenants_llm.get(f"{tenant_id}-{version}")
