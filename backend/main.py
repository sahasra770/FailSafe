import io
import os
from collections import Counter
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
import uvicorn  # Fixed: Added missing import
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import models
from auth import get_current_user
from database import SessionLocal, engine
from routers import auth, dashboard, interventions, predictions, students


def auto_seed():
    db = SessionLocal()
    try:
        # Check if DB needs seeding
        if db.query(models.User).count() <= 2:
            try:
                import import_real_data
                import_real_data.seed()
            except Exception as e:
                print(f"Seed error: {e}")
    finally:
        db.close()


# ── lifespan: runs AFTER uvicorn binds the port ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed data
    models.Base.metadata.create_all(bind=engine)
    auto_seed()
    yield
    # Shutdown (add cleanup here if needed)


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


# ── helpers ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")
FEAT_PATH = os.path.join(BASE_DIR, "ml", "features.pkl")

RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}


def format_prediction(pred_class: int, proba: np.ndarray) -> dict:
    """Helper to consistently format the prediction payload."""
    return {
        "risk_label": RISK_LABELS[pred_class],
        "risk_score": round(float(proba[pred_class]) * 100, 2),
        "probabilities": {
            "Low": round(float(proba[0]) * 100, 2),
            "Medium": round(float(proba[1]) * 100, 2),
            "High": round(float(proba[2]) * 100, 2),
        },
    }


# ── CSV upload endpoint ───────────────────────────────────────────────────────
@app.post("/upload-students")
async def upload_students(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Only .csv files are accepted."
        )

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse CSV. Make sure it is UTF-8 encoded.",
        )

    try:
        model = joblib.load(MODEL_PATH)
        features = joblib.load(FEAT_PATH)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="ML model files missing. Please ensure models are trained and saved.",
        )

    # Validate essential columns
    min_required = ["G1", "G2", "absences", "failures", "studytime"]
    missing = [c for c in min_required if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}. Required baseline: {min_required}",
        )

    # Fill missing expected features with 0 to prevent ML model misalignment
    for feat in features:
        if feat not in df.columns:
            df[feat] = 0

    X = df[features].fillna(0)

    # Predict batch
    try:
        proba_all = model.predict_proba(X)
        pred_class = np.argmax(proba_all, axis=1)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error running inference on data: {str(e)}"
        )

    results = []

    # Dynamically locate ID identifier using dictionary conversion for safer parsing
    id_candidates = ["student_id", "name", "id"]
    id_col = next((c for c in id_candidates if c in df.columns), None)

    for i, row_dict in enumerate(df.to_dict(orient="records")):
        # Match student ID fallback safely
        student_id = row_dict.get(id_col) if id_col else f"row_{i+1}"

        # Format using the helper function
        pred_data = format_prediction(int(pred_class[i]), proba_all[i])
        pred_data["student_id"] = str(student_id)

        results.append(pred_data)

    counts = Counter(r["risk_label"] for r in results)

    return {
        "students_processed": len(results),
        "summary": {
            "High": counts.get("High", 0),
            "Medium": counts.get("Medium", 0),
            "Low": counts.get("Low", 0),
        },
        "predictions": results,
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to the FAILSAFE API"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)