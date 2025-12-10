import os
import json
import base64
import extract_msg
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

ALERT_JSON = r"alerts.json"                 
MSG_INPUT_DIR = r"dataset/raw_msgs"            
IMAGE_OUTPUT_DIR = r"dataset/images"       
METADATA_CSV_PATH = r"dataset/metadata.csv" 

def load_alerts(json_path):
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found -- {json_path}")
    
    #note: each alert is one alert dictionary
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

#only extracts raw image data
def extract_images_from_msg(msg_path):
    msg = extract_msg.openMsg(msg_path)
    html = getattr(msg, "htmlBody", None)

    if not html:
        return []

    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="ignore")

    images = []
    for chunk in html.split('"'):
        if "base64" in chunk and "," in chunk and len(chunk) > 10000: #logic for broken html image src tags -- need to find them 
            try:
                raw = chunk.split(",", 1)[1]
                img_bytes = base64.b64decode(raw)
                img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    images.append(img)
            except Exception:
                continue
    return images

#process alert set, turn raw data into dataset
def process_dataset(alerts):
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    rows = []
    count = 0

    for alert in alerts:
        msg_file = Path(alert.get("imagePath", "")).name
        location = alert.get("location", "").lower().replace(" ", "_")
        direction = alert.get("direction", "").lower()
        msg_path = os.path.join(MSG_INPUT_DIR, msg_file)

        if not os.path.exists(msg_path):
            print(f"[WARN] MSG missing -- {msg_file}")
            continue

        imgs = extract_images_from_msg(msg_path)
        if not imgs:
            print(f"Error. No images found in -- {msg_file}")
            continue

        for idx, img in enumerate(imgs):
            img_name = f"{location}_{direction}_{idx}.jpg"
            save_path = os.path.join(IMAGE_OUTPUT_DIR, img_name)

            cv2.imwrite(save_path, img)
            rows.append({
                "Image": img_name,
                "Location": location,
                "Direction": direction,
                "Timestamp": alert.get("timestamp", ""),
                "OriginalMsgFilename": msg_file
            })

            print(f"[SAVED] {img_name}")
            count += 1

    df = pd.DataFrame(rows)
    df.to_csv(METADATA_CSV_PATH, index=False)
    print(f"\n Images saved.")
    print(f"\n Metadata -- {METADATA_CSV_PATH}")
    return df

def main():
    alerts = load_alerts("alert.json")
    print(f"Loaded {len(alerts)} alerts from JSON")

    process_dataset(alerts)

if __name__ == "__main__":
    main()
