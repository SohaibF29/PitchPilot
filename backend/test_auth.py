import asyncio
from app.config import get_settings

settings = get_settings()
secret = settings.supabase_jwt_secret.get_secret_value()
print(f"SECRET IS: '{secret}'")
print(f"is_development: {settings.is_development}")

if not secret:
    print("INSIDE NOT SECRET")
else:
    print("SECRET IS POPULATED!")
