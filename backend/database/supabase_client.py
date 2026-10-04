import os
import threading

from dotenv import load_dotenv

load_dotenv()

_url = os.getenv("SUPABASE_URL", "")
# Use service_role key for server-side operations (bypasses RLS for writes).
# Falls back to anon key for local dev without a service role key.
_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")

if _url and _key:
    from supabase import create_client, Client as _Client

    # Ein Client pro Thread: postgrest nutzt eine httpx-Session mit HTTP/2, die
    # nicht von mehreren Threads gleichzeitig benutzt werden darf. FastAPI führt
    # sync-Routen im Threadpool aus; ein gemeinsamer Client führte dort zu
    # httpx.ReadError ([Errno 35] Resource temporarily unavailable) und damit zu
    # 500ern bei parallelen Requests. Daher get_supabase_client() pro Aufruf
    # verwenden und den Client nicht auf Modulebene zwischenspeichern.
    _local = threading.local()

    def get_supabase_client() -> _Client:
        client = getattr(_local, "client", None)
        if client is None:
            client = create_client(_url, _key)
            _local.client = client
        return client
else:
    from database.in_memory_store import get_in_memory_client

    def get_supabase_client():
        return get_in_memory_client()
