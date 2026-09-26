import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATASET_SIZE, FEATURES, CLASSES, SEED

np.random.seed(SEED)

EXTRA_SAMPLES_PER_CLASS = {
    "SAFE": 1600,
    "WEATHER": 1600,
    "ALCOHOL": 0,
    "EXPLOSIVE": 1600,
    "NARCOTIC": 1600,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a balanced synthetic sensor dataset.")
    parser.add_argument(
        "--samples",
        type=int,
        default=DATASET_SIZE,
        help="Total row count; must be divisible by the number of classes (default: 250000).",
    )
    return parser.parse_args()


args = parse_args()
if args.samples % len(CLASSES) != 0:
    raise SystemExit(
        f"--samples must be divisible by {len(CLASSES)} for a balanced dataset."
    )


# ============================================================
# BASE CLASS DISTRIBUTIONS
# ============================================================

CLASS_PARAMS = {

    "SAFE": {
        "mean": [2.615, 0.375, 31.1, 68.0],
        "std":  [0.045, 0.025, 0.50, 2.0],
    },

    "WEATHER": {
        "mean": [2.615, 0.375, 33.0, 76.0],
        "std":  [0.055, 0.035, 1.5, 6.0],
    },

    # Deliberately moved away from household-response regions.
    "ALCOHOL": {
        "mean": [2.950, 0.500, 31.3, 67.5],
        "std":  [0.220, 0.085, 0.80, 3.0],
    },

    "EXPLOSIVE": {
        "mean": [2.380, 0.670, 31.1, 68.0],
        "std":  [0.070, 0.050, 0.50, 2.0],
    },

    "NARCOTIC": {
        "mean": [2.300, 0.620, 31.1, 68.0],
        "std":  [0.070, 0.050, 0.50, 2.0],
    },
}


def generate_class(name, n):
    p = CLASS_PARAMS[name]

    return np.random.normal(
        loc=p["mean"],
        scale=p["std"],
        size=(n, len(FEATURES))
    )


# ============================================================
# BASE DATASET
# ============================================================

X_parts = []
y_parts = []

for cls in CLASSES:
    class_total = args.samples // len(CLASSES)
    base_count = class_total - EXTRA_SAMPLES_PER_CLASS[cls]
    if base_count < 0:
        raise ValueError("Requested dataset is too small for the configured demo samples.")

    X_cls = generate_class(cls, base_count)

    X_parts.append(X_cls)
    y_parts.extend([cls] * base_count)


# ============================================================
# MEASURED HOUSEHOLD SENSOR ENVELOPES
#
# Synthetic examples only; replace these distributions with labelled hardware logs
# before treating model predictions as real-world detections.
#
# HARPIC:
# roughly:
# VMQ3   2.67 - 2.81
# VMQ135 0.60 - 0.89
#
# MOOV:
# roughly:
# VMQ3   2.57  - 2.60
# VMQ135 0.69  - 0.83
# ============================================================


# ============================================================
# HARPIC DEMO REGION
#
# Synthetic cross-sensitivity region.
#
# Target:
#       NARCOTIC probability rises
#
# This does NOT mean Harpic chemically contains narcotics.
# It represents a deliberately constructed demonstration
# mapping for the SENTRY prototype.
# ============================================================

HARPIC_CENTER = np.array([
    2.735,
    0.755,
    30.90,
    66.80
])

HARPIC_STD = np.array([
    0.055,
    0.075,
    0.25,
    1.00
])

N_HARPIC = 1600

harpic = np.random.normal(
    HARPIC_CENTER,
    HARPIC_STD,
    size=(N_HARPIC, len(FEATURES))
)

# Add sensor response variation.
harpic[:, 0] += np.random.normal(0, 0.015, N_HARPIC)
harpic[:, 1] += np.random.normal(0, 0.020, N_HARPIC)

X_parts.append(harpic)
y_parts.extend(["NARCOTIC"] * N_HARPIC)


# ============================================================
# MOOV DEMO REGION
#
# Target:
#       EXPLOSIVE probability rises
#
# Again, this is synthetic cross-sensitivity for the prototype.
# ============================================================

MOOV_CENTER = np.array([
    2.592,
    0.770,
    30.95,
    69.70
])

MOOV_STD = np.array([
    0.020,
    0.055,
    0.25,
    0.90
])

N_MOOV = 1600

moov = np.random.normal(
    MOOV_CENTER,
    MOOV_STD,
    size=(N_MOOV, len(FEATURES))
)

moov[:, 0] += np.random.normal(0, 0.008, N_MOOV)
moov[:, 1] += np.random.normal(0, 0.015, N_MOOV)

X_parts.append(moov)
y_parts.extend(["EXPLOSIVE"] * N_MOOV)


# ============================================================
# HOUSEHOLD TRANSITION REGIONS
#
# These prevent the classifier from making an unrealistically
# sharp boundary immediately outside the demo envelopes.
#
# Lower-intensity points remain SAFE/WEATHER.
# ============================================================

N_SAFE_HOUSEHOLD = 1200

household_center = np.array([
    2.610,
    0.650,
    30.95,
    69.0
])

household_std = np.array([
    0.040,
    0.080,
    0.30,
    1.20
])

household = np.random.normal(
    household_center,
    household_std,
    size=(N_SAFE_HOUSEHOLD, len(FEATURES))
)

X_parts.append(household[:600])
y_parts.extend(["SAFE"] * 600)

X_parts.append(household[600:])
y_parts.extend(["WEATHER"] * 600)


# ============================================================
# CONTROLLED BOUNDARY SAMPLES
# ============================================================

def add_boundary(class_a, class_b, n, label):
    mean_a = np.array(CLASS_PARAMS[class_a]["mean"])
    mean_b = np.array(CLASS_PARAMS[class_b]["mean"])

    t = np.random.uniform(0.15, 0.35, n)

    samples = (
        mean_a[None, :] * (1.0 - t[:, None])
        + mean_b[None, :] * t[:, None]
    )

    noise = np.random.normal(
        0,
        np.array([
            0.025,
            0.020,
            0.35,
            1.20
        ]),
        size=(n, len(FEATURES))
    )

    samples += noise

    X_parts.append(samples)
    y_parts.extend([label] * n)


add_boundary("SAFE", "EXPLOSIVE", 500, "SAFE")
add_boundary("WEATHER", "EXPLOSIVE", 500, "WEATHER")

add_boundary("SAFE", "NARCOTIC", 500, "SAFE")
add_boundary("WEATHER", "NARCOTIC", 500, "WEATHER")


# ============================================================
# COMBINE
# ============================================================

X = np.vstack(X_parts)
y = np.array(y_parts)


# ============================================================
# LIMITS
# ============================================================

X[:, 0] = np.clip(X[:, 0], 2.00, 3.30)
X[:, 1] = np.clip(X[:, 1], 0.25, 0.95)
X[:, 2] = np.clip(X[:, 2], 28.0, 36.0)
X[:, 3] = np.clip(X[:, 3], 50.0, 85.0)


# ============================================================
# SHUFFLE
# ============================================================

idx = np.random.permutation(len(X))

X = X[idx]
y = y[idx]


# ============================================================
# SAVE
# ============================================================

df = pd.DataFrame(X, columns=FEATURES)
df["label"] = y

DATASET_PATH = Path(__file__).resolve().with_name("dataset.csv")
df.to_csv(DATASET_PATH, index=False)


# ============================================================
# REPORT
# ============================================================

print("=" * 60)
print("SENTRY SYNTHETIC DEMO DATASET")
print("=" * 60)

print(f"Rows       : {len(df)}")
print(f"Features   : {len(FEATURES)}")
print(f"Saved to   : {DATASET_PATH}")

print("\nClass distribution:")
print(df["label"].value_counts().sort_index())

print("\nFeature ranges:")

for feature in FEATURES:
    print(
        f"{feature:12s}: "
        f"{df[feature].min():.6f} - "
        f"{df[feature].max():.6f}"
    )

print("\nDemo regions:")

print("\nHARPIC -> synthetic NARCOTIC region")
for feature, value in zip(FEATURES, HARPIC_CENTER):
    print(f"{feature:12s}: {value:.4f}")

print("\nMOOV -> synthetic EXPLOSIVE region")
for feature, value in zip(FEATURES, MOOV_CENTER):
    print(f"{feature:12s}: {value:.4f}")

print("=" * 60)