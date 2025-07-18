from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zgpfvrwsjsbsvevflypk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_secret_VpH-6yfypCG-7cUS6ZnQgQ_hQgPxLdJ")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
