import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import engine, Base
from app.services.mqtt_service import mqtt_manager
from app.routes import auth, telemetry, appliances, alerts, relay

# Ensure the schema is available for ASGI clients that do not run lifespan
# events (for example, lightweight API tests).
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start MQTT background worker if enabled
    loop = asyncio.get_running_loop()
    mqtt_manager.start(loop)
    
    yield
    
    mqtt_manager.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST & Real-time WebSocket API for Edge-AI Non-Intrusive Appliance Load Monitoring and Micro-Arc Fault Detection.",
    lifespan=lifespan
)

# CORS Middleware (allows browser frontend on any local port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(appliances.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(relay.router, prefix=settings.API_V1_STR)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "safety_target": "Arc trip < 60 ms",
        "sampling_rate": "2 kHz ADC1 DMA"
    }

@app.get("/health")
def readiness_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
