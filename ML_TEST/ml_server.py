import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from ml.config import (
        CLASSES,
        COMPENSATION_ALPHA_H,
        COMPENSATION_ALPHA_T,
        FEATURES,
        MODEL_BASELINES,
        REAL_BASELINES,
    )
except ModuleNotFoundError:
    from ML.config import (
        CLASSES,
        COMPENSATION_ALPHA_H,
        COMPENSATION_ALPHA_T,
        FEATURES,
        MODEL_BASELINES,
        REAL_BASELINES,
    )


app = Flask(__name__)
MODEL_DIR = ROOT / "ML" / "models" / "tinyml"
MODEL_PATH = MODEL_DIR / "sentry_tinyml.keras"
SCALER_MEAN_PATH = MODEL_DIR / "scaler_mean.npy"
SCALER_SCALE_PATH = MODEL_DIR / "scaler_scale.npy"
LABELS_PATH = MODEL_DIR / "labels.json"
ALERT_POLICY_PATH = MODEL_DIR / "alert_policy.json"
HIGH_ALERT_LABELS = {"ALCOHOL", "NARCOTIC"}

model = tf.keras.models.load_model(MODEL_PATH, compile=False)
scaler_mean = np.load(SCALER_MEAN_PATH).astype(np.float32)
scaler_scale = np.load(SCALER_SCALE_PATH).astype(np.float32)

with open(LABELS_PATH, "r", encoding="utf-8") as labels_file:
    label_classes = json.load(labels_file)
with open(ALERT_POLICY_PATH, "r", encoding="utf-8") as policy_file:
    alert_policy = json.load(policy_file)

alert_threshold = float(alert_policy["threshold"])
if model.input_shape[-1] != len(FEATURES):
    raise ValueError(
        f"Model expects {model.input_shape[-1]} features; config defines {len(FEATURES)}."
    )
if label_classes != CLASSES or model.output_shape[-1] != len(label_classes):
    raise ValueError("Model labels do not match the configured class order.")
if scaler_mean.shape != (len(FEATURES),) or scaler_scale.shape != (len(FEATURES),):
    raise ValueError("Saved scaler does not match the configured feature count.")

print("SENTRY ML server loaded")
print(f"Features: {FEATURES}")
print(f"Classes: {label_classes}")
print(f"High-alert threshold: {alert_threshold:.6f}")


def convert_sensor(raw_value, sensor_name):
    return (raw_value / REAL_BASELINES[sensor_name]) * MODEL_BASELINES[sensor_name]


def compensate_sensor(value, temperature, humidity, sensor_index):
    return float(
        value
        - COMPENSATION_ALPHA_H[sensor_index] * (humidity - 50.0)
        - COMPENSATION_ALPHA_T[sensor_index] * (temperature - 25.0)
    )


def extract_features(readings):
    if not isinstance(readings, list) or len(readings) != 30:
        raise ValueError("Exactly 30 readings are required.")
    if not all(isinstance(reading, dict) for reading in readings):
        raise ValueError("Each reading must be a JSON object.")

    mq3 = np.asarray([float(item["mq3"]) for item in readings], dtype=np.float64)
    mq135 = np.asarray([float(item["mq135"]) for item in readings], dtype=np.float64)
    temperature = np.asarray(
        [float(item["temperature"]) for item in readings], dtype=np.float64
    )
    humidity = np.asarray([float(item["humidity"]) for item in readings], dtype=np.float64)

    vmq3 = np.asarray([
        compensate_sensor(
            convert_sensor(mq3[index], "MQ3"), temperature[index], humidity[index], 0
        )
        for index in range(len(readings))
    ])
    vmq135 = np.asarray([
        compensate_sensor(
            convert_sensor(mq135[index], "MQ135"), temperature[index], humidity[index], 1
        )
        for index in range(len(readings))
    ])

    return np.asarray([
        float(np.mean(vmq3[-5:])),
        float(np.mean(vmq135[-5:])),
        float(np.mean(temperature[-5:])),
        float(np.mean(humidity[-5:])),
    ], dtype=np.float32)


def predict(features):
    scaled = ((features - scaler_mean) / scaler_scale).astype(np.float32)
    probabilities_array = model.predict(scaled.reshape(1, -1), verbose=0)[0]
    probabilities = {
        label: float(probabilities_array[index])
        for index, label in enumerate(label_classes)
    }
    alert_score = sum(probabilities[label] for label in HIGH_ALERT_LABELS)

    if alert_score >= alert_threshold:
        prediction = max(HIGH_ALERT_LABELS, key=probabilities.get)
    else:
        prediction = max(probabilities, key=probabilities.get)

    return prediction, probabilities, alert_score


@app.post("/predict")
def predict_endpoint():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    readings = data.get("readings")
    if not isinstance(readings, list) or len(readings) != 30:
        count = len(readings) if isinstance(readings, list) else 0
        return jsonify({"error": f"Expected 30 readings, received {count}."}), 400

    readiness_states = {
        str(item.get("source_status", "")).strip().upper()
        for item in readings
        if isinstance(item, dict)
    }
    if readiness_states & {"WARMUP", "CALIBRATION"}:
        return jsonify({"error": "Sensor warmup and calibration are not complete."}), 425

    try:
        features = extract_features(readings)
        prediction, probabilities, alert_score = predict(features)
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400

    is_high_alert = prediction in HIGH_ALERT_LABELS
    response = {
        "status": "HIGH-ALERT" if is_high_alert else "NON-THREAT",
        "prediction": prediction,
        "confidence": round(probabilities[prediction], 4),
        "high_alert_score": round(alert_score, 4),
        "high_alert_threshold": round(alert_threshold, 6),
        "probabilities": probabilities,
        "raw_model_probabilities": probabilities,
        "features": {
            name: round(float(features[index]), 5 if index < 2 else 2)
            for index, name in enumerate(FEATURES)
        },
    }
    print(
        f"{response['status']}: {prediction} "
        f"({response['confidence']:.4f}); alert score={alert_score:.4f}"
    )
    return jsonify(response)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL_PATH.name,
        "features": FEATURES,
        "classes": label_classes,
        "high_alert_labels": sorted(HIGH_ALERT_LABELS),
        "high_alert_threshold": alert_threshold,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
