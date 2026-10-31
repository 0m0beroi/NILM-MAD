"""
Post-Training Quantization (PTQ) Script to INT8 FlatBuffer for TensorFlow Lite Micro.
Exports C-header byte array for embedded ESP32 deployment.
"""

import os
import subprocess
import numpy as np
import tensorflow as tf
from synthetic_dataset import build_dataset

def representative_dataset_gen():
    X_raw, X_scalars, _ = build_dataset(num_samples_per_class=20)
    norm_params = np.load("../models/scalar_norm_params.npz")
    X_scalars_norm = (X_scalars - norm_params["mean"]) / norm_params["std"]
    
    for i in range(len(X_raw)):
        # Yield input samples for each model input
        raw_sample = np.expand_dims(X_raw[i], axis=0).astype(np.float32)
        scalar_sample = np.expand_dims(X_scalars_norm[i], axis=0).astype(np.float32)
        yield [raw_sample, scalar_sample]

def convert_to_int8():
    model_path = "../models/nilm_model.keras"
    if not os.path.exists(model_path):
        print(f"Model file {model_path} not found. Please run train_nilm.py first.")
        return

    model = tf.keras.models.load_model(model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    
    # Enforce full integer quantization for TFLite Micro compatibility
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    
    tflite_quant_model = converter.convert()
    
    tflite_path = "../models/nilm_model_int8.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_quant_model)
        
    model_size_kb = len(tflite_quant_model) / 1024.0
    print(f"INT8 Quantized TFLite Model Size: {model_size_kb:.2f} KB (Target: < 50 KB SRAM)")
    
    # Generate C Header Array
    c_header_path = "../../firmware/include/model_data.h"
    with open(c_header_path, "w") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write("// Auto-generated INT8 Quantized Model Flatbuffer for ESP32 TFLite-Micro\n")
        f.write(f"// Model Size: {len(tflite_quant_model)} bytes\n\n")
        f.write("alignas(16) const unsigned char g_nilm_model_data[] = {\n  ")
        
        hex_bytes = [f"0x{b:02x}" for b in tflite_quant_model]
        lines = []
        for i in range(0, len(hex_bytes), 12):
            lines.append(", ".join(hex_bytes[i:i+12]))
        f.write(",\n  ".join(lines))
        f.write("\n};\n\n")
        f.write(f"const unsigned int g_nilm_model_data_len = {len(tflite_quant_model)};\n")
        
    print(f"Exported C-header to {c_header_path}")

if __name__ == "__main__":
    convert_to_int8()

