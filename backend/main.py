import io
import os
import asyncio
import random
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

# Password hashing (used in upload)
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEPARTMENTS = ["Computer Science", "Electronics", "Mechanical", "Civil", "Information Technology"]

# Features used by the model
FEATURE_NAMES = [
    'G1', 'G2', 'absences', 'failures', 'studytime',
    'Medu', 'Fedu', 'goout', 'Dalc', 'Walc', 'health',
    'famrel', 'freetime', 'traveltime', 'age'
]

from ml_model import prediction_service


def get_intervention(row, risk_label):
    """Generate intervention based on student data"""
    reasons = []

    if row.get('absences', 0) > 10:
        reasons.append(('absences', row['absences']))
    if row.get('failures', 0) > 0:
        reasons.append(('failures', row['failures']))
    if row.get('G2', 20) < 10:
        reasons.append(('low_grades', row['G2']))
    if row.get('studytime', 4) < 2:
        reasons.append(('studytime', row['studytime']))
    if row.get('goout', 1) > 3:
        reasons.append(('goout', row['goout']))
    if row.get('Dalc', 1) > 2 or row.get('Walc', 1) > 3:
        reasons.append(('alcohol', row.get('Dalc', 0)))
    if row.get('health', 5) < 2:
        reasons.append(('health', row['health']))

    prefix = "[Early Intervention] " if risk_label == 'Medium' else ""

    if not reasons:
        return "Academic Mentorship", prefix + "Assign academic mentor and schedule bi-weekly progress review sessions"

    primary = reasons[0][0]

    if primary == 'absences':
        return "Attendance Counseling", f"{prefix}Student has {int(reasons[0][1])} absences. Schedule immediate counseling."
    elif primary == 'failures':
        return "Remedial Support", f"{prefix}Student has {int(reasons[0][1])} failed subject(s). Enroll in remedial classes."
    elif primary == 'low_grades':
        return "Academic Tutoring", f"{prefix}Low performance in recent exams. Provide personalized tutoring."
    elif primary == 'studytime':
        return "Study Plan Adjustment", f"{prefix}Low study time. Create structured study schedule."
    elif primary == 'goout':
        return "Counseling Referral", f"{prefix}High social activity affecting studies."
    elif primary == 'alcohol':
        return "Wellness Counseling", f"{prefix}Lifestyle factors detected."
    elif primary == 'health':
        return "Health Support", f"{prefix}Health issues reported."
    else:
        return "Academic Support", prefix + "Multiple risk factors. Assign mentor."


# ── Lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ FAILSAFE API startup completed!")
    yield
    print("👋 Shutting down...")


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


# ── Upload Students with Prediction ─────────────────────────────────────
@app.post("/upload-students")
async def upload_students(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        db = SessionLocal()
        uploaded_count = 0
        predicted_count = 0

        for i, row in df.iterrows():
            # Create User
            name = f"Student {uploaded_count + 1}"
            email = f"student{uploaded_count + 1}@failsafe.com"

            user = models.User(
                name=name,
                email=email,
                password_hash=pwd_context.hash("password"),
                role="student"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create Student
            dept = random.choice(DEPARTMENTS)
            roll_no = f"{dept[:2].upper()}{1000 + uploaded_count}"
            cgpa = round((row.get('G2', 10) / 20.0) * 10, 2)

            student = models.Student(
                user_id=user.id,
                roll_no=roll_no,
                department=dept,
                semester=random.randint(2, 8),
                cgpa=cgpa
            )
            db.add(student)
            db.commit()
            db.refresh(student)

            # Run Prediction
            features = {feat: float(row.get(feat, 0)) for feat in FEATURE_NAMES}
            try:
                result = prediction_service.predict_risk(features)

                pred = models.Prediction(
                    student_id=student.id,
                    risk_score=result['risk_score'],
                    risk_label=result['risk_label'],
                    shap_values=result.get('shap_values', {})
                )
                db.add(pred)

                # Create Intervention for Medium/High Risk
                if result['risk_label'] in ['High', 'Medium']:
                    int_type, int_desc = get_intervention(row.to_dict(), result['risk_label'])
                    intervention = models.Intervention(
                        student_id=student.id,
                        type=int_type,
                        description=int_desc,
                        assigned_by=current_user.id,
                        status="pending"
                    )
                    db.add(intervention)

                predicted_count += 1
            except Exception as e:
                print(f"Prediction error for student {i}: {e}")

            uploaded_count += 1
            if uploaded_count % 50 == 0:
                db.commit()  # Commit in batches

        db.commit()
        db.close()

        return {
            "message": f"Successfully uploaded {uploaded_count} students",
            "predicted": predicted_count,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)