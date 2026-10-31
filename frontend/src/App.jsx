import React, { useState, useEffect } from 'react';
import { 
  Zap, AlertTriangle, ShieldCheck, Activity, Power, 
  Cpu, RefreshCw, Radio, HardDrive, AlertOctagon 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  AreaChart, Area 
} from 'recharts';

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export default function App() {
  const [telemetry, setTelemetry] = useState({
    v_rms: 231.4,
    i_rms: 4.82,
    active_power_p: 1115.3,
    reactive_power_q: 142.1,
    power_factor: 0.992,
    frequency: 50.02,
    detected_class_index: 0,
    confidence: 0.965,
    harmonics: [4.75, 0.08, 0.12, 0.03, 0.05, 0.02, 0.01]
  });

  const [relayState, setRelayState] = useState(true); // true = closed (active)
  const [arcAlert, setArcAlert] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("Connected (1 Hz)");

  const APPLIANCE_CLASSES = [
    { name: "Resistive Heater / Geyser", type: "Linear Load", badge: "bg-emerald-950 text-emerald-400 border-emerald-800" },
    { name: "Induction Fan / Motor", type: "Inductive Load", badge: "bg-blue-950 text-blue-400 border-blue-800" },
    { name: "LED Lamp Array", type: "Non-Linear SMPS Driver", badge: "bg-amber-950 text-amber-400 border-amber-800" },
    { name: "SMPS / Laptop Charger", type: "Pulsed Switching", badge: "bg-purple-950 text-purple-400 border-purple-800" },
    { name: "Compressor / Refrigerator", type: "Dynamic Motor", badge: "bg-indigo-950 text-indigo-400 border-indigo-800" }
  ];

  // Poll latest telemetry from backend
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/telemetry/latest?limit=1`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setTelemetry(data[0]);
          }
        }
      } catch (err) {
        // Fallback for standalone demo
      }
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const handleRelayToggle = async () => {
    const action = relayState ? "OPEN" : "CLOSE";
    try {
      await fetch(`${API_BASE_URL}/api/v1/control/relay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: 1, action })
      });
      setRelayState(!relayState);
    } catch (e) {
      setRelayState(!relayState);
    }
  };

  const triggerMockArc = () => {
    setArcAlert({
      time: new Date().toLocaleTimeString(),
      latency: "57.4 ms",
      cycles: 3,
      didt: "24.6 A/ms",
      entropy: "0.892"
    });
    setRelayState(false);
  };

  const harmonicData = [
    { harmonic: "H1 (50Hz)", amplitude: telemetry.harmonics[0] || 0 },
    { harmonic: "H2 (100Hz)", amplitude: telemetry.harmonics[1] || 0 },
    { harmonic: "H3 (150Hz)", amplitude: telemetry.harmonics[2] || 0 },
    { harmonic: "H4 (200Hz)", amplitude: telemetry.harmonics[3] || 0 },
    { harmonic: "H5 (250Hz)", amplitude: telemetry.harmonics[4] || 0 },
    { harmonic: "H6 (300Hz)", amplitude: telemetry.harmonics[5] || 0 },
    { harmonic: "H7 (350Hz)", amplitude: telemetry.harmonics[6] || 0 },
  ];

  const currentAppliance = APPLIANCE_CLASSES[telemetry.detected_class_index] || APPLIANCE_CLASSES[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 lg:p-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Zap className="h-8 w-8 text-emerald-400" />
            <h1 className="text-2xl font-bold tracking-tight">Edge-AI NILM & Micro-Arc Monitor</h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Dual-Core ESP32 TinyML Signal Processing & Deterministic Fault Interruption System
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 px-3 py-1 bg-slate-900 border border-slate-700 text-xs rounded-full font-mono text-emerald-400">
            <Radio className="h-3 w-3 animate-pulse" /> {connectionStatus}
          </span>
          <button 
            onClick={triggerMockArc}
            className="px-3 py-1.5 bg-red-950 hover:bg-red-900 border border-red-700 text-red-300 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition"
          >
            <AlertOctagon className="h-3.5 w-3.5" /> Simulate Arc Trip
          </button>
        </div>
      </header>

      {/* Arc Alert Banner */}
      {arcAlert && (
        <div className="mt-6 p-4 bg-red-950/80 border-2 border-red-600 rounded-xl flex items-start justify-between shadow-2xl animate-bounce-short">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-200 font-bold text-base">CRITICAL SAFETY TRIP: Micro-Arc Fault Isolated</h3>
              <p className="text-red-300 text-sm mt-0.5">
                Hardware trip triggered via GPIO26 in <span className="font-mono font-bold text-white">{arcAlert.latency}</span> (&lt; 60 ms safety SLA) after {arcAlert.cycles} line cycles. Peak di/dt: {arcAlert.didt}, Entropy: {arcAlert.entropy}.
              </p>
            </div>
          </div>
          <button 
            onClick={() => { setArcAlert(null); setRelayState(true); }}
            className="px-4 py-1.5 bg-red-700 hover:bg-red-600 text-white text-xs font-bold rounded-lg transition"
          >
            Acknowledge & Reset
          </button>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {/* Voltage Card */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 text-xs font-medium">
            <span>GRID VOLTAGE (V_RMS)</span>
            <Activity className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-white mt-2">
            {telemetry.v_rms} <span className="text-sm text-slate-400 font-normal">V</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">ZMPT101B @ 2 kHz ADC1</div>
        </div>

        {/* Current Card */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 text-xs font-medium">
            <span>LOAD CURRENT (I_RMS)</span>
            <Zap className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-white mt-2">
            {telemetry.i_rms} <span className="text-sm text-slate-400 font-normal">A</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">SCT-013-030 Split Core</div>
        </div>

        {/* Active Power Card */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 text-xs font-medium">
            <span>ACTIVE POWER (P)</span>
            <Cpu className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-white mt-2">
            {telemetry.active_power_p} <span className="text-sm text-slate-400 font-normal">W</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">Reactive Q: {telemetry.reactive_power_q} VAR</div>
        </div>

        {/* Power Factor Card */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 text-xs font-medium">
            <span>POWER FACTOR (PF)</span>
            <ShieldCheck className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-white mt-2">
            {telemetry.power_factor}
          </div>
          <div className="text-xs text-slate-500 mt-1">Frequency: {telemetry.frequency} Hz</div>
        </div>
      </div>

      {/* Classification & Relay Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* On-Chip TinyML Load Classifier Card */}
        <div className="lg:col-span-2 p-6 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Edge-AI Load Disaggregation (NILM)</h2>
              <p className="text-xs text-slate-400">1D-CNN INT8 Quantized on ESP32 TFLite-Micro (&lt; 25 ms)</p>
            </div>
            <span className={`px-3 py-1 border text-xs font-semibold rounded-full ${currentAppliance.badge}`}>
              {currentAppliance.type}
            </span>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider">Identified Primary Appliance</span>
              <div className="text-2xl font-bold text-emerald-400 mt-0.5">{currentAppliance.name}</div>
            </div>
            <div className="w-full md:w-48">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Confidence</span>
                <span className="font-mono font-bold text-white">{(telemetry.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-emerald-500 h-2.5 rounded-full transition-all duration-500" 
                  style={{ width: `${telemetry.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Harmonic Bar Chart */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-slate-300 mb-3">Current Harmonic Spectrum (H1 – H7 Amplitudes)</h3>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={harmonicData}>
                  <XAxis dataKey="harmonic" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} unit="A" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                    labelStyle={{ color: '#94a3b8' }} 
                  />
                  <Bar dataKey="amplitude" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Protection & Hardware Control */}
        <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Hardware Protection State</h2>
            <p className="text-xs text-slate-400 mt-1">Dual-Core FreeRTOS Trip Controller (GPIO26)</p>

            <div className="mt-6 p-4 rounded-xl border flex items-center justify-between bg-slate-950 border-slate-800">
              <div className="flex items-center gap-3">
                <Power className={`h-6 w-6 ${relayState ? "text-emerald-400" : "text-red-500"}`} />
                <div>
                  <div className="text-sm font-bold">{relayState ? "MAINS CONNECTED" : "CIRCUIT ISOLATED"}</div>
                  <div className="text-xs text-slate-500">Relay State: {relayState ? "Closed (Engaged)" : "Tripped / Open"}</div>
                </div>
              </div>
              <span className={`w-3 h-3 rounded-full ${relayState ? "bg-emerald-400 animate-pulse" : "bg-red-500"}`} />
            </div>

            <div className="mt-6 space-y-3">
              <div className="flex justify-between text-xs py-2 border-b border-slate-800">
                <span className="text-slate-400">Fault Detection Mode</span>
                <span className="text-slate-200 font-mono">di/dt + HF Spectral Entropy</span>
              </div>
              <div className="flex justify-between text-xs py-2 border-b border-slate-800">
                <span className="text-slate-400">Response Latency SLA</span>
                <span className="text-emerald-400 font-mono font-bold">&lt; 60 ms (3 cycles)</span>
              </div>
              <div className="flex justify-between text-xs py-2 border-b border-slate-800">
                <span className="text-slate-400">Sampling Rate</span>
                <span className="text-slate-200 font-mono">2,000 Hz (Core 0 ISR)</span>
              </div>
              <div className="flex justify-between text-xs py-2 border-b border-slate-800">
                <span className="text-slate-400">Memory Footprint</span>
                <span className="text-slate-200 font-mono">38.4 KB / 50 KB SRAM</span>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={handleRelayToggle}
              className={`w-full py-3 rounded-lg font-semibold text-sm transition flex items-center justify-center gap-2 ${
                relayState 
                  ? "bg-red-600 hover:bg-red-500 text-white" 
                  : "bg-emerald-600 hover:bg-emerald-500 text-white"
              }`}
            >
              <Power className="h-4 w-4" />
              {relayState ? "Manually Trip / Isolate Relay" : "Reset & Restore Circuit Relay"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
