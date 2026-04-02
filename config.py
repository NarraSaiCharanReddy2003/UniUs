import os
from dotenv import load_dotenv

# Load .env from the same directory as this config file
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Data Configuration
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "data_unius.csv")

# App Configuration
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
PORT = int(os.getenv("PORT", "5000"))
