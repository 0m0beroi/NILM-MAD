from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.models import ApplianceClass

router = APIRouter(prefix="/appliances", tags=["Appliances"])

class ApplianceSchema(BaseModel):
    id: int
    class_index: int
    name: str
    category: str
    base_power_watts: float
    harmonic_profile: str

    class Config:
        from_attributes = True

DEFAULT_APPLIANCES = [
    {"class_index": 0, "name": "Resistive Heater / Geyser", "category": "Linear / Resistive", "base_power_watts": 1500.0, "harmonic_profile": "Unity PF (~0.99), Near zero harmonic distortion"},
    {"class_index": 1, "name": "Induction Fan / Motor", "category": "Inductive", "base_power_watts": 75.0, "harmonic_profile": "Lagging PF (~0.75-0.85), Phase shifted fundamental"},
    {"class_index": 2, "name": "LED Lamp", "category": "Non-linear / Driver", "base_power_watts": 15.0, "harmonic_profile": "High 3rd (60%) and 5th (35%) harmonics, low power"},
    {"class_index": 3, "name": "SMPS / Laptop Charger", "category": "Non-linear / Switching", "base_power_watts": 65.0, "harmonic_profile": "Pulsed crest factor > 2.5, rich odd harmonic spectrum"},
    {"class_index": 4, "name": "Compressor / Refrigerator", "category": "Inductive / Dynamic", "base_power_watts": 180.0, "harmonic_profile": "Inrush surge (4-6x), dynamic lagging displacement"}
]

@router.get("/", response_model=List[ApplianceSchema])
def list_appliances(db: Session = Depends(get_db)):
    appliances = db.query(ApplianceClass).order_by(ApplianceClass.class_index).all()
    if not appliances:
        for app_data in DEFAULT_APPLIANCES:
            app = ApplianceClass(**app_data)
            db.add(app)
        db.commit()
        appliances = db.query(ApplianceClass).order_by(ApplianceClass.class_index).all()
    return appliances
