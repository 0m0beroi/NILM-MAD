from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DeviceNode
from app.schemas import RelayControlRequest
from app.services.mqtt_service import mqtt_manager

router = APIRouter(prefix="/control", tags=["Hardware Relay Control"])

@router.post("/relay")
def control_relay(req: RelayControlRequest, db: Session = Depends(get_db)):
    device = db.query(DeviceNode).filter(DeviceNode.id == req.device_id).first()
    if not device:
        # Create default device if not yet registered
        device = DeviceNode(id=req.device_id, mac_address="ESP32-BENCH-01", name="ESP32-Bench-Relay")
        db.add(device)
        db.commit()
        db.refresh(device)

    if req.action == "CLOSE":
        device.relay_closed = True
        device.status = "online"
    elif req.action == "OPEN":
        device.relay_closed = False
        device.status = "isolated"
    elif req.action == "RESET":
        device.relay_closed = True
        device.status = "online"

    db.commit()
    db.refresh(device)

    # Publish to MQTT topic if broker available
    mqtt_manager.publish_relay_command(device.mac_address, req.action)

    return {
        "status": "success",
        "action": req.action,
        "device_id": device.id,
        "mac_address": device.mac_address,
        "relay_closed": device.relay_closed,
        "device_status": device.status
    }
