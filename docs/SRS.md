# Software Requirements Specification (SRS)
## IEEE-830 Standard Format
### Project: Edge-AI Enabled Non-Intrusive Appliance Load Monitoring (NILM) and Micro-Arc Fault Detection System

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software, hardware interface, firmware, machine learning, and architectural requirements for the Edge-AI Enabled Non-Intrusive Appliance Load Monitoring (NILM) and Micro-Arc Fault Detection System. It serves as the single source of truth for design, implementation, verification, and capstone evaluation.

### 1.2 Scope
The system operates at the single-point residential service entrance. It acquires synchronized voltage and current telemetry, performs on-chip appliance classification across five domestic categories using an INT8-quantized 1D Depthwise-Separable CNN, executes cycle-by-cycle micro-arc fault detection, actuates a high-speed hardware trip relay within 60 ms upon detecting hazardous arcing, and streams disaggregated energy telemetry to a local dashboard via MQTT over Wi-Fi.

### 1.3 Definitions, Acronyms, and Abbreviations
- **AFE**: Analog Front-End
- **AFDD**: Arc Fault Detection Device
- **CT**: Current Transformer (SCT-013-030)
- **VT**: Voltage Transformer (ZMPT101B)
- **di/dt**: First derivative of current with respect to time (rate of change)
- **GAP**: Global Average Pooling
- **INT8**: 8-bit Integer Quantization
- **ISR**: Interrupt Service Routine
- **MCB / RCCB**: Miniature Circuit Breaker / Residual Current Circuit Breaker
- **NILM**: Non-Intrusive Load Monitoring
- **PTQ**: Post-Training Quantization
- **SLA**: Service Level Agreement
- **TFLM**: TensorFlow Lite for Microcontrollers
- **THD**: Total Harmonic Distortion

### 1.4 References
1. IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.
2. G. W. Hart, "Nonintrusive appliance load monitoring," *Proc. IEEE*, vol. 80, no. 12, pp. 1870–1891, Dec. 1992.
3. J. M. Gillis et al., "Nonintrusive Load Monitoring Using Advanced Deep Learning and High-Frequency V-I Trajectory," *IEEE Trans. Smart Grid*, 2023.
4. F. Xiong et al., "A Novel Arc Fault Detection Method Based on High-Frequency Current Characteristics and Machine Learning," *IEEE Trans. Power Delivery*, 2022.
5. R. David et al., "TensorFlow Lite Micro: Embedded Machine Learning for TinyML Systems," *Proc. MLSys*, 2021.

---

## 2. Overall Description

### 2.1 Product Perspective
The system operates as an edge computing safety and energy management appliance installed in the distribution board. Unlike cloud-dependent smart meters, all safety-critical signal processing, deep learning inferences, and fault interruption decisions occur strictly locally on an ESP32-WROOM-32 microcontroller.

### 2.2 Product Functions
1. Dual-channel synchronized 2 kHz sampling of mains voltage and current.
2. Cycle-by-cycle voltage zero-crossing synchronization.
3. Root-mean-square calculation of $V_{rms}$, $I_{rms}$, active power $P$, reactive power $Q$, and power factor $PF$.
4. Harmonic extraction of $1^{\text{st}}$ through $7^{\text{th}}$ current spectral harmonics via fixed-point DFT.
5. Edge appliance classification into 5 target domestic classes via TinyML 1D-CNN.
6. Micro-arc fault detection via high-pass filtering (> 300 Hz), $di/dt$, and spectral entropy.
7. Sub-60 ms circuit isolation via GPIO26 hardware relay actuation.
8. Benign switching transient gating to eliminate false trips from motor inrush or dimmers.
9. MQTT telemetry publishing (1 Hz) and Web Dashboard presentation.

### 2.3 User Characteristics
- **Homeowner / Facility Manager**: Observes real-time power metrics, appliance breakdowns, and safety alerts.
- **Electrical Safety Officer**: Acknowledges fault events and conducts remote/local breaker reset.
- **Academic Evaluator / Capstone Examiner**: Inspects system timing, ADC linearity, memory footprint, and confusion matrices.

### 2.4 Constraints
1. **Cost Constraint**: Total hardware Bill of Materials (BOM) must remain under ₹2,000.
2. **Memory Constraint**: TFLite Micro tensor arena must occupy less than 50 KB of internal SRAM.
3. **Latency Constraint**: Complete fault detection and physical relay tripping must execute in less than 60 ms (3 cycles of 50 Hz AC).
4. **Hardware Conflict**: ADC2 cannot be utilized due to Wi-Fi driver peripheral sharing; all analog pins are strictly restricted to ADC1 (GPIO34 and GPIO35).
5. **Supply Voltage**: Single-phase 230 V RMS ($\pm 10\%$) at 50 Hz ($\pm 1$ Hz).

---

## 3. Specific Requirements

### 3.1 Functional Requirements
- **FR-1 [Signal Conditioning]**: The AFE shall shift bipolar AC signals to a 1.65 V DC virtual ground and attenuate frequencies above 720 Hz via an RC low-pass anti-aliasing filter.
- **FR-2 [Deterministic Sampling]**: The firmware shall sample ADC1 at exactly 2,000 Hz ($500\ \mu\text{s} \pm 2\ \mu\text{s}$) using hardware timer interrupts and double-buffering.
- **FR-3 [Power Calculation]**: The DSP module shall compute true RMS voltage, true RMS current, active power, reactive power, and displacement power factor over a 256-sample window.
- **FR-4 [Harmonic Decomposition]**: The DSP module shall calculate normalized amplitudes of the $1^{\text{st}}$ through $7^{\text{th}}$ harmonics of current.
- **FR-5 [NILM Classification]**: The TinyML engine shall classify the primary active appliance into one of five domestic classes with an accuracy $\ge 90\%$.
- **FR-6 [Arc Detection]**: The arc detection engine shall identify series micro-arc faults within 3 consecutive 20 ms line cycles.
- **FR-7 [Hardware Interruption]**: Upon 3 consecutive fault cycles, the system shall assert GPIO26 HIGH within 60 ms from initial arc onset.
- **FR-8 [Benign Transient Suppression]**: Harmless switching events (such as motor starting inrush) shall be gated using the current CNN inference label to prevent nuisance trips.
- **FR-9 [Telemetry Transmission]**: Telemetry frames shall be formatted in JSON and published to MQTT topics at a 1-second cadence.
- **FR-10 [Remote Relay Control]**: The system shall subscribe to MQTT control topics to permit authorized breaker reset or remote isolation.

### 3.2 Non-Functional Requirements
- **NFR-1 [Safety]**: Hardware bench testing must incorporate an isolation transformer (230 V to 12 V AC) and Schottky barrier diodes to protect against overvoltage rails.
- **NFR-2 [Inference Latency]**: On-chip 1D-CNN execution must complete in under 25 ms per window on Core 1.
- **NFR-3 [Reliability]**: FreeRTOS tasks shall feature independent stack monitoring and hardware watchdog timers.
- **NFR-4 [Maintainability]**: Modular architecture separating sensing, DSP, edge AI, safety tripping, and communications.
- **NFR-5 [Security]**: Role-Based Access Control on backend APIs and token-authenticated WebSocket feeds.

