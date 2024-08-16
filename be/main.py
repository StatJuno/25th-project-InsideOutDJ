# backend/main.py
from fastapi import FastAPI
import pandas as pd
app = FastAPI()

@app.get("/")
def read_root():
    df = pd.read_json("top_5_songs.json")
    return df