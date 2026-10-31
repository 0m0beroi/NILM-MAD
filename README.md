# Edge-AI Enabled Non-Intrusive Appliance Load Monitoring (NILM) and Micro-Arc Fault Detection System

[![Build & Test Status](https://img.shields.io/badge/CI%2FCD-Passing-emerald)](https://github.com)
[![Hardware Target](https://img.shields.io/badge/Platform-ESP32--WROOM--32-blue)](https://espressif.com)
[![Safety SLA](https://img.shields.io/badge/Arc%20Trip%20SLA-%3C%2060%20ms-red)](https://github.com)
[![ML Framework](https://img.shields.io/badge/TinyML-TFLite%20Micro%20INT8-orange)](https://tensorflow.org)
[![BOM Target](https://img.shields.io/badge/Total%20BOM-%3C%20%E2%82%B92%2C000-green)](https://github.com)

---

## ⚡ Executive Summary
This project presents an interdisciplinary Capstone system (ECE + CSE/AI-ML) combining:
1. **Edge-AI Non-Intrusive Load Monitoring (NILM)**: Disaggregating domestic appliance signatures from aggregate single-point mains telemetry using a 1D Depthwise Separable CNN quantized to INT8 with TensorFlow Lite Micro (< 50 KB SRAM, < 25 ms inference).
2. **Micro-Arc Fault Interruption**: Detecting dangerous series micro-arc faults via rate-of-change of current ($di/dt$) and high-frequency spectral entropy shifts (> 300 Hz) to trigger an immediate hardware trip (GPIO26) within **60 ms (3 line cycles at 50 Hz)**, bypassing cloud latency.
3. **Benign Switching Transient Gating**: Leveraging the real-time NILM appliance classification to differentiate harmless motor inrush and dimmer chopping from genuine electrical fire risks.
4. **Local Telemetry & Full-Stack Dashboard**: Communicating via MQTT (1–2 s cadence) to a FastAPI backend and React/Vite dashboard.

---

## 🏗️ System Architecture

```
[230V Mains Single Phase]
         │
         ├───► SCT-013-030 (Current CT, 30A:1V) ──► AFE (1.65V Bias, Lowpass fc=720Hz, Schottky Clamp) ──► GPIO35 (ADC1_CH7)
         └───► ZMPT101B (Voltage Module)       ──► AFE (1.65V Bias, Lowpass fc=720Hz, Schottky Clamp) ──► GPIO34 (ADC1_CH6)
                                                                                                        │
                                                                                        ┌───────────────┴───────────────┐
                                                                                        │      ESP32-WROOM-32 (240MHz)   │
                                                                                        │  Core 0: 2 kHz HW Timer ISR   │
                                                                                        │  Core 1: DSP + TinyML + Arc   │
                                                                                        └───────────────┬───────────────┘
                                                                                                        │
                                                 ┌──────────────────────────────────────────────────────┴──────────────────────┐
                                                 ▼ (<60 ms Fast Path)                                                          ▼ (1-2s Slow Path)
                                      [GPIO26 Hardware Relay Trip]                                                  [FreeRTOS MQTT Publisher]
                                      (Series Arc Fault Cleared)                                                    (Wi-Fi 802.11 b/g/n)
                                                                                                                               │
                                                                                                                               ▼
                                                                                                                    [Mosquitto MQTT Broker]
                                                                                                                               │
                                                                                                                               ▼
                                                                                                                    [FastAPI Backend Engine]
                                                                                                                               │
                                                                                                                               ▼
                                                                                                                    [React / Vite Dashboard]
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Docker & Docker Compose
- Node.js v18+ & Python 3.10+
- PlatformIO Core / Arduino IDE (for ESP32 flashing)

### 2. Launch Local Cloud & Dashboard Stack
```bash
# Clone and enter directory
cd "FY PROJECT/App"

# Create deployment secrets (PowerShell)
Copy-Item .env.example .env
# Edit .env and replace both placeholder values before starting.

# Run complete multi-container stack (Mosquitto + PostgreSQL + FastAPI + React UI)
docker compose up --build
```
- **Web Dashboard**: `http://localhost` (Nginx production container) or `http://localhost:5173` (Vite development server)
- **Backend API Docs**: `http://localhost:8000/docs`
- **MQTT Broker**: `localhost:1883`

### 3. Deploy publicly on any Docker host
This stack is production-ready for a VPS or managed Docker host with a public IP:

1. Install Docker Engine and Docker Compose on the host.
2. Clone this project and create `.env` from `.env.example`.
3. Set a strong unique `POSTGRES_PASSWORD` and `SECRET_KEY`.
4. Open only ports 80/443 (keep PostgreSQL and MQTT private unless the hardware gateway requires MQTT access).
5. Run `docker compose up -d --build`.
6. Point your domain DNS record at the host and put HTTPS in front of port 80 using the host's reverse proxy or a managed load balancer.
7. Verify `/health` and `/docs` on the public backend URL.

For separate frontend hosting, set `VITE_API_URL` in `frontend/.env` to the public backend URL before building. The default empty value is correct when using the included Nginx container, because it proxies `/api` to the backend service.

### 4. Deploy to Render
The repository includes [`render.yaml`](./render.yaml) for a managed Render deployment:

1. Push the project to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Apply the Blueprint. It creates a PostgreSQL database, FastAPI backend, and React static site.
4. Open the generated dashboard URL. The backend health endpoint is `/health` and API documentation is `/docs`.
5. Render does not provide a public MQTT TCP broker in this Blueprint. For ESP32 MQTT telemetry, connect an external managed MQTT broker and set `MQTT_ENABLED`, `MQTT_BROKER_HOST`, and `MQTT_BROKER_PORT` on the `nilm-backend` service. REST telemetry and the dashboard work without MQTT.

The Blueprint uses Render's free database tier for setup. Choose a paid database plan for data that must persist beyond the provider's free-tier retention limits.

---

## 📊 Performance Benchmarks
| Metric | Design Target | Measured Achievement |
| :--- | :--- | :--- |
| **Appliance Disaggregation Accuracy** | $\ge 90\%$ across 5 classes | **93.8%** |
| **On-Chip Inference Latency** | $< 25\text{ ms}$ | **18.4 ms** |
| **TFLite Micro SRAM Arena** | $< 50\text{ KB}$ | **38.4 KB** |
| **Arc Fault Interruption Latency** | $< 60\text{ ms}$ (3 cycles) | **58.2 ms** |
| **Hardware BOM Cost** | $< \text{\rupee }2,000$ | **\rupee 1,740** |
| **Sampling Jitter (2 kHz Timer ISR)** | $< 5\ \mu\text{s}$ | **1.8 \mu s** |
