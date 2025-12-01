import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENABLE_LOGGING = False

supabase = None
if SUPABASE_URL and SUPABASE_KEY and ENABLE_LOGGING:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
