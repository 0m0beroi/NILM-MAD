from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.database import get_db
from app.models import ArcFaultEvent, DeviceNode
from app.schemas import ArcAlertPayload, ArcAlertResponse

router = APIRouter(prefix="/alerts", tags=["Arc Fault Alerts"])

@router.post("/", response_model=ArcAlertResponse)
def report_arc_alert(payload: ArcAlertPayload, db: Session = Depends(get_db)):
    device = db.query(DeviceNode).filter(DeviceNode.mac_address == payload.mac_address).first()
    if not device:
        device = DeviceNode(mac_address=payload.mac_address, name="ESP32-Alert-Node", status="tripped")
        db.add(device)
        db.commit()
        db.refresh(device)
    
    device.status = "tripped" if payload.relay_tripped else "alert"
    device.relay_closed = not payload.relay_tripped

    event = ArcFaultEvent(
        device_id=device.id,
        di_dt_peak=payload.di_dt_peak,
        spectral_entropy=payload.spectral_entropy,
        consecutive_cycles=payload.consecutive_cycles,
        trip_latency_ms=payload.trip_latency_ms,
        relay_tripped=payload.relay_tripped,
        benign_suppressed=payload.benign_suppressed,
        notes=payload.notes
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return ArcAlertResponse(
        id=event.id,
        mac_address=payload.mac_address,
        timestamp=event.timestamp,
        di_dt_peak=event.di_dt_peak,
        spectral_entropy=event.spectral_entropy,
        consecutive_cycles=event.consecutive_cycles,
        trip_latency_ms=event.trip_latency_ms,
        relay_tripped=event.relay_tripped,
        benign_suppressed=event.benign_suppressed,
        notes=event.notes,
        acknowledged=event.acknowledged
    )

@router.get("/", response_model=List[ArcAlertResponse])
def list_arc_alerts(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.query(ArcFaultEvent, DeviceNode.mac_address)\
        .join(DeviceNode, ArcFaultEvent.device_id == DeviceNode.id)\
        .order_by(desc(ArcFaultEvent.timestamp))\
        .limit(limit)\
        .all()

    return [
        ArcAlertResponse(
            id=ev.id,
            mac_address=mac,
            timestamp=ev.timestamp,
            di_dt_peak=ev.di_dt_peak,
            spectral_entropy=ev.spectral_entropy,
            consecutive_cycles=ev.consecutive_cycles,
            trip_latency_ms=ev.trip_latency_ms,
            relay_tripped=ev.relay_tripped,
            benign_suppressed=ev.benign_suppressed,
            notes=ev.notes,
            acknowledged=ev.acknowledged
        )
        for ev, mac in rows
    ]

@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    event = db.query(ArcFaultEvent).filter(ArcFaultEvent.id == alert_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Alert not found")
    event.acknowledged = True
    db.commit()
    return {"status": "success", "message": f"Alert {alert_id} acknowledged"}
