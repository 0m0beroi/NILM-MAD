from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Edge-AI NILM & Micro-Arc Fault Detection"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecret_capstone_jwt_signing_key_9384729384729"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # SQLite is convenient for development; use PostgreSQL in production.
    DATABASE_URL: str = "sqlite:///./nilm_system.db"
    
    # MQTT Broker Configuration
    MQTT_ENABLED: bool = False # Set True when Mosquitto broker is active
    MQTT_BROKER_HOST: str = "127.0.0.1"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_TELEMETRY: str = "esp32/nilm/telemetry"
    MQTT_TOPIC_ALERTS: str = "esp32/nilm/alerts"
    MQTT_TOPIC_RELAY_CONTROL: str = "esp32/nilm/control/relay"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value

settings = Settings()
