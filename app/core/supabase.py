from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY

# -------------------------------------------------
# Supabase Client Initialization
# -------------------------------------------------
def get_supabase_client() -> Client:
    """
    Returns a singleton Supabase client.
    Used across the entire backend.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# Global reusable client
supabase: Client = get_supabase_client()
