"""
1D Depthwise-Separable CNN NILM Classifier Training Script
Implements the exact dual-branch neural architecture specified in Section 7 of the synopsis.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.model_selection import train_test_split
from synthetic_dataset import build_dataset

def build_nilm_model():
    # Branch 1: Raw V-I 1D Waveform (80 timesteps, 2 channels)
    raw_input = layers.Input(shape=(80, 2), name="raw_vi_input")
    
    # Layer 1: Conv1D k=3, 8 ch, ReLU
    x = layers.Conv1D(filters=8, kernel_size=3, padding="same", activation="relu")(raw_input)
    
    # Layer 2: Depthwise Separable Conv1D (16 ch) + MaxPool
    x = layers.SeparableConv1D(filters=16, kernel_size=3, padding="same", activation="relu")(x)
    x = layers.MaxPooling1D(pool_size=2)(x)
    
    # Layer 3: Depthwise Separable Conv1D (32 ch) + Global Average Pooling
    x = layers.SeparableConv1D(filters=32, kernel_size=3, padding="same", activation="relu")(x)
    waveform_features = layers.GlobalAveragePooling1D()(x)
    
    # Branch 2: Scalar DSP Features (9 features: H1..H7, P, Q)
    scalar_input = layers.Input(shape=(9,), name="scalar_features_input")
    scalar_features = layers.Dense(16, activation="relu")(scalar_input)
    
    # Feature Fusion via Concatenation
    combined = layers.concatenate([waveform_features, scalar_features])
    
    # Classification Head
    dense = layers.Dense(32, activation="relu")(combined)
    dense = layers.Dropout(0.2)(dense)
    output = layers.Dense(5, activation="softmax", name="appliance_class_output")(dense)
    
    model = models.Model(inputs=[raw_input, scalar_input], outputs=output, name="NILM_1D_CNN")
    return model

def train():
    os.makedirs("../models", exist_ok=True)
    print("Generating training dataset (5,000 samples across 5 classes)...")
    X_raw, X_scalars, y = build_dataset(num_samples_per_class=1000)
    
    # Normalize scalars using standard statistics
    scalar_mean = np.mean(X_scalars, axis=0)
    scalar_std = np.std(X_scalars, axis=0) + 1e-6
    X_scalars_norm = (X_scalars - scalar_mean) / scalar_std
    
    # Split Train / Validation / Test
    X_raw_tr, X_raw_val, X_sc_tr, X_sc_val, y_tr, y_val = train_test_split(
        X_raw, X_scalars_norm, y, test_size=0.2, random_state=42, stratify=y
    )
    
    model = build_nilm_model()
    model.summary()
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    early_stop = callbacks.EarlyStopping(monitor="val_accuracy", patience=10, restore_best_weights=True)
    
    history = model.fit(
        [X_raw_tr, X_sc_tr], y_tr,
        validation_data=([X_raw_val, X_sc_val], y_val),
        epochs=40,
        batch_size=32,
        callbacks=[early_stop]
    )
    
    val_loss, val_acc = model.evaluate([X_raw_val, X_sc_val], y_val)
    print(f"\nFinal Validation Accuracy: {val_acc * 100:.2f}% (Target: >=90%)")
    
    model.save("../models/nilm_model.keras")
    np.savez("../models/scalar_norm_params.npz", mean=scalar_mean, std=scalar_std)
    print("Saved model to ../models/nilm_model.keras")

if __name__ == "__main__":
    train()

