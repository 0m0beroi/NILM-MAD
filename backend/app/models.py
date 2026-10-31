from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="operator")  # admin, operator, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DeviceNode(Base):
    __tablename__ = "device_nodes"

    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(150), default="Main Electrical Distribution Board")
    ip_address = Column(String(45), nullable=True)
    status = Column(String(30), default="offline") # online, offline, tripped
    relay_closed = Column(Boolean, default=True)
    firmware_version = Column(String(20), default="1.0.0")
    last_heartbeat = Column(DateTime, nullable=True)

    telemetries = relationship("TelemetryLog", back_populates="device", cascade="all, delete-orphan")
    arc_events = relationship("ArcFaultEvent", back_populates="device", cascade="all, delete-orphan")

class ApplianceClass(Base):
    __tablename__ = "appliance_classes"

    id = Column(Integer, primary_key=True, index=True)
    class_index = Column(Integer, unique=True, nullable=False) # 0 to 4
    name = Column(String(100), nullable=False) # e.g. Resistive Heater, Induction Fan, LED Lamp, SMPS, Compressor
    category = Column(String(50), nullable=False) # Linear, Inductive, Non-linear
    base_power_watts = Column(Float, nullable=False)
    harmonic_profile = Column(Text, nullable=True) # JSON or description

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("device_nodes.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    v_rms = Column(Float, nullable=False)
    i_rms = Column(Float, nullable=False)
    active_power_p = Column(Float, nullable=False)
    reactive_power_q = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=False)
    frequency = Column(Float, default=50.0)
    
    # TinyML Inference Output
    detected_class_index = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # 1st to 7th Harmonic Amplitudes (A)
    h1 = Column(Float, default=0.0)
    h2 = Column(Float, default=0.0)
    h3 = Column(Float, default=0.0)
    h4 = Column(Float, default=0.0)
    h5 = Column(Float, default=0.0)
    h6 = Column(Float, default=0.0)
    h7 = Column(Float, default=0.0)

    device = relationship("DeviceNode", back_populates="telemetries")

class ArcFaultEvent(Base):
    __tablename__ = "arc_fault_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("device_nodes.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    di_dt_peak = Column(Float, nullable=False)
    spectral_entropy = Column(Float, nullable=False)
    consecutive_cycles = Column(Integer, default=3)
    trip_latency_ms = Column(Float, default=58.2)
    relay_tripped = Column(Boolean, default=True)
    benign_suppressed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)

    device = relationship("DeviceNode", back_populates="arc_events")

