import io
import os
import asyncio
from collections import Counter
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import models
from auth import get_current_user
from database import SessionLocal, engine
from routers import auth, dashboard, interventions, predictions, students


# ── Improved Non-blocking Auto Seed ─────────────────────────────────────
async def auto_seed():
    db = SessionLocal()
    try:
        if db.query(models.User).count() <= 2:
            print("🔄 Starting database seeding...")
            try:
                def run_seed():
                    import import_real_data
                    import_real_data.seed()
                
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_seed)
                print("✅ Seeding completed successfully.")
            except Exception as e:
                print(f"⚠️ Seed error: {e}")
    finally:
        db.close()


# ── Lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    
    # Run seeding in background
    asyncio.create_task(auto_seed())
    
    print("✅ FAILSAFE API startup completed! Ready to accept requests.")
    yield
    
    print("👋 Shutting down FAILSAFE API...")


# ── Create FastAPI App ─────────────────────────────────────────────────────
app = FastAPI(
    title="FAILSAFE API",
    description="Student failure prediction and intervention system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(predictions.router)
app.include_router(interventions.router)
app.include_router(dashboard.router)


# ── Helpers ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")
FEAT_PATH = os.path.join(BASE_DIR, "ml", "features.pkl")

RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}


def format_prediction(pred_class: int, proba: np.ndarray) -> dict:
    return {
        "risk_label": RISK_LABELS[pred_class],
        "risk_score": round(float(proba[pred_class]) * 100, 2),
        "probabilities": {
            "Low": round(float(proba[0]) * 100, 2),
            "Medium": round(float(proba[1]) * 100, 2),
            "High": round(float(proba[2]) * 100, 2),
        },
    }


# ── CSV Upload Endpoint ───────────────────────────────────────────────────
@app.post("/upload-students")
async def upload_students(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

   