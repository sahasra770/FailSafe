from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import auth, students, predictions, interventions, dashboard

# Create database tables
models.Base.metadata.create_all(bind=engine)
# Auto-seed if database is empty
from database import SessionLocal
def auto_seed():
    db = SessionLocal()
    if db.query(models.User).count() == 0:
        import seed
        seed.seed_db()
    db.close()

auto_seed()

app = FastAPI(
    title="FAILSAFE API",
    description="Student failure prediction and intervention system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev. Restrict in prod.
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the FAILSAFE API"}
