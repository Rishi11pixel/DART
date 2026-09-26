# ml/train_tinyml.py

import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from config import CLASSES, DATASET_SIZE, FEATURES, SEED

# ============================================================
# CONFIGURATION
# ============================================================

np.random.seed(SEED)
tf.random.set_seed(SEED)

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "dataset.csv"

MODEL_DIR = BASE_DIR / "models" / "tinyml"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

KERAS_MODEL_PATH = MODEL_DIR / "sentry_tinyml.keras"
TFLITE_MODEL_PATH = MODEL_DIR / "sentry_tinyml_int8.tflite"

SCALER_MEAN_PATH = MODEL_DIR / "scaler_mean.npy"
SCALER_SCALE_PATH = MODEL_DIR / "scaler_scale.npy"

LABELS_PATH = MODEL_DIR / "labels.json"
ALERT_POLICY_PATH = MODEL_DIR / "alert_policy.json"


# ============================================================
# FEATURES
# ============================================================
LABELS = CLASSES

LABEL_TO_ID = {
    label: i
    for i, label in enumerate(LABELS)
}

ID_TO_LABEL = {
    i: label
    for i, label in enumerate(LABELS)
}


# ============================================================
# SETTINGS
# ============================================================

VALIDATION_SIZE = 0.20
TEST_SIZE = 0.20

EPOCHS = 50
BATCH_SIZE = 512
SHUFFLE_BUFFER_SIZE = 50_000
TFLITE_BATCH_SIZE = 1024
L2_STRENGTH = 0.0005
DROPOUT_RATE = 0.20

LEARNING_RATE = 0.001
HIGH_ALERT_LABELS = ("ALCOHOL", "NARCOTIC")
TARGET_ALERT_RECALL = 0.995


def apply_alert_policy(probabilities, threshold):
    predictions = np.argmax(probabilities, axis=1)
    alert_indices = [LABEL_TO_ID[label] for label in HIGH_ALERT_LABELS]
    alert_scores = probabilities[:, alert_indices].sum(axis=1)
    force_alert = alert_scores >= threshold
    strongest_alert = np.argmax(probabilities[:, alert_indices], axis=1)
    predictions[force_alert] = np.asarray(alert_indices)[strongest_alert[force_alert]]
    return predictions


def make_dataset(features, labels, training=False):
    dataset = tf.data.Dataset.from_tensor_slices((features, labels))
    if training:
        dataset = dataset.shuffle(
            buffer_size=min(len(features), SHUFFLE_BUFFER_SIZE),
            seed=SEED,
            reshuffle_each_iteration=True,
        )
    return dataset.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


# ============================================================
# LOAD DATASET
# ============================================================

print()
print("=" * 60)
print("             SENTRY TinyML TRAINING")
print("=" * 60)

print()
print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Dataset shape: {df.shape}")

# ------------------------------------------------------------
# Validate dataset
# ------------------------------------------------------------

required_columns = FEATURES + ["label"]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# Reject columns outside the selected sensor inputs and label.
unexpected_columns = set(df.columns) - set(required_columns)
if unexpected_columns:
    raise ValueError(
        f"Unexpected dataset columns: {sorted(unexpected_columns)}"
    )

# Make sure SEN0567 is completely gone
for column in df.columns:
    if "SEN0567" in column.upper():
        raise ValueError(
            f"SEN0567 still exists in dataset: {column}"
        )

# Make sure labels are valid
unknown_labels = set(df["label"].unique()) - set(LABELS)

if unknown_labels:
    raise ValueError(
        f"Unknown labels found: {unknown_labels}"
    )

if len(df) != DATASET_SIZE:
    raise ValueError(
        f"Expected {DATASET_SIZE} dataset rows, found {len(df)}."
    )

class_counts = df["label"].value_counts()
expected_class_count = DATASET_SIZE // len(CLASSES)
if any(class_counts.get(label, 0) != expected_class_count for label in CLASSES):
    raise ValueError(
        f"Dataset must contain {expected_class_count} rows per class: "
        f"{class_counts.to_dict()}"
    )


# ============================================================
# PREPARE X / Y
# ============================================================

X = df[FEATURES].astype(np.float32).values

y = np.array([
    LABEL_TO_ID[label]
    for label in df["label"]
], dtype=np.int32)


print()
print("Features:")
for i, feature in enumerate(FEATURES):
    print(f"  {i} -> {feature}")

