import os
import base64
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from openai import OpenAI
from shapely.geometry import Polygon, box as shapely_box
from ultralytics import YOLO

load_dotenv()

METADATA_CSV_PATH   = os.getenv("METADATA_CSV_PATH", r"dataset/metadata.csv")
IMAGE_DIR           = os.getenv("IMAGE_DIR", r"dataset/images")
DETECTION_OUTPUT_DIR = os.getenv("DETECTION_OUTPUT_DIR", r"dataset/output")
FINAL_RESULTS_CSV   = os.getenv("FINAL_RESULTS_CSV", r"dataset/results.csv")

IGCT_WEIGHT = os.getenv("IGCT_WEIGHT", "weights/yolov10b_igct.pt")
GATE_WEIGHT = os.getenv("GATE_WEIGHT", "weights/yolov11x_gate.pt")
COCO_WEIGHT = os.getenv("COCO_WEIGHT", "yolov10x.pt")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  
SIGNAL_API_URL = os.getenv("SIGNAL_API_URL")

# OCR header crops
LOCATION_CROPS = {
}

# gate region of interest crops
ROI = {
}

# crossing region of interest crops
CROSSING_ROI = {
}

def box_overlaps_polys(box_xyxy, polys):
    x1, y1, x2, y2 = [float(v) for v in box_xyxy]
    bbox = shapely_box(x1, y1, x2, y2)
    for poly in polys:
        if Polygon(poly).intersects(bbox):
            return True
    return False


def gate_validation(image_path, url):
    if not url or not os.path.exists(image_path):
        return None
    image = cv2.imread(image_path)
    ok, buf = cv2.imencode(".png", image)
    if not ok:
        return None
    files = {'file': ('gate.png', buf.tobytes(), 'image/png')}
    try:
        resp = requests.post(url, files=files, timeout=5)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


def differentiate_legal_occupier(img, client: OpenAI):
    if client is None or img is None:
        return None
    try:
        _, buffer = cv2.imencode('.jpg', img)
        b64 = base64.b64encode(buffer).decode('utf-8')
        messages = [
            {"role": "user", "content": "Return 0 for person, 1 for vehicle."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    }
                ]
            },
        ]
        out = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=20,
        )
        return out.choices[0].message.content.strip()
    except Exception:
        return None


def stage2_detect(images_dir, image_names, output_folder,
                  igct_weight, gate_weight, coco_weight,
                  use_openai=True, plot=True):

    os.makedirs(output_folder, exist_ok=True)
    results = []

    igct_model = YOLO(igct_weight)
    gate_model = YOLO(gate_weight)
    coco_model = YOLO(coco_weight)

    openai_client = OpenAI(api_key=OPENAI_API_KEY) if (use_openai and OPENAI_API_KEY) else None

    igct_names = getattr(getattr(igct_model, "model", None), "names", {})
    coco_names = getattr(getattr(coco_model, "model", None), "names", {})

    for idx, img_name in enumerate(image_names, start=1):
        img_path = os.path.join(images_dir, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Error -- Could not read image: {img_path}")
            continue

        print(f"[DETECT] {idx}/{len(image_names)}: {img_name}")
        memo = defaultdict(int)
        classification = ""

        base = os.path.splitext(img_name)[0]
        parts = base.split("_")
        if len(parts) >= 2:
            location_key = "_".join(parts[:-1]).lower()
        else:
            location_key = base.lower()

        # gate validation logic
        if not ROI.get(location_key):
            # no explicit gate ROIs, just run gate YOLO
            gate_results = gate_model(frame, conf=0.25, verbose=False)
            for res in gate_results:
                for box in res.boxes:
                    _, _, w, h = box.xywh[0]
                    if w / h > 1.5:
                        memo["horizontal_gate"] += 1
        else:
            # use external API validation on ROI crops
            for roi in ROI.get(location_key, []):
                (x1, y1), (x2, y2) = roi
                gate_img = frame[y1:y2, x1:x2, :]
                tmp = os.path.join(output_folder, f"gate_{img_name}")
                cv2.imwrite(tmp, gate_img)
                res = gate_validation(tmp, SIGNAL_API_URL)
                if res and 'Yes' in str(res.get("prediction", "")):
                    memo["horizontal_gate"] += 1

        # IGCT detection
        obj_results = igct_model(frame, conf=0.5, verbose=False)
        if plot:
            obj_frame = obj_results[0].plot()
            cv2.imwrite(os.path.join(output_folder, f"obj_{img_name}"), obj_frame)

        for r in obj_results:
            for box in r.boxes:
                cls_name = igct_names.get(int(box.cls), "")
                if cls_name == "legal_occupier_vehicle":
                    x, y, w, h = box.xywh[0].detach()
                    crop = frame[int(y - h / 2):int(y + h / 2),
                                 int(x - w / 2):int(x + w / 2)]
                    res = differentiate_legal_occupier(crop, openai_client)
                    if res == "1":
                        memo["legal_occupier_vehicle"] += 1
                elif cls_name == "train":
                    memo["train"] += 1
                elif cls_name == "truck":
                    memo["truck"] += 1

        accurate_class = any(memo.values())

        # COCO model fallback
        if not accurate_class and CROSSING_ROI.get(location_key):
            polys = CROSSING_ROI[location_key]
            coco_results = coco_model(frame, conf=0.25, verbose=False)
            counts = defaultdict(int)

            # only need to detect following classes -- others are excluded
            VALID_CLASSES = {"person", "car", "truck", "bicycle"}

            for r in coco_results:
                for c, xy in zip(r.boxes.cls.tolist(), r.boxes.xyxy.tolist()):
                    c = int(c)
                    nm = coco_names.get(c, str(c)).lower()
                    if nm not in VALID_CLASSES:
                        continue
                    if not box_overlaps_polys(xy, polys):
                        continue
                    counts[nm] += 1

            if counts:
                classification = ", ".join(f"{k}:{v}" for k, v in counts.items())

        results.append({
            "Image": img_name,
            "horizontal_gate": memo["horizontal_gate"] > 0,
            "legal_occupier_vehicle": memo["legal_occupier_vehicle"] > 0,
            "train": memo["train"] > 0,
            "truck": memo["truck"] > 0,
            "accurate_alert": any(memo.values()) or bool(classification),
            "accurate_class": any(memo.values()),
            "classification": classification,
        })

    return pd.DataFrame(results)

def main():
    meta_path = Path(METADATA_CSV_PATH)
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata CSV not found -- {meta_path}")

    meta_df = pd.read_csv(meta_path)

    if "Image" not in meta_df.columns:
        raise ValueError("Metadata CSV does not contain 'Image' column")

    image_names = meta_df["Image"].tolist()

    det_df = stage2_detect(
        IMAGE_DIR,
        image_names,
        DETECTION_OUTPUT_DIR,
        IGCT_WEIGHT,
        GATE_WEIGHT,
        COCO_WEIGHT,
        use_openai=True,
        plot=True,
    )

    final_df = meta_df.merge(det_df, on="Image", how="left")

    out_csv = Path(FINAL_RESULTS_CSV)
    out_dir = out_csv.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    out_xlsx = out_csv.with_suffix(".xlsx")
    final_df.to_csv(out_csv, index=False)
    final_df.to_excel(out_xlsx, index=False, engine="openpyxl")

    print(f"\n Detection complete.")
    print(f"   CSV : {out_csv}")
    print(f"   XLSX: {out_xlsx}")
    print(f"   Rows: {len(final_df)}")


if __name__ == "__main__":
    main()
