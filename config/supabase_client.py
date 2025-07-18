# config/supabase_client.py
from supabase import create_client, Client

# URL e Chave do Supabase (substitua pelas suas se quiser trocar depois)
url: str = "https://zgpfvrwsjsbsvevflypk.supabase.co"
key: str = "sb_secret_VpH-6yfypCG-7cUS6ZnQgQ_hQgPxLdJ"
supabase: Client = create_client(url, key)

