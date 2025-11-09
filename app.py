from fastapi import FastAPI, HTTPException, Body, Query
import asyncio
from parser import TGParser
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SESSION_NAME = os.getenv("SESSION_NAME")
DB_PATH = os.getenv("DB_PATH")
PROXY_IP = os.getenv("PROXY_IP")
PROXY_PORT = os.getenv("PROXY_PORT")

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run")
async def run(payload: dict = Body(...), token: str = Query(None)):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    channels = payload.get("channels")
    if not isinstance(channels, list):
        raise HTTPException(status_code=422, detail="Input should be a valid list")

    async def job():
        parser = TGParser(API_ID, API_HASH, SESSION_NAME, DB_PATH, WEBHOOK_URL, PROXY_IP, PROXY_PORT)
    await parser.run(channels)

    asyncio.create_task(job())
    return {"status": "started"}
