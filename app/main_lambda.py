"""
Lambda entrypoint for the "web" function: wraps the exact same FastAPI app
used by `uvicorn app.main:app` locally (app/main.py is untouched) with
Mangum, so API Gateway (HTTP API) events get turned into ASGI calls.

Deployed only -- not used by `uvicorn` locally.
"""
from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
