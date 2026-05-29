# System Architecture

## Overview

```text
smart_privacy_guardian/
├── app.py                  Entry point
├── config/
│   └── settings.py         Shared paths, thresholds, camera, UI config
├── src/
│   ├── core/
│   │   ├── face_recog.py   Face embedding, encryption, verification
│   │   ├── blur.py         Screen blur overlay
│   │   ├── liveness.py     Optional blink-based liveness
│   │   └── audio_alert.py  Voice/audio alert
│   ├── detection/
│   │   └── detector.py     Haar face detection + YOLOv5s threats
│   └── ui/
│       └── main_window.py  PyQt5 main window
├── models/                 Runtime model and embedding files
├── assets/                 Runtime audio and admin face files
├── logs/                   Runtime logs
├── tests/
├── docs/
└── frontend/               Optional FastAPI frontend
```

## Data Flow

```text
Webcam
  -> DetectionManager background thread
       -> Haar Cascade: face boxes
       -> YOLOv5s ONNX: threat boxes and person boxes

MainWindow QTimer
  -> det.get()
       -> threats trigger blur
       -> person boxes without face overlap trigger blur
       -> face boxes go through FaceRecognizer.verify()
            -> admin and live: screen remains visible
            -> unknown or not live: blur and alert
```

## Key Decisions

| Decision | Reason |
| --- | --- |
| Background detection thread | Keeps the PyQt UI responsive |
| YOLO throttling | Reduces CPU load from ONNX inference |
| 64x64 pixel embedding | Lightweight and offline |
| Fernet encryption | Protects stored admin embedding data |
| SHA-256 checksum | Detects embedding tampering |
| Separate shoulder-surfer list | Avoids treating body boxes as face crops |
