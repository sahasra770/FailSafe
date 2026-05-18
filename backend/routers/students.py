from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
import models, schemas, auth, database

router = APIRouter(prefix="/students", tags=["students"])

@router.get("/", response_model=List[schemas.StudentResponse])
def get_students(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_role(["faculty", "hod"]))):
    students = db.query(models.Student).all()
    return students

@router.get("/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "student":
        student_record = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if not student_record or student_record.id != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this student")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/upload")
def upload_students_csv(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_role(["faculty", "hod"]))):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = file.file.read()
    df = pd.read_csv(io.BytesIO(content))

    # Load model
    import joblib, numpy as np, os
    BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
    model      = joblib.load(os.path.join(BASE_DIR, "model.pkl"))
    features   = joblib.load(os.path.join(BASE_DIR, "features.pkl"))

    RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}

    for feat in features:
        if feat not in df.columns:
            df[feat] = 0

    X         = df[features].fillna(0)
    proba_all = model.predict_proba(X)
    pred_class = np.argmax(proba_all, axis=1)

    results = []
    id_col = next((c for c in ["student_id", "name", "id"] if c in df.columns), None)
    for i in range(len(df)):
        pc   = int(pred_class[i])
        prob = proba_all[i]
        results.append({
            "student_id":    str(df.iloc[i][id_col]) if id_col else f"row_{i+1}",
            "risk_label":    RISK_LABELS[pc],
            "risk_score":    round(float(prob[pc]) * 100, 2),
            "probabilities": {
                "Low":    round(float(prob[0]) * 100, 2),
                "Medium": round(float(prob[1]) * 100, 2),
                "High":   round(float(prob[2]) * 100, 2),
            }
        })

    from collections import Counter
    counts = Counter(r["risk_label"] for r in results)
    return {
        "students_processed": len(results),
        "summary": {"High": counts.get("High",0), "Medium": counts.get("Medium",0), "Low": counts.get("Low",0)},
        "predictions": results
    }
    
    