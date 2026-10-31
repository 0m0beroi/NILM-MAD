from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.database import get_db
from app.models import TelemetryLog, DeviceNode
from app.schemas import TelemetryPayload, TelemetryResponse
from app.services.mqtt_service import ws_manager

router = APIRouter(prefix="/telemetry", tags=["Telemetry & Disaggregation"])

@router.post("/", response_model=TelemetryResponse)
def ingest_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    device = db.query(DeviceNode).filter(DeviceNode.mac_address == payload.mac_address).first()
    if not device:
        device = DeviceNode(
            mac_address=payload.mac_address,
            name=f"ESP32-Node-{payload.mac_address[-4:]}",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    
    h = payload.harmonics + [0.0] * (7 - len(payload.harmonics))
    telemetry = TelemetryLog(
        device_id=device.id,
        v_rms=payload.v_rms,
        i_rms=payload.i_rms,
        active_power_p=payload.active_power_p,
        reactive_power_q=payload.reactive_power_q,
        power_factor=payload.power_factor,
        frequency=payload.frequency,
        detected_class_index=payload.detected_class_index,
        confidence=payload.confidence,
        h1=h[0], h2=h[1], h3=h[2], h4=h[3], h5=h[4], h6=h[5], h7=h[6]
    )
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    
    return TelemetryResponse(
        id=telemetry.id,
        mac_address=payload.mac_address,
        timestamp=telemetry.timestamp,
        v_rms=telemetry.v_rms,
        i_rms=telemetry.i_rms,
        active_power_p=telemetry.active_power_p,
        reactive_power_q=telemetry.reactive_power_q,
        power_factor=telemetry.power_factor,
        frequency=telemetry.frequency,
        detected_class_index=telemetry.detected_class_index,
        confidence=telemetry.confidence,
        harmonics=[telemetry.h1, telemetry.h2, telemetry.h3, telemetry.h4, telemetry.h5, telemetry.h6, telemetry.h7]
    )

@router.get("/latest", response_model=List[TelemetryResponse])
def get_latest_telemetry(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.query(TelemetryLog, DeviceNode.mac_address)\
        .join(DeviceNode, TelemetryLog.device_id == DeviceNode.id)\
        .order_by(desc(TelemetryLog.timestamp))\
        .limit(limit)\
        .all()
    
    response = []
    for log, mac in rows:
        response.append(TelemetryResponse(
            id=log.id,
            mac_address=mac,
            timestamp=log.timestamp,
            v_rms=log.v_rms,
            i_rms=log.i_rms,
            active_power_p=log.active_power_p,
            reactive_power_q=log.reactive_power_q,
            power_factor=log.power_factor,
            frequency=log.frequency,
            detected_class_index=log.detected_class_index,
            confidence=log.confidence,
            harmonics=[log.h1, log.h2, log.h3, log.h4, log.h5, log.h6, log.h7]
        ))
    return response

@router.websocket("/ws")
async def websocket_telemetry_stream(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
