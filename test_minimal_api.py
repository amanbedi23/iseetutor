#!/usr/bin/env python3
"""Minimal API to test if FastAPI works"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="ISEE Tutor Test API")

@app.get("/")
def read_root():
    return {"message": "ISEE Tutor API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting minimal test API on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)