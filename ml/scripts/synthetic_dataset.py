"""
Synthetic NILM & Arc-Fault Dataset Generator
Generates realistic domestic voltage and current waveforms at 2 kHz (40 samples per 50 Hz cycle).
Includes 5 domestic appliance load classes and series micro-arc anomalies.
"""

import numpy as np

SAMPLE_RATE = 2000 # 2 kHz
FREQ = 50.0        # 50 Hz
CYCLE_SAMPLES = int(SAMPLE_RATE / FREQ) # 40 samples per cycle
WINDOW_CYCLES = 2   # 2 cycles = 80 samples
WINDOW_SIZE = CYCLE_SAMPLES * WINDOW_CYCLES # 80 samples

def generate_voltage(num_samples=WINDOW_SIZE, noise_std=0.01):
    t = np.linspace(0, num_samples / SAMPLE_RATE, num_samples, endpoint=False)
    v = 230.0 * np.sqrt(2) * np.sin(2 * np.pi * FREQ * t)
    # Slight grid voltage harmonic distortion (3rd harmonic at 1.5%)
    v += (230.0 * np.sqrt(2) * 0.015) * np.sin(2 * np.pi * 3 * FREQ * t)
    v += np.random.normal(0, noise_std * 230.0, num_samples)
    return v

def generate_appliance_sample(class_index, noise_level=0.02):
    t = np.linspace(0, WINDOW_SIZE / SAMPLE_RATE, WINDOW_SIZE, endpoint=False)
    v = generate_voltage()
    
    if class_index == 0:
        # Class 0: Resistive Heater / Geyser (Pure active power, ~1500W, linear unity PF)
        i_peak = (1500.0 / 230.0) * np.sqrt(2)
        i = i_peak * np.sin(2 * np.pi * FREQ * t)
    
    elif class_index == 1:
        # Class 1: Induction Fan / Motor (~75W, lagging phase ~35 deg)
        i_peak = (75.0 / (230.0 * 0.8)) * np.sqrt(2)
        phase_lag = np.radians(36.8) # cos(phi) = 0.80
        i = i_peak * np.sin(2 * np.pi * FREQ * t - phase_lag)
    
    elif class_index == 2:
        # Class 2: LED Lamp (~15W, bridge rectifier non-linear switching, strong 3rd & 5th)
        i_peak = (15.0 / (230.0 * 0.6)) * np.sqrt(2)
        i = i_peak * (np.sin(2 * np.pi * FREQ * t) 
                      + 0.65 * np.sin(2 * np.pi * 3 * FREQ * t) 
                      + 0.35 * np.sin(2 * np.pi * 5 * FREQ * t))
    
    elif class_index == 3:
        # Class 3: SMPS Laptop Charger (~65W, sharp peak pulses near voltage peak)
        v_norm = v / np.max(np.abs(v))
        i_raw = np.maximum(0, np.abs(v_norm) - 0.72) ** 1.8 * np.sign(v_norm)
        i_peak = (65.0 / (230.0 * 0.55)) * np.sqrt(2)
        i = (i_raw / (np.max(np.abs(i_raw)) + 1e-6)) * i_peak
        
    elif class_index == 4:
        # Class 4: Compressor / Refrigerator (~180W, dynamic inductive motor)
        i_peak = (180.0 / (230.0 * 0.72)) * np.sqrt(2)
        phase_lag = np.radians(43.9) # cos(phi) = 0.72
        i = i_peak * np.sin(2 * np.pi * FREQ * t - phase_lag)
        # Add 3rd harmonic from saturation
        i += (i_peak * 0.12) * np.sin(2 * np.pi * 3 * FREQ * t)
        
    else:
        raise ValueError("Invalid class index")
        
    # Add Gaussian noise
    i += np.random.normal(0, np.std(i) * noise_level + 0.01, WINDOW_SIZE)
    
    # Feature extraction (9 scalar features: H1..H7, P, Q)
    v_rms = np.sqrt(np.mean(v ** 2))
    i_rms = np.sqrt(np.mean(i ** 2))
    p = np.mean(v * i)
    s = v_rms * i_rms
    q = np.sqrt(max(0.0, s**2 - p**2))
    
    # Harmonics via FFT
    fft_vals = np.abs(np.fft.rfft(i)) / (WINDOW_SIZE / 2)
    # df = 2000 / 80 = 25 Hz. Fundamental 50Hz = index 2.
    # Harmonics 1 to 7: indices 2, 4, 6, 8, 10, 12, 14
    harmonics = [fft_vals[2 * h] if 2 * h < len(fft_vals) else 0.0 for h in range(1, 8)]
    scalar_features = np.array(harmonics + [p, q], dtype=np.float32)
    
    # Normalized raw waveform matrix (2 x 80: channel 0 = V, channel 1 = I)
    raw_vi = np.stack([v / 350.0, i / 15.0], axis=-1).astype(np.float32) # Shape (80, 2)
    
    return raw_vi, scalar_features, class_index

def build_dataset(num_samples_per_class=1000):
    raw_list, scalar_list, labels_list = [], [], []
    for cls in range(5):
        for _ in range(num_samples_per_class):
            raw_vi, scalar_feats, label = generate_appliance_sample(cls)
            raw_list.append(raw_vi)
            scalar_list.append(scalar_feats)
            labels_list.append(label)
            
    X_raw = np.array(raw_list)
    X_scalars = np.array(scalar_list)
    y = np.array(labels_list)
    
    # Shuffle
    indices = np.random.permutation(len(y))
    return X_raw[indices], X_scalars[indices], y[indices]

if __name__ == "__main__":
    X_raw, X_scalars, y = build_dataset(100)
    print(f"Generated synthetic dataset: X_raw shape={X_raw.shape}, X_scalars shape={X_scalars.shape}, y={y.shape}")

