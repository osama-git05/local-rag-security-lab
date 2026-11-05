from app.paths import ROOT
import secrets
from pathlib import Path

env_path = ROOT / ".env"

# Exclusive creation prevents overwriting existing credentials.
with env_path.open("x", encoding="utf-8") as file:
    file.write(f"EMPLOYEE_TOKEN={secrets.token_urlsafe(32)}\n")
    file.write(f"ADMIN_TOKEN={secrets.token_urlsafe(32)}\n")

print("Created employee and administrator tokens in .env.")
print("Keep this file private. Do not commit or screenshot its contents.")