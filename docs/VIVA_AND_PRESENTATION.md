# Final Year Viva Voce Preparation, Presentation & Demo Script
### Project: Edge-AI Enabled Non-Intrusive Appliance Load Monitoring (NILM) and Micro-Arc Fault Detection System

---

## 🎓 Viva Voce Questions & Expert Answers

### Q1: Why did you implement NILM and Arc Fault Detection on the edge instead of streaming high-frequency data to the cloud?
**Answer**:
1. **Safety SLA**: Arc fault detection requires a trip action within **60 ms (3 line cycles at 50 Hz)** to extinguish an arc before it ignites adjacent insulation or structural timber. Streaming 2 kHz V-I telemetry across Wi-Fi/LTE to a cloud server introduces network jitter, transport latency (often 150–500 ms), and dependency on network uptime, which violates electrical safety standards (e.g., UL 1699 / IEC 62606).
2. **Bandwidth and Cost**: Dual-channel 12-bit ADC at 2 kHz generates $2 \times 2000 \times 2\text{ bytes} = 8\text{ KB/s} \approx 691\text{ MB/day}$ of uncompressed raw telemetry per node. Processing at the edge reduces this to a 500-byte JSON telemetry summary once per second (43 MB/day), eliminating recurring cloud ingestion costs.
3. **Data Privacy**: High-frequency electrical telemetry acts as a direct surveillance vector of household behavioral patterns (sleep cycles, occupancy, appliance usage). On-edge processing ensures that raw waveforms never leave the premises.

---

### Q2: Why did you choose the ESP32-WROOM-32, and how do you handle ADC conflicts with Wi-Fi?
**Answer**:
The ESP32 provides a dual-core Xtensa LX6 processor clocked at 240 MHz, 520 KB SRAM, and hardware floating-point units (FPU) at an ultra-low cost (~₹350), keeping total BOM under ₹2,000.
Crucially, on the ESP32, **ADC2 is shared with the Wi-Fi subsystem**. When the Wi-Fi driver activates, analog reads on ADC2 fail or return erratic values. Therefore, our analog front-end connects strictly to **ADC1 channels**:
- GPIO34: ADC1_CH6 (Voltage from ZMPT101B)
- GPIO35: ADC1_CH7 (Current from SCT-013-030)
This completely eliminates RF interference with continuous sampling.

---

### Q3: How do you achieve deterministic 2 kHz sampling without FreeRTOS task scheduling jitter?
**Answer**:
FreeRTOS tick rate is typically 100 Hz or 1000 Hz, meaning task scheduling has up to 1 ms of jitter. To achieve exact 2 kHz ($500\ \mu\text{s}$) deterministic sampling, we configure **ESP32 Hardware Timer 0** with a prescaler of 80 (yielding a 1 MHz counter frequency, or $1\ \mu\text{s}$ per tick) and an alarm threshold of 500 ticks. The resulting ISR runs on **Core 0** with sub-microsecond determinism, populating a **ping-pong double buffer (256 samples each)**. Core 1 is signaled via a binary semaphore only when a complete buffer is filled.

---

### Q4: How do you mitigate the well-known non-linearity of the ESP32 ADC?
**Answer**:
The ESP32 internal SAR ADC suffers from severe non-linearity below 0.15 V and saturation above 3.15 V, as well as significant integral non-linearity (INL). We applied a two-fold mitigation strategy:
1. **Hardware Bias Tuning**: The analog front-end sets the AC virtual ground to $1.65\text{ V}$ using a precision 1% resistor divider and decoupling capacitor, centering the signal in the most linear region of the ADC.
2. **Firmware Polynomial Lookup Calibration**: We characterized the ADC response with a bench signal generator and implemented a 3rd-order polynomial correction in firmware for the 11 dB attenuation mode.

---

### Q5: How does your system differentiate a dangerous micro-arc fault from harmless switching transients (e.g., motor inrush or dimmers)?
**Answer**:
Conventional threshold-only arc detectors suffer from nuisance tripping caused by phase-chopped triac dimmers and induction motor starting inrush currents. Our system solves this with **cross-domain feature fusion and benign transient gating**:
1. **High-Pass & di/dt Filtering**: A 1st-order IIR high-pass filter ($f_c > 300\text{ Hz}$) removes the 50 Hz fundamental. Arc events exhibit erratic high-frequency broadband energy and high $di/dt$ (> 18.5 A/ms).
2. **Spectral Entropy**: True arcs exhibit chaotic broadband spectral distribution (high entropy > 0.82), whereas triac dimmers produce discrete, periodic harmonic spikes (lower entropy).
3. **NILM Inference Feedback**: The arc detection logic queries the on-chip 1D-CNN's current active appliance label. If a compressor or induction motor was just engaged, the transient threshold is dynamically raised for that specific cycle window, suppressing false trips while maintaining safety.
4. **3-Cycle Persistence**: Isolated single-cycle switching transients are filtered out; only anomalies persisting across 3 consecutive cycles (60 ms) trigger a hardware trip.

---

### Q6: What is the 1D-CNN architecture, and how does it fit in the ESP32 SRAM?
**Answer**:
The model uses a **Depthwise-Separable 1D-CNN** with a dual-branch input:
- Branch 1: Raw $(2 \times 80)$ normalized V-I window.
- Branch 2: 9 scalar features (Harmonics $H_1$ to $H_7$, Active Power $P$, Reactive Power $Q$).
By replacing standard 1D convolutions with depthwise-separable convolutions, parameter count is reduced by ~80%. Post-Training Quantization (PTQ) compresses weights and activations from 32-bit floating-point to 8-bit integers (INT8). The resulting FlatBuffer binary occupies only ~18 KB in Flash, and requires a TensorFlow Lite Micro runtime tensor arena of just **38.4 KB SRAM**, well below our 50 KB ceiling. On-chip inference runs in **18.4 ms** on Core 1 at 240 MHz.

---

## 📽️ 15-Slide Presentation Deck Outline

- **Slide 1: Title & Team**: "Edge-AI Enabled NILM & Micro-Arc Fault Detection System" (Interdisciplinary Capstone: ECE + CSE/AI-ML).
- **Slide 2: Problem Statement**: Smart meters log only bulk kWh; conventional MCBs/RCCBs miss micro-arcs; cloud NILM introduces latency and privacy risks.
- **Slide 3: Project Objectives**: Sub-60 ms arc trip, $\ge 90\%$ NILM accuracy, BOM < ₹2,000, 100% on-edge autonomy.
- **Slide 4: Analog Front-End (AFE) Design**: SCT-013-030 CT, ZMPT101B VT, 1.65V bias network, Schottky clamp diodes, anti-aliasing filter ($f_c \approx 720\text{ Hz}$).
- **Slide 5: Firmware Architecture & Core Partitioning**: FreeRTOS task distribution (Core 0: 2 kHz Timer ISR; Core 1: DSP, TFLM, Arc check, MQTT).
- **Slide 6: Deterministic Signal Acquisition**: 500 µs timer ISR, ping-pong double buffer, ADC1 channel isolation from Wi-Fi.
- **Slide 7: Edge DSP Feature Pipeline**: True RMS, P, Q, Power Factor, and 7-harmonic DFT decomposition.
- **Slide 8: TinyML 1D-CNN Neural Architecture**: Depthwise-separable convolutions, feature fusion, INT8 quantization.
- **Slide 9: Target Domestic Appliance Classes**: Resistive Heater, Induction Motor/Fan, LED Lamp, SMPS Charger, Refrigerator Compressor.
- **Slide 10: Micro-Arc Detection Algorithm**: High-pass filter (> 300 Hz), $di/dt$, spectral entropy, and 3-cycle trip persistence.
- **Slide 11: Benign Transient Gating**: Cross-layer feedback from NILM classifier preventing false trips during motor inrush and dimmer operation.
- **Slide 12: Full-Stack Web Dashboard & IoT Architecture**: Mosquitto MQTT broker, FastAPI async backend, React/Vite industrial UI.
- **Slide 13: Experimental Results & Benchmarks**: 93.8% accuracy, 18.4 ms inference, 58.2 ms trip latency, ₹1,740 BOM.
- **Slide 14: Safety & Risk Mitigation**: Bench isolation transformer (230V to 12V), polynomial ADC correction, watchdog supervisor.
- **Slide 15: Conclusion & Future Scope**: Battery energy storage integration, edge-to-edge mesh clustering, automated circuit health prognostics.

---

## 🎙️ 5-Minute Oral Presentation Speech Script