print()
print("Classes:")
for i, label in enumerate(LABELS):
    print(f"  {i} -> {label}")

print()
print(f"Input feature count: {X.shape[1]}")


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train_full, X_test, y_train_full, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=SEED,
    stratify=y,
)

X_train, X_val, y_train, y_val = train_test_split(
    X_train_full,
    y_train_full,
    test_size=VALIDATION_SIZE,
    random_state=SEED,
    stratify=y_train_full,
)

print()
print("Dataset split:")
print(f"  Training   : {X_train.shape}")
print(f"  Validation : {X_val.shape}")
print(f"  Test       : {X_test.shape}")


# ============================================================
# STANDARD SCALER
# ============================================================

print()
print("Fitting StandardScaler...")

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train).astype(np.float32)
X_val_scaled = scaler.transform(X_val).astype(np.float32)
X_test_scaled = scaler.transform(X_test).astype(np.float32)

# Save scaler parameters
np.save(
    SCALER_MEAN_PATH,
    scaler.mean_.astype(np.float32),
)

np.save(
    SCALER_SCALE_PATH,
    scaler.scale_.astype(np.float32),
)

print("Scaler saved.")


# ============================================================
# SAVE LABELS
# ============================================================

with open(LABELS_PATH, "w") as f:
    json.dump(LABELS, f, indent=2)

print("Labels saved.")


# ============================================================
# BUILD TINYML MODEL
# ============================================================

print()
print("Building TinyML neural network...")

model = tf.keras.Sequential([
    tf.keras.layers.Input(
        shape=(len(FEATURES),),
        name="input",
    ),

    tf.keras.layers.Dense(
        32,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(L2_STRENGTH),
        name="dense_32",
    ),

    tf.keras.layers.Dropout(DROPOUT_RATE, name="dropout_1"),

    tf.keras.layers.Dense(
        16,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(L2_STRENGTH),
        name="dense_16",
    ),

    tf.keras.layers.Dropout(DROPOUT_RATE / 2, name="dropout_2"),

    tf.keras.layers.Dense(
        len(LABELS),
        activation="softmax",
        kernel_regularizer=tf.keras.regularizers.l2(L2_STRENGTH),
        name="classification",
    ),
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()


# ============================================================
# TRAINING
# ============================================================

print()
print("Training...")

train_dataset = make_dataset(X_train_scaled, y_train, training=True)
validation_dataset = make_dataset(X_val_scaled, y_val)

early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=6,
    min_delta=0.0005,
    restore_best_weights=True,
)

reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=2,
    cooldown=1,
    min_lr=0.00001,
    verbose=1,
)

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS,
    callbacks=[early_stopping, reduce_lr],
    shuffle=False,
    verbose=1,
)

validation_probabilities = model.predict(
    X_val_scaled,
    batch_size=BATCH_SIZE,
    verbose=0,
)
alert_indices = [LABEL_TO_ID[label] for label in HIGH_ALERT_LABELS]
validation_alert_scores = validation_probabilities[:, alert_indices].sum(axis=1)
validation_alert_mask = np.isin(
    y_val,
    alert_indices,
)
validation_base_predictions = np.argmax(validation_probabilities, axis=1)
validation_base_alert = np.isin(validation_base_predictions, alert_indices)
missable_alert_scores = np.sort(
    validation_alert_scores[validation_alert_mask & ~validation_base_alert]
)
allowed_misses = int(
    np.floor((1.0 - TARGET_ALERT_RECALL) * np.sum(validation_alert_mask))
)
if len(missable_alert_scores) > allowed_misses:
    alert_threshold = float(missable_alert_scores[allowed_misses])
else:
    alert_threshold = float(validation_alert_scores.max()) + 1e-7

validation_policy_predictions = apply_alert_policy(
    validation_probabilities,
    alert_threshold,
)
validation_policy_alert = np.isin(validation_policy_predictions, alert_indices)
validation_alert_recall = float(
    np.mean(validation_policy_alert[validation_alert_mask])
)
validation_false_alert_rate = float(
    np.mean(validation_policy_alert[~validation_alert_mask])
)

with open(ALERT_POLICY_PATH, "w", encoding="utf-8") as f:
    json.dump({
        "high_alert_labels": list(HIGH_ALERT_LABELS),
        "threshold": alert_threshold,
        "target_validation_recall": TARGET_ALERT_RECALL,
        "validation_recall": validation_alert_recall,
        "validation_false_alert_rate": validation_false_alert_rate,
        "calibration": "highest threshold meeting target validation recall",
    }, f, indent=2)

