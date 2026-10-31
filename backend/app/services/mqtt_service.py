import json
import logging
import asyncio
import threading
from typing import Set
from fastapi import WebSocket
import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger("MQTTService")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        for dead in disconnected:
            self.active_connections.discard(dead)

ws_manager = ConnectionManager()

class MQTTClientManager:
    def __init__(self):
        self.client = None
        self.loop = None
        self.is_connected = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT} (rc={rc})")
        self.is_connected = True
        client.subscribe(settings.MQTT_TOPIC_TELEMETRY)
        client.subscribe(settings.MQTT_TOPIC_ALERTS)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            topic = msg.topic
            event = {"topic": topic, "data": payload}
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(ws_manager.broadcast_json(event), self.loop)
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def _background_worker(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fastapi_backend_nilm")
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=30)
            self.client.loop_forever()
        except Exception as e:
            logger.info(f"MQTT Broker offline (standalone mode active): {e}")

    def start(self, event_loop):
        self.loop = event_loop
        if settings.MQTT_ENABLED:
            thread = threading.Thread(target=self._background_worker, daemon=True)
            thread.start()
        else:
            logger.info("Standalone mode: MQTT disabled. Telemetry accepted via REST & WebSocket.")

    def publish_relay_command(self, mac_address: str, command: str):
        if self.client and self.is_connected:
            try:
                payload = json.dumps({"mac": mac_address, "command": command})
                self.client.publish(settings.MQTT_TOPIC_RELAY_CONTROL, payload, qos=1)
            except Exception as e:
                logger.warning(f"Could not publish relay control via MQTT: {e}")

    def stop(self):
        if self.client and self.is_connected:
            try:
                self.client.disconnect()
            except Exception:
                pass

mqtt_manager = MQTTClientManager()