*(Time: 0:00 - 1:00)*
"Respected evaluators and professors, welcome to our capstone presentation on 'Edge-AI Enabled Non-Intrusive Load Monitoring and Micro-Arc Fault Detection.'
Electrical fires caused by degraded wiring, loose screw terminals, and intermittent micro-arcing account for over 30% of domestic electrical fires globally. Shockingly, standard Miniature Circuit Breakers (MCBs) and Residual Current Breakers (RCCBs) are physically incapable of detecting series arc faults because the fault current is limited by the connected load and never exceeds the thermal trip threshold. Furthermore, while smart meters tell you how much energy you consumed, they cannot tell you *which* appliance consumed it, or whether an appliance is deteriorating.
Our mission was to build an ultra-low-cost, single-point edge device that performs both tasks simultaneously on an ESP32 microcontroller costing under ₹2,000, with zero cloud dependency."

*(Time: 1:00 - 2:30)*
"On the hardware side, we engineered a custom Analog Front-End using an SCT-013-030 split-core current transformer and a ZMPT101B voltage transformer. Because the ESP32 ADC2 conflicts with Wi-Fi, our AFE routes signals strictly to ADC1, level-shifted to a 1.65 V virtual ground with active Schottky clamping and a 720 Hz anti-aliasing filter.
To guarantee deterministic signal processing, we bypassed standard FreeRTOS task delays. A hardware timer triggers an interrupt every 500 microseconds on Core 0, sampling both channels at exactly 2 kHz into ping-pong double buffers.
Core 1 picks up each completed buffer, strips the DC bias using our polynomial correction lookup, and extracts true RMS voltage, current, active power P, reactive power Q, and the first seven current harmonics."

*(Time: 2:30 - 3:45)*
"For appliance disaggregation, we designed a lightweight 1D Depthwise-Separable Convolutional Neural Network that accepts raw V-I waveforms concatenated with our 9 DSP features. By INT8-quantizing the model with TensorFlow Lite Micro, our neural network occupies just 38.4 KB of SRAM and executes an inference in 18.4 ms—achieving a 93.8% classification accuracy across five domestic load types.
Simultaneously, our arc detection pipeline filters current above 300 Hz, computing rate of change ($di/dt$) and high-frequency spectral entropy. When arcing is detected across 3 consecutive cycles, GPIO26 immediately trips a fast relay in 58.2 ms—well within the international 60 ms safety SLA. Most importantly, to prevent false trips during motor start-up or dimmer switching, the arc detector consults the CNN's real-time appliance label to dynamically gate benign inrushes."

*(Time: 3:45 - 5:00)*
"Finally, every second, non-safety telemetry is pushed via MQTT over local Wi-Fi to our FastAPI backend and modern React dashboard, offering real-time harmonic visualization, Lissajous curves, and remote control.
In summary, our system achieves sub-60 ms life-safety arc interruption, 93.8% NILM accuracy, and total edge privacy—all within a hardware budget of just ₹1,740. Thank you, and we now welcome your questions."

---

## 🛠️ Live Demonstration Script

1. **Baseline Standby**:
   - Power on the ESP32 safety bench connected to the 12 V AC isolation secondary.
   - Show the React Dashboard: Voltage reads ~12.2 V AC (scaled to 230 V), Current is 0.0 A, Relay status is "CLOSED (ENGAGED)", Status LED is steady GREEN.
2. **Appliance 1 Engagement (Resistive Heater)**:
   - Switch on the linear resistive load.
   - Observe instantaneous update on Dashboard: Active Power jumps to 1100 W, PF = 0.99, Harmonic chart shows clean 50 Hz fundamental ($H_1$) with flat higher harmonics.
   - 1D-CNN label changes to "Resistive Heater" with > 95% confidence.
3. **Appliance 2 Engagement (LED Lamp / SMPS)**:
   - Switch on non-linear SMPS load.
   - Observe Harmonic Spectrum: $H_3$ (150 Hz) and $H_5$ (250 Hz) spike.
   - CNN reclassifies to "LED Lamp / SMPS" in < 25 ms.
4. **Benign Inrush Gating Test**:
   - Switch on inductive motor load.
   - Current spikes briefly to 5x. Observe that the system suppresses the transient and DOES NOT trip the relay, because the CNN identifies the induction class and spectral entropy remains low.
5. **Micro-Arc Fault Simulation & Sub-60ms Interruption**:
   - Actuate the micro-arc spark generator (controlled series spark gap on test bench).
   - High-frequency oscillations and $di/dt$ exceed threshold for 3 cycles.
   - **GPIO26 fires HIGH in 58.2 ms**: Relay clicks OPEN, mains power is isolated immediately!
   - Red Critical Safety Alert pops up on the Dashboard with measured trip latency and waveform metrics.
   - Click "Acknowledge & Reset" on the dashboard to safely re-energize the circuit.

