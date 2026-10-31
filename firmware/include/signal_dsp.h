#pragma once
#include <Arduino.h>
#include <math.h>
#include "afe_config.h"

struct PowerMetrics {
    float v_rms;
    float i_rms;
    float p_active;
    float q_reactive;
    float s_apparent;
    float power_factor;
    float harmonics[7]; // H1 to H7 normalized amplitudes
};

class SignalDSP {
public:
    static void compute_metrics(
        const float* v_buf,
        const float* i_buf,
        uint16_t length,
        PowerMetrics& out
    ) {
        float sum_v_sq = 0.0f;
        float sum_i_sq = 0.0f;
        float sum_p = 0.0f;

        for (uint16_t k = 0; k < length; ++k) {
            float v = v_buf[k];
            float i = i_buf[k];
            sum_v_sq += v * v;
            sum_i_sq += i * i;
            sum_p += v * i;
        }

        out.v_rms = sqrtf(sum_v_sq / (float)length);
        out.i_rms = sqrtf(sum_i_sq / (float)length);
        out.p_active = sum_p / (float)length;
        out.s_apparent = out.v_rms * out.i_rms;

        if (out.s_apparent > out.p_active) {
            out.q_reactive = sqrtf((out.s_apparent * out.s_apparent) - (out.p_active * out.p_active));
        } else {
            out.q_reactive = 0.0f;
        }

        if (out.s_apparent > 0.01f) {
            out.power_factor = out.p_active / out.s_apparent;
        } else {
            out.power_factor = 1.0f;
        }

        // Compute Harmonics H1 to H7 using Discrete Fourier Transform (DFT bins)
        // With N=256 samples at 2000 Hz, frequency resolution df = 2000 / 256 = 7.8125 Hz
        // Fundamental 50 Hz corresponds to bin k = 50 / 7.8125 = 6.4 (approx bin 6-7)
        // We compute exact Goertzel or DFT correlation at multiples of 50 Hz:
        for (int h = 1; h <= 7; ++h) {
            float target_freq = (float)h * GRID_FREQUENCY_HZ;
            float omega = 2.0f * M_PI * target_freq / SAMPLING_FREQUENCY_HZ;
            float real_part = 0.0f;
            float imag_part = 0.0f;

            for (uint16_t n = 0; n < length; ++n) {
                float angle = omega * (float)n;
                real_part += i_buf[n] * cosf(angle);
                imag_part -= i_buf[n] * sinf(angle);
            }
            float magnitude = (2.0f / (float)length) * sqrtf(real_part * real_part + imag_part * imag_part);
            out.harmonics[h - 1] = magnitude;
        }
    }
};

