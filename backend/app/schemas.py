from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: Optional[str] = "operator"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DeviceBase(BaseModel):
    mac_address: str
    name: str
    location: Optional[str] = "Main Distribution Board"

class DeviceCreate(DeviceBase):
    pass

class DeviceResponse(DeviceBase):
    id: int
    status: str
    relay_closed: bool
    firmware_version: str
    last_heartbeat: Optional[datetime]

    class Config:
        from_attributes = True

class TelemetryPayload(BaseModel):
    mac_address: str
    v_rms: float = Field(..., description="Root-Mean-Square Voltage in Volts")
    i_rms: float = Field(..., description="Root-Mean-Square Current in Amperes")
    active_power_p: float = Field(..., description="Real Power in Watts")
    reactive_power_q: float = Field(..., description="Reactive Power in VAR")
    power_factor: float = Field(..., description="Power Factor (-1.0 to 1.0)")
    frequency: float = 50.0
    detected_class_index: int = Field(..., ge=0, le=4)
    confidence: float = Field(..., ge=0.0, le=1.0)
    harmonics: List[float] = Field(default_factory=lambda: [0.0]*7, description="H1 to H7 Amplitudes")

class TelemetryResponse(TelemetryPayload):
    id: int
    timestamp: datetime
    appliance_name: Optional[str] = None

    class Config:
        from_attributes = True

class ArcAlertPayload(BaseModel):
    mac_address: str
    di_dt_peak: float
    spectral_entropy: float
    consecutive_cycles: int = 3
    trip_latency_ms: float
    relay_tripped: bool = True
    benign_suppressed: bool = False
    notes: Optional[str] = None

class ArcAlertResponse(ArcAlertPayload):
    id: int
    timestamp: datetime
    acknowledged: bool

    class Config:
        from_attributes = True

class RelayControlRequest(BaseModel):
    device_id: int
    action: str = Field(..., pattern="^(CLOSE|OPEN|RESET)$") # CLOSE (normal), OPEN (isolate), RESET (clear arc trip)

