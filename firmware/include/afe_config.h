#pragma once
#include <Arduino.h>

// ==========================================
// PIN DEFINITIONS & HARDWARE ASSIGNMENTS
// ==========================================
// Notice: Only ADC1 channels are used because ADC2 conflicts with Wi-Fi!
#define PIN_ADC_VOLTAGE        34  // ADC1_CH6 (ZMPT101B AC voltage output via 1.65V bias)
#define PIN_ADC_CURRENT        35  // ADC1_CH7 (SCT-013-030 AC current output via 1.65V bias)
#define PIN_ZERO_CROSS_IN      25  // Hardware zero-crossing comparator input
#define PIN_RELAY_TRIP_OUT     26  // Fast active-high relay trip output (<60ms)
#define PIN_STATUS_LED         2   // On-board LED indicator

// ==========================================
// SAMPLING & AC GRID SPECIFICATIONS
// ==========================================
#define GRID_FREQUENCY_HZ      50.0f
#define SAMPLING_FREQUENCY_HZ  2000.0f // 2 kHz sampling rate
#define SAMPLE_INTERVAL_US     500     // 500 microseconds (1 / 2000)
#define SAMPLES_PER_CYCLE      40      // 2000 / 50 = 40 samples per 20ms cycle
#define BUFFER_SIZE            256     // Ping-Pong buffer depth (~6.4 line cycles)

// ==========================================
// SENSOR CALIBRATION PARAMETERS
// ==========================================
// Midpoint voltage 3.3V / 2 = 1.65V -> 4095 * (1.65 / 3.3) = ~2048 counts
#define ADC_RAW_MIDPOINT       2048.0f 
#define ADC_VOLTAGE_REF        3.3f
#define ADC_MAX_COUNTS         4095.0f

// SCT-013-030: 30A / 1V RMS output -> 1V RMS = 1.414V peak -> 30A / 1.0V = 30 A/V
#define CURRENT_CALIBRATION_FACTOR   30.0f

// ZMPT101B module calibration factor (bench calibrated against calibrated multimeter)
#define VOLTAGE_CALIBRATION_FACTOR   230.0f / 1.0f

// ==========================================
// ADC POLYNOMIAL CORRECTION LOOKUP
// Mitigating ESP32 non-linearity below 0.15V and above 3.15V
// ==========================================
inline float correct_adc_nonlinearity(uint16_t raw_counts) {
    float x = (float)raw_counts;
    // 3rd-order polynomial fit for 11dB attenuation
    float v = (0.000105f * x) + (0.000000045f * x * x) - (0.00000000001f * x * x * x);
    if (v < 0.05f) v = 0.05f;
    if (v > 3.25f) v = 3.25f;
    return v;
}

