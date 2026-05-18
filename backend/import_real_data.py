import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import random
from database import SessionLocal, engine
import models
from ml_model import prediction_service
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEPARTMENTS = ["Computer Science", "Electronics", "Mechanical", "Civil", "Information Technology"]

FEATURE_NAMES = ['G1', 'G2', 'G3', 'absences', 'failures', 'studytime', 
                  'Medu', 'Fedu', 'goout', 'Dalc', 'Walc', 'health']

models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()

    db.query(models.Prediction).delete()
    db.query(models.Intervention).delete()
    db.query(models.Student).delete()
    db.query(models.User).delete()
    db.commit()

    faculty = models.User(name="Dr. Smith", email="faculty@failsafe.com",
                          password_hash=pwd_context.hash("password"), role="faculty")
    hod = models.User(name="Prof. Johnson", email="hod@failsafe.com",
                      password_hash=pwd_context.hash("password"), role="hod")
    db.add_all([faculty, hod])
    db.commit()

    df = pd.read_csv("processed_student_data.csv")

    random.seed(42)

    for i, row in df.iterrows():
        name = f"Student {i+1}"
        email = f"student{i+1}@failsafe.com"

        cgpa = round((row['G3'] / 20.0) * 10, 2)

        user = models.User(
            name=name,
            email=email,
            password_hash=pwd_context.hash("password"),
            role="student"
        )
        db.add(user)
        db.commit()

        dept = random.choice(DEPARTMENTS)
        roll_no = f"{dept[:2].upper()}{200+i}"
        student = models.Student(
            user_id=user.id,
            roll_no=roll_no,
            department=dept,
            semester=random.randint(2, 8),
            cgpa=cgpa
        )
        db.add(student)
        db.commit()

        features = {feat: row[feat] for feat in FEATURE_NAMES if feat in row}
        try:
            result = prediction_service.predict_risk(features)
            pred = models.Prediction(
                student_id=student.id,
                risk_score=result['risk_score'],
                risk_label=result['risk_label'],
                shap_values=result['shap_values']
            )
            db.add(pred)

            if result['risk_label'] == 'High':
                intervention = models.Intervention(
                    student_id=student.id,
                    type="Academic Support",
                    description=result.get('explanation', 'Schedule counseling session'),
                    assigned_by=faculty.id,
                    status="pending"
                )
                db.add(intervention)
        except Exception as e:
            print(f"Prediction error for student {i}: {e}")

        db.commit()
        if i % 10 == 0:
            print(f"Processed {i+1} students...")

    print(f"\nDone! Imported {len(df)} real students into FAILSAFE database.")
    db.close()

if __name__ == "__main__":
    seed()