print()
print(f"High-alert threshold saved: {alert_threshold:.6f}")
print(f"Validation high-alert recall : {validation_alert_recall:.4f}")
print(f"Validation false-alert rate : {validation_false_alert_rate:.4f}")


# ============================================================
# SAVE KERAS MODEL
# ============================================================

model.save(KERAS_MODEL_PATH)

print()
print(f"Keras model saved:")
print(KERAS_MODEL_PATH)


# ============================================================
# FLOAT MODEL EVALUATION
# ============================================================

print()
print("=" * 60)
print("FLOAT MODEL EVALUATION")
print("=" * 60)

test_probabilities = model.predict(
    X_test_scaled,
    verbose=0,
)

y_pred = apply_alert_policy(
    test_probabilities,
    alert_threshold,
)

train_probabilities = model.predict(
    X_train_scaled,
    batch_size=BATCH_SIZE,
    verbose=0,
)

y_train_pred = apply_alert_policy(
    train_probabilities,
    alert_threshold,
)
train_accuracy = accuracy_score(y_train, y_train_pred)
train_macro_f1 = f1_score(y_train, y_train_pred, average="macro")

accuracy = accuracy_score(
    y_test,
    y_pred,
)

macro_f1 = f1_score(
    y_test,
    y_pred,
    average="macro",
)

print()
print(f"Accuracy : {accuracy:.4f}")
print(f"Macro F1 : {macro_f1:.4f}")
print(f"Train accuracy : {train_accuracy:.4f}")
print(f"Train Macro F1 : {train_macro_f1:.4f}")
print(f"Train-test accuracy gap : {train_accuracy - accuracy:+.4f}")

test_alert_mask = np.isin(y_test, alert_indices)
test_alert_predictions = np.isin(y_pred, alert_indices)
alert_false_negatives = int(np.sum(test_alert_mask & ~test_alert_predictions))
test_alert_recall = 1.0 - alert_false_negatives / int(np.sum(test_alert_mask))
non_alert_mask = ~test_alert_mask
alert_false_positive_rate = float(
    np.mean(test_alert_predictions[non_alert_mask])
)
print(f"Held-out high-alert false negatives : {alert_false_negatives}")
print(f"Held-out high-alert recall : {test_alert_recall:.4f}")
print(f"Held-out non-alert false-positive rate : {alert_false_positive_rate:.4f}")

print()
print("Classification report:")

print(
    classification_report(
        y_test,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=LABELS,
        digits=4,
        zero_division=0,
    )
)

print("Confusion matrix:")

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=list(range(len(LABELS))),
)

print()

header = "             " + " ".join(
    f"{label:>10}"
    for label in LABELS
)

print(header)

for i, label in enumerate(LABELS):
    row = " ".join(
        f"{value:10d}"
        for value in cm[i]
    )

    print(
        f"{label:>10} {row}"
    )


# ============================================================
# INT8 QUANTIZATION
# ============================================================

print()
print("=" * 60)
print("INT8 QUANTIZATION")
print("=" * 60)

print()
print("Converting to INT8 TFLite...")

converter = tf.lite.TFLiteConverter.from_keras_model(model)

converter.optimizations = [
    tf.lite.Optimize.DEFAULT
]


# Representative dataset
def representative_dataset():
    # Use a subset to keep conversion fast
    count = min(1000, len(X_train_scaled))

    for i in range(count):
        sample = X_train_scaled[i:i + 1].astype(
            np.float32
        )

        yield [sample]


converter.representative_dataset = representative_dataset

converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
]

converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()

with open(TFLITE_MODEL_PATH, "wb") as f:
    f.write(tflite_model)

print()
print("INT8 model saved:")
print(TFLITE_MODEL_PATH)

print()
print(
    f"INT8 model size: "
    f"{len(tflite_model)} bytes"
)


# ============================================================
# INT8 MODEL VERIFICATION
# ============================================================

print()
print("=" * 60)
print("INT8 MODEL VERIFICATION")
print("=" * 60)

interpreter = tf.lite.Interpreter(
    model_path=str(TFLITE_MODEL_PATH)
)

interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
input_index = input_details[0]["index"]
interpreter.resize_tensor_input(
    input_index,
    [TFLITE_BATCH_SIZE, len(FEATURES)],
)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_index = input_details[0]["index"]
output_index = output_details[0]["index"]

