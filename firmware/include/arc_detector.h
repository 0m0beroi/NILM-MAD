#pragma once
#include <Arduino.h>
#include <math.h>
#include "afe_config.h"

class ArcFaultDetector {
private:
    float highpass_prev_in = 0.0f;
    float highpass_prev_out = 0.0f;
    int consecutive_arc_cycles = 0;
    const int TRIP_CYCLE_THRESHOLD = 3; // 3 cycles @ 50 Hz = 60 ms

    // Thresholds tuned during bench testing
    const float DI_DT_THRESHOLD = 18.5f;       // Amperes / ms threshold
    const float SPECTRAL_ENTROPY_THRESHOLD = 0.82f; // Broadband randomness indicator

public:
    void init() {
        pinMode(PIN_RELAY_TRIP_OUT, OUTPUT);
        digitalWrite(PIN_RELAY_TRIP_OUT, LOW); // Relay un-tripped (closed circuit)
        consecutive_arc_cycles = 0;
    }

    // High-pass 1st order IIR filter (cutoff ~300 Hz) to eliminate 50 Hz fundamental
    float filter_highpass_300hz(float sample) {
        // RC filter at 300 Hz with fs=2000 Hz: alpha = RC / (RC + dt)
        const float alpha = 0.514f; 
        float out = alpha * (highpass_prev_out + sample - highpass_prev_in);
        highpass_prev_in = sample;
        highpass_prev_out = out;
        return out;
    }

    // Fast arc check executed at the completion of each line cycle (20 ms window)
    bool check_cycle_window(
        const float* i_cycle_samples,
        uint16_t length,
        int current_active_appliance_class,
        float& out_max_didt,
        float& out_entropy
    ) {
        float max_didt = 0.0f;
        float hf_buffer[SAMPLES_PER_CYCLE];
        float energy_sum = 0.0001f;

        // 1. High-pass filter above 300 Hz and compute max di/dt
        for (uint16_t k = 0; k < length; ++k) {
            hf_buffer[k] = filter_highpass_300hz(i_cycle_samples[k]);
            energy_sum += hf_buffer[k] * hf_buffer[k];

            if (k > 0) {
                // dt = 0.5 ms -> di / 0.5 ms = 2000 * di
                float didt = fabsf(i_cycle_samples[k] - i_cycle_samples[k - 1]) * 2000.0f;
                if (didt > max_didt) {
                    max_didt = didt;
                }
            }
        }

        // 2. Compute spectral/signal entropy of high-frequency components
        float entropy = 0.0f;
        for (uint16_t k = 0; k < length; ++k) {
            float p = (hf_buffer[k] * hf_buffer[k]) / energy_sum;
            if (p > 1e-6f) {
                entropy -= p * log2f(p);
            }
        }
        // Normalize entropy over SAMPLES_PER_CYCLE (max entropy = log2(40) = 5.32)
        entropy = entropy / 5.32f;

        out_max_didt = max_didt;
        out_entropy = entropy;

        bool anomaly_detected = (max_didt > DI_DT_THRESHOLD) || (entropy > SPECTRAL_ENTROPY_THRESHOLD);

        if (anomaly_detected) {
            // Benign Transient Gating:
            // If CNN detects class 1 (Induction motor) during initial spin-up or class 4 (Compressor inrush),
            // or typical dimmer chopping, check if profile matches benign switching:
            bool is_benign_inrush = (current_active_appliance_class == 4 && max_didt < 28.0f && entropy < 0.70f);

            if (!is_benign_inrush) {
                consecutive_arc_cycles++;
                if (consecutive_arc_cycles >= TRIP_CYCLE_THRESHOLD) {
                    // FAST HARDWARE TRIP: Under 60 ms!
                    digitalWrite(PIN_RELAY_TRIP_OUT, HIGH);
                    return true; // ARC FAULT TRIPPED!
                }
            } else {
                consecutive_arc_cycles = 0; // Benign switching suppressed
            }
        } else {
            consecutive_arc_cycles = 0;
        }

        return false;
    }

    void reset_trip() {
        digitalWrite(PIN_RELAY_TRIP_OUT, LOW);
        consecutive_arc_cycles = 0;
    }
};

