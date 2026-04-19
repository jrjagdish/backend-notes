from fastapi import FastAPI
from dotenv import load_dotenv
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
connection = psycopg2.connect(DATABASE_URL)
load_dotenv()

app = FastAPI()

@app.get("/")
def health_check():
    return {"message" : "API working good"}