input_scale, input_zero_point = (
    input_details[0]["quantization"]
)

output_scale, output_zero_point = (
    output_details[0]["quantization"]
)

print()
print("Input:")
print(
    f"  shape      : "
    f"{input_details[0]['shape']}"
)

print(
    f"  dtype      : "
    f"{input_details[0]['dtype']}"
)

print(
    f"  scale      : "
    f"{input_scale}"
)

print(
    f"  zero point : "
    f"{input_zero_point}"
)

print()
print("Output:")
print(
    f"  shape      : "
    f"{output_details[0]['shape']}"
)

print(
    f"  dtype      : "
    f"{output_details[0]['dtype']}"
)

print(
    f"  scale      : "
    f"{output_scale}"
)

print(
    f"  zero point : "
    f"{output_zero_point}"
)


# ============================================================
# INT8 TEST SET EVALUATION
# ============================================================

print()
print("Evaluating INT8 model...")

int8_probabilities = []

if input_scale == 0:
    raise ValueError("Invalid INT8 input scale.")

for start in range(0, len(X_test_scaled), TFLITE_BATCH_SIZE):
    batch = X_test_scaled[start:start + TFLITE_BATCH_SIZE].astype(np.float32)
    valid_count = len(batch)
    if valid_count < TFLITE_BATCH_SIZE:
        batch = np.pad(
            batch,
            ((0, TFLITE_BATCH_SIZE - valid_count), (0, 0)),
        )

    quantized = np.clip(
        np.rint(batch / input_scale + input_zero_point),
        -128,
        127,
    ).astype(np.int8)
    interpreter.set_tensor(
        input_index,
        quantized,
    )

    interpreter.invoke()

    output = interpreter.get_tensor(output_index)[:valid_count]

    # Dequantize output
    if output_scale != 0:
        output = (output.astype(np.float32) - output_zero_point) * output_scale

    int8_probabilities.extend(output.tolist())


int8_probabilities = np.asarray(int8_probabilities, dtype=np.float32)
int8_predictions = apply_alert_policy(
    int8_probabilities,
    alert_threshold,
)


# ============================================================
# INT8 METRICS
# ============================================================

int8_accuracy = accuracy_score(
    y_test,
    int8_predictions,
)

int8_macro_f1 = f1_score(
    y_test,
    int8_predictions,
    average="macro",
)

print()
print(
    f"INT8 Accuracy : "
    f"{int8_accuracy:.4f}"
)

print(
    f"INT8 Macro F1 : "
    f"{int8_macro_f1:.4f}"
)

int8_alert_predictions = np.isin(int8_predictions, alert_indices)
int8_false_negatives = int(np.sum(test_alert_mask & ~int8_alert_predictions))
int8_alert_recall = 1.0 - int8_false_negatives / int(np.sum(test_alert_mask))
print(f"INT8 held-out high-alert false negatives : {int8_false_negatives}")
print(f"INT8 held-out high-alert recall : {int8_alert_recall:.4f}")

print()
print("INT8 classification report:")

print(
    classification_report(
        y_test,
        int8_predictions,
        labels=list(range(len(LABELS))),
        target_names=LABELS,
        digits=4,
        zero_division=0,
    )
)

print("INT8 confusion matrix:")

int8_cm = confusion_matrix(
    y_test,
    int8_predictions,
    labels=list(range(len(LABELS))),
)

print()

print(header)

for i, label in enumerate(LABELS):

    row = " ".join(
        f"{value:10d}"
        for value in int8_cm[i]
    )

    print(
        f"{label:>10} {row}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print()
print(f"Features : {len(FEATURES)}")
print(f"Classes  : {len(LABELS)}")

print()
print(f"Float accuracy : {accuracy:.4f}")
print(f"Float Macro F1 : {macro_f1:.4f}")

print()
print(f"INT8 accuracy  : {int8_accuracy:.4f}")
print(f"INT8 Macro F1  : {int8_macro_f1:.4f}")

print()
print("Artifacts:")

print(f"  Keras : {KERAS_MODEL_PATH}")
print(f"  TFLite: {TFLITE_MODEL_PATH}")
print(f"  Mean  : {SCALER_MEAN_PATH}")
print(f"  Scale : {SCALER_SCALE_PATH}")
print(f"  Labels: {LABELS_PATH}")
print(f"  Alert policy: {ALERT_POLICY_PATH}")

