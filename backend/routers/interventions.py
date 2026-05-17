from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/interventions", tags=["interventions"])

@router.get("/{student_id}", response_model=List[schemas.InterventionResponse])
def get_interventions(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "student":
        student_record = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if not student_record or student_record.id != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    interventions = db.query(models.Intervention).filter(models.Intervention.student_id == student_id).all()
    return interventions

@router.post("/", response_model=schemas.InterventionResponse)
def assign_intervention(intervention: schemas.InterventionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_role(["faculty", "hod"]))):
    new_intervention = models.Intervention(
        student_id=intervention.student_id,
        type=intervention.type,
        description=intervention.description,
        assigned_by=current_user.id,
        status="assigned"
    )
    db.add(new_intervention)
    db.commit()
    db.refresh(new_intervention)
    return new_intervention

@router.put("/{intervention_id}/status", response_model=schemas.InterventionResponse)
def update_status(intervention_id: int, status_update: schemas.InterventionStatusUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_role(["faculty", "hod"]))):
    intervention = db.query(models.Intervention).filter(models.Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention.status = status_update.status
    db.commit()
    db.refresh(intervention)
    return intervention
