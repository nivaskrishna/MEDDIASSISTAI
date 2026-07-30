from pydantic_settings import BaseSettings, SettingsConfigDict

import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediAssist AI"
    DATABASE_URL: str = "sqlite+aiosqlite:////tmp/mediassist.db" if os.environ.get("VERCEL") or os.environ.get("STREAMLIT_SERVER_PORT") or os.path.exists("/tmp") else "sqlite+aiosqlite:///./mediassist.db"
    GEMINI_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    HUGGINGFACE_API_KEY: str = ""
    OPENFDA_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    MONGODB_URI: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    s = Settings()
    # Try reading from Streamlit secrets if st can be imported
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for key in ["GEMINI_API_KEY", "HUGGINGFACE_API_KEY", "OPENFDA_API_KEY", "OPENROUTER_API_KEY", "MONGODB_URI"]:
                if key in st.secrets and st.secrets[key]:
                    setattr(s, key, st.secrets[key])
    except Exception:
        pass
    return s

settings = get_settings()

