import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATASET_SIZE, FEATURES, CLASSES, SEED


RNG = np.random.default_rng(SEED)

# Each label is a mixture of a typical response and a wider envelope. The
# envelopes overlap intentionally to represent sensor cross-sensitivity.
CLASS_COMPONENTS = {
    "SAFE": [
        ([2.615, 0.375, 31.1, 68.0], [0.045, 0.035, 0.65, 2.8]),
        ([2.670, 0.460, 31.5, 69.5], [0.045, 0.050, 0.80, 3.2]),
    ],
    "WEATHER": [
        ([2.615, 0.375, 33.0, 76.0], [0.050, 0.040, 1.2, 4.5]),
        ([2.670, 0.460, 33.2, 75.0], [0.055, 0.050, 1.3, 4.5]),
    ],
    "ALCOHOL": [
        ([2.960, 0.480, 31.4, 68.8], [0.160, 0.070, 0.90, 3.5]),
        ([2.840, 0.520, 31.4, 69.0], [0.100, 0.060, 0.85, 3.5]),
    ],
    "NARCOTIC": [
        ([2.300, 0.760, 31.2, 68.5], [0.090, 0.100, 0.85, 3.5]),
        ([2.430, 0.670, 31.2, 68.5], [0.080, 0.070, 0.85, 3.5]),
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a balanced synthetic sensor dataset with overlapping response envelopes."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DATASET_SIZE,
        help=f"Total rows, divisible evenly by {len(CLASSES)} (default: {DATASET_SIZE}).",
    )
    return parser.parse_args()


def generate_class(name, count):
    components = CLASS_COMPONENTS[name]
    envelope_count = count // 4
    core_count = count - envelope_count
    values = np.vstack((
        RNG.normal(*components[0], size=(core_count, len(FEATURES))),
        RNG.normal(*components[1], size=(envelope_count, len(FEATURES))),
    ))
    return values[RNG.permutation(count)]


def main():
    args = parse_args()
    if args.samples <= 0 or args.samples % len(CLASSES) != 0:
        raise SystemExit(
            f"--samples must be a positive multiple of {len(CLASSES)} for equal class counts."
        )

    per_class = args.samples // len(CLASSES)
    features = []
    labels = []

    for class_name in CLASSES:
        features.append(generate_class(class_name, per_class))
        labels.extend([class_name] * per_class)

    X = np.vstack(features)
    y = np.asarray(labels)

    X[:, 0] = np.clip(X[:, 0], 2.00, 3.30)
    X[:, 1] = np.clip(X[:, 1], 0.20, 1.00)
    X[:, 2] = np.clip(X[:, 2], 27.0, 38.0)
    X[:, 3] = np.clip(X[:, 3], 45.0, 90.0)

    order = RNG.permutation(len(X))
    df = pd.DataFrame(X[order], columns=FEATURES)
    df["label"] = y[order]

    dataset_path = Path(__file__).resolve().with_name("dataset.csv")
    df.to_csv(dataset_path, index=False)

    print("=" * 60)
    print("SENTRY SYNTHETIC ENVELOPE DATASET")
    print("=" * 60)
    print(f"Rows       : {len(df)}")
    print(f"Features   : {len(FEATURES)}")
    print(f"Saved to   : {dataset_path}")
    print("\nClass distribution:")
    print(df["label"].value_counts().reindex(CLASSES))
    print("\nFeature ranges:")
    for feature in FEATURES:
        print(f"{feature:12s}: {df[feature].min():.6f} - {df[feature].max():.6f}")
    print("\nAlert labels: ALCOHOL, NARCOTIC")
    print("Envelope samples overlap neighboring SAFE/WEATHER responses by design.")
    print("=" * 60)


if __name__ == "__main__":
    main()
