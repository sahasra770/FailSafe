from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine, SessionLocal
from routers import auth, students, predictions, interventions, dashboard
from auth import get_current_user
import numpy as np
import io
import joblib
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

def auto_seed():
    db = SessionLocal()
    if db.query(models.User).count() <= 2:
        try:
            import import_real_data
            import_real_data.seed()
        except Exception as e:
            print(f"Seed error: {e}")
    db.close()

auto_seed()

app = FastAPI(
    title="FAILSAFE API",
    description="Student failure prediction and intervention system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(predictions.router)
app.include_router(interventions.router)
app.include_router(dashboard.router)


# ── helpers ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")
FEAT_PATH  = os.path.join(BASE_DIR, "ml", "features.pkl")

RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}

def get_risk_label(pred_class: int, proba: list) -> dict:
    return {
        "risk_label": RISK_LABELS[pred_class],
        "risk_score": round(float(proba[pred_class]) * 100, 2),
        "probabilities": {
            "Low":    round(float(proba[0]) * 100, 2),
            "Medium": round(float(proba[1]) * 100, 2),
            "High":   round(float(proba[2]) * 100, 2),
        }
    }


# ── CSV upload endpoint ───────────────────────────────────────────────────────
@app.post("/upload-students")
async def upload_students(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """
    Faculty uploads a CSV. The endpoint runs XGBoost predictions and
    returns per-student risk levels (Low / Medium / High).

    Required columns: G1, G2, absences, failures, studytime
    Optional but recommended: Medu, Fedu, goout, Dalc, Walc, health,
                              famrel, freetime, traveltime, age
    A 'student_id' or 'name' column is used for identification if present.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse CSV. Make sure it is UTF-8 encoded.")

    # Load model + feature list
    try:
        model    = joblib.load(MODEL_PATH)
        features = joblib.load(FEAT_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ML model not found. Please retrain first.")

    # Check minimum required columns
    min_required = ["G1", "G2", "absences", "failures", "studytime"]
    missing = [c for c in min_required if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}. "
                   f"Required: {min_required}"
        )

    # Fill any missing optional feature columns with 0
    for feat in features:
        if feat not in df.columns:
            df[feat] = 0

    X = df[features].fillna(0)

    proba_all  = model.predict_proba(X)          # shape (n_students, 3)
    pred_class = np.argmax(proba_all, axis=1)    # 0/1/2

    results = []
    id_col = next((c for c in ["student_id", "name", "id"] if c in df.columns), None)

    for i, row in enumerate(df.itertuples(index=False)):
        student_id = getattr(row, id_col) if id_col else f"row_{i+1}"
        pc   = int(pred_class[i])
        prob = proba_all[i]
        results.append({
            "student_id":    str(student_id),
            "risk_label":    RISK_LABELS[pc],
            "risk_score":    round(float(prob[pc]) * 100, 2),
            "probabilities": {
                "Low":    round(float(prob[0]) * 100, 2),
                "Medium": round(float(prob[1]) * 100, 2),
                "High":   round(float(prob[2]) * 100, 2),
            }
        })

    # Summary counts
    from collections import Counter
    counts = Counter(r["risk_label"] for r in results)

    return {
        "students_processed": len(results),
        "summary": {
            "High":   counts.get("High", 0),
            "Medium": counts.get("Medium", 0),
            "Low":    counts.get("Low", 0),
        },
        "predictions": results
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to the FAILSAFE API"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))