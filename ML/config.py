FEATURES = [
    "VMQ3",
    "VMQ135",
    "temperature",
    "humidity",
]

CLASSES = [
    "SAFE",
    "WEATHER",
    "ALCOHOL",
    "NARCOTIC",
]

SAMPLE_INTERVAL_MS = 100
SAMPLE_INTERVAL_S = SAMPLE_INTERVAL_MS / 1000.0
WINDOW_SECONDS = 3
SAMPLES_PER_WINDOW = 30
N_SAMPLES = SAMPLES_PER_WINDOW
DATASET_SIZE = 240_000
SEED = 823

H_REF = 50.0
T_REF = 25.0

# Model-space baselines for the two MQ sensors used by this model.
MODEL_BASELINES = {
    "MQ3": 2.68,
    "MQ135": 0.42,
}

# Approximate ESP32 clean-air raw baselines.
# Demonstration calibration values, not laboratory calibration constants.
REAL_BASELINES = {
    "MQ3": 1920.0,
    "MQ135": 480.0,
}

# Prototype environmental compensation coefficients for MQ3 and MQ135.
COMPENSATION_ALPHA_H = [
    0.0014,  # MQ3
    0.0022,  # MQ135
]

COMPENSATION_ALPHA_T = [
    0.0007,  # MQ3
    0.0009,  # MQ135
]