import requests
import re
import time
import os
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

SERVER_URL = os.getenv("SENTRY_ML_SERVER_URL", "http://127.0.0.1:5000/predict")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READINGS_FILE = REPO_ROOT / "sentry_fake_readings_1800.txt"
READINGS_FILE = DEFAULT_READINGS_FILE
WAIT_TIME = 0.1

# ============================================================
# LOAD ALL READINGS FROM TXT
# ============================================================

def load_readings():

    print("\nReading:", READINGS_FILE)

    if not READINGS_FILE.is_file():
        raise FileNotFoundError(
            f"Canonical fake readings file not found: {READINGS_FILE}"
        )

    with open(
        READINGS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()


    # --------------------------------------------------------
    # Match every sensor-reading block in the TXT file.
    # --------------------------------------------------------

    pattern = re.compile(
        r"Temperature:\s*([-+]?\d+(?:\.\d+)?)\s*C\s*"
        r"Humidity:\s*([-+]?\d+(?:\.\d+)?)\s*%\s*"
        r"MQ-3\s*\(Flying-Fish\):\s*(\d+)\s*"
        r"MQ-135\s*\(Air Quality\):\s*(\d+)\s*"
        r"(?:STATUS:\s*([^\r\n]+))?",
        re.MULTILINE
    )


    matches = pattern.findall(text)


    readings = []


    for i, match in enumerate(matches):
        temperature = float(match[0])
        humidity = float(match[1])
        mq3 = float(match[2])
        mq135 = float(match[3])
        source_status = match[4].strip() if match[4] else None

        readings.append({
            "timestamp": round(i * 0.1, 1),
            "temperature": temperature,
            "humidity": humidity,
            "mq3": mq3,
            "mq135": mq135,
        })

        if source_status:
            readings[-1]["source_status"] = source_status


    return readings


def send_reading(window, reading_number):
    payload = [{**reading, "battery": 84, "signal": 92} for reading in window]
    try:
        response = requests.post(SERVER_URL, json={"readings": payload}, timeout=10)
        if response.status_code != 200:
            print(f"Window {reading_number}: HTTP {response.status_code} - {response.text}")
            return False

        result = response.json()
        prediction = result.get("prediction")
        confidence = float(result.get("confidence", 0.0))
        print(f"{reading_number:03d} | prediction={prediction} confidence={confidence:.4f}")
        return True
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to the ML server. Run: python ML_TEST/ml_server.py")
        return False
    except (KeyError, ValueError, requests.RequestException) as exc:
        print(f"ERROR sending window {reading_number}: {exc}")
        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n========================================"
    )

    print(
        "       SENTRY SENSOR → ML"
    )

    print(
        "========================================"
    )


    # ========================================================
    # LOAD EVERYTHING FROM TXT
    # ========================================================

    readings = load_readings()


    print(

        f"\nTotal sensor readings found: "
        f"{len(readings)}"

    )


    if len(readings) < 30:

        print(

            "ERROR: TXT file contains fewer "
            "than 30 readings."

        )

        return


    print(
        "\nStarting transmission..."
    )

    window = []
    window_number = 1

    for reading in readings:
        window.append(reading)

        if len(window) == 30:
            if not send_reading(window, window_number):
                print("\nStopping.")
                break
            window = []
            window_number += 1
            time.sleep(WAIT_TIME)

    if window:
        print(f"\nSending final partial window ({len(window)} readings).")
        send_reading(window, window_number)


    print(
        "\n========================================"
    )

    print(
        "         TRANSMISSION COMPLETE"
    )

    print(
        "========================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()