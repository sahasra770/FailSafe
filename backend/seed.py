import auth
import models
import database
from datetime import datetime
from sqlalchemy.orm import Session
from ml_model import prediction_service

def seed_db():
    models.Base.metadata.drop_all(bind=database.engine)
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    
    # Create Users
    faculty = models.User(name="Dr. Smith", email="faculty@failsafe.com", password_hash=auth.get_password_hash("password"), role="faculty")
    hod = models.User(name="Prof. Johnson", email="hod@failsafe.com", password_hash=auth.get_password_hash("password"), role="hod")
    student1_user = models.User(name="Alice Cooper", email="alice@failsafe.com", password_hash=auth.get_password_hash("password"), role="student")
    student2_user = models.User(name="Bob Builder", email="bob@failsafe.com", password_hash=auth.get_password_hash("password"), role="student")
    student3_user = models.User(name="Charlie Brown", email="charlie@failsafe.com", password_hash=auth.get_password_hash("password"), role="student")
    
    db.add_all([faculty, hod, student1_user, student2_user, student3_user])
    db.commit()

    # Create Students
    s1 = models.Student(user_id=student1_user.id, roll_no="CS101", department="Computer Science", semester=4, cgpa=8.5)
    s2 = models.Student(user_id=student2_user.id, roll_no="CS102", department="Computer Science", semester=4, cgpa=5.5)
    s3 = models.Student(user_id=student3_user.id, roll_no="CS103", department="Computer Science", semester=4, cgpa=7.0)
    
    db.add_all([s1, s2, s3])
    db.commit()

    # Add Attendance
    db.add(models.Attendance(student_id=s1.id, subject="Math", attendance_percentage=90.0, week=1))
    db.add(models.Attendance(student_id=s2.id, subject="Math", attendance_percentage=45.0, week=1))
    db.add(models.Attendance(student_id=s3.id, subject="Math", attendance_percentage=75.0, week=1))

    # Add Assignments
    db.add(models.Assignment(student_id=s1.id, subject="Math", score=85.0))
    db.add(models.Assignment(student_id=s2.id, subject="Math", score=40.0))
    db.add(models.Assignment(student_id=s3.id, subject="Math", score=65.0))
    db.commit()

    # Generate initial predictions for them
    for s in [s1, s2, s3]:
        attendances = db.query(models.Attendance).filter(models.Attendance.student_id == s.id).all()
        avg_att = sum(a.attendance_percentage for a in attendances) / len(attendances)
        assignments = db.query(models.Assignment).filter(models.Assignment.student_id == s.id).all()
        avg_ass = sum(a.score for a in assignments) / len(assignments)

        res = prediction_service.predict_risk({
    'absences': avg_att,
    'G1': avg_ass,
    'G2': avg_ass,
    'G3': s.cgpa * 4,
    'failures': 0,
    'studytime': 2,
    'school': 'GP',
    'sex': 'M',
    'age': 18,
    'address': 'U',
    'famsize': 'GT3',
    'Pstatus': 'T',
    'Medu': 2, 'Fedu': 2,
    'Mjob': 'other', 'Fjob': 'other',
    'reason': 'course', 'guardian': 'mother',
    'traveltime': 1, 'schoolsup': 'no',
    'famsup': 'yes', 'paid': 'no',
    'activities': 'no', 'nursery': 'yes',
    'higher': 'yes', 'internet': 'yes',
    'romantic': 'no', 'famrel': 3,
    'freetime': 3, 'goout': 3,
    'Dalc': 1, 'Walc': 2, 'health': 3
})
        if "error" not in res:
            p = models.Prediction(
                student_id=s.id,
                risk_score=res["risk_score"],
                risk_label=res["risk_label"],
                shap_values=res["shap_values"]
            )
            db.add(p)
    
    db.commit()
    print("Database seeded successfully with dummy users and records.")

if __name__ == "__main__":
    seed_db()
