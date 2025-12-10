import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# from .env
JAR_PATH = os.getenv("JAVA_ALERT_SERVICE_JAR", r"email_service/rail-alert-service/target/rail-alert-service-1.0-SNAPSHOT.jar")
MSG_INPUT_DIR = os.getenv("MSG_INPUT_DIR", r"dataset/raw_msgs")
ALERT_JSON_PATH = os.getenv("ALERT_JSON_PATH", r"alerts.json")

PROCESS_SCRIPT = os.getenv("PROCESS_SCRIPT", "process_dataset.py")
DETECT_SCRIPT = os.getenv("DETECT_SCRIPT", "detect_objects.py")

def run_step(description, cmd):
    print(f"\n{description}")
    print(">", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print("Done.")
    except subprocess.CalledProcessError as e:
        print("Failed -- ", e)
        sys.exit(1)


def main():
    # create alert.json with .msg files
    output_folder = Path(ALERT_JSON_PATH).parent.as_posix()
    run_step(
        "Extracting alerts from .msg.",
        ["java", "-jar", JAR_PATH, MSG_INPUT_DIR, Path(ALERT_JSON_PATH).parent.as_posix()]
    )

    # extract images + metadata
    run_step(
        "Processing dataset.",
        [sys.executable, PROCESS_SCRIPT]
    )

    # run object detection
    run_step(
        "Running YOLO + OpenAI detection.",
        [sys.executable, DETECT_SCRIPT]
    )

    print("Complete.")

if __name__ == "__main__":
    main()
