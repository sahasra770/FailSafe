from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# Student Schemas
class StudentBase(BaseModel):
    roll_no: str
    department: str
    semester: int
    cgpa: float

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    user_id: int
    user: UserResponse

    model_config = {"from_attributes": True}

# Prediction Schemas
class PredictionResponse(BaseModel):
    id: int
    student_id: int
    risk_score: float
    risk_label: str
    predicted_on: datetime
    shap_values: Dict[str, Any]

    model_config = {"from_attributes": True}

# Intervention Schemas
class InterventionCreate(BaseModel):
    student_id: int
    type: str
    description: str

class InterventionStatusUpdate(BaseModel):
    status: str

class InterventionResponse(BaseModel):
    id: int
    student_id: int
    type: str
    description: str
    assigned_by: int
    status: str

    model_config = {"from_attributes": True}