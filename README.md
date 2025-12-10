# RailWatch-Email-Alert-Parser

A hybrid system for converting railroad alert emails into a structured,
AI-validated defect detection dataset. This project ingests Outlook `.msg` alerts,
extracts embedded camera images, detects gate violations and track occupancy using YOLO
models, and outputs enriched CSV/XLSX files for safety analytics.

---

## Problem

Field alert systems generate `.msg` email notifications containing embedded crossing
camera images. These emails:

- are inconsistent in format
- contain multiple embedded base64 images
- require directional interpretation (East/West)
- must be validated against multiple ML models

Manual parsing is not scalable.

---

## Overview

This pipeline automatically:

1. **Extracts metadata** (timestamp, location, direction) from `.msg` files 
2. **Generates a dataset**: saves images + metadata 
3. **Runs ML inference** using:
   - Custom **YOLOv10 IGCT** model (train / truck / legal occupier)
   - **YOLOv11 gate model**
   - **COCO fallback** for ambiguous detections
   - Optional **OpenAI classification** verification
4. **Outputs final CSV/XLSX datasets** suitable for reporting and training future models

---

## Criteria

## Data Annotation Criteria

This project evaluates rail-crossing imagery to determine whether alerts generated from camera snapshots are valid and properly characterized. Each processed image contains metadata across the following key fields:

---

### **1) Accurate Alert**

**Definition:**  
Indicates whether the image contains **any object of interest** within the defined **Region of Interest (ROI)**.

An alert is considered **accurate** if at least one of the following appears:

- 🚦 Gate Down (NOT gate up)
- 🚂 Train
- 🚛 Truck
- 🚜 Legal Occupier (Railway Maintenance Vehicle)
- 🚶 Person
- 🚗 Car

**Values:**
- `true` → At least one relevant object is visible in the ROI
- `false` → No meaningful object detected

---

### **2️) Accurate Classification**

**Definition:**  
Indicates whether the alert corresponds to one of the *primary* objects that justify a true rail-crossing alert:

- 🚦 Gate Down  
- 🚂 Train  
- 🚜 Legal Occupier (Railway Vehicle)

**Values:**
- `true` → The object belongs to one of the categories above  
- `false` → Something else was detected

---

### **3️) Classification**

**Definition:**  
If the alert was **not** a primary object listed under section (2), this column stores the detected object type.

(If the alert was correctly classified under section (2), this column may be empty.)

The following is supplied in the output:
- Dataset of Images  
- Results File (CSV/XLSX)  
- Region of Interest (ROI) Outline

---

## Architecture

Email Service:
- Ingests exported rail alert emails
- Parses .msg messages and extracts metadata such as:
- Timestamp
- Location
- Direction (E/W)
- Original message filename
- Produces a structured alerts.json file that serves as the pipeline's entry point

ML Service:
- Consumes alerts.json and the matching .msg files
- Extracts embedded crossing images from alerts
- Applies object detection and classification using trained models
- Determines whether alerts are accurate and what was detected
- Outputs final analytics: results.csv and results.xlsx
