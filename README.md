# Smart Privacy Guardian

AI-based real-time screen privacy protection for desktop systems.

Smart Privacy Guardian monitors a webcam feed, verifies the enrolled admin face,
detects nearby people and threat devices, and blurs the screen with an audio
alert when privacy is at risk.

## Core Features

| Feature | Technology |
| --- | --- |
| Admin face enrollment | OpenCV Haar Cascade + pixel embedding |
| Face recognition | 64x64 grayscale embedding + cosine similarity |
| Phone/device detection | YOLOv5s ONNX via OpenCV DNN |
| Shoulder-surfer detection | YOLO person class + face overlap checks |
| Screen blur | PyQt5 fullscreen overlay + pyautogui screenshot |
| Audio alert | gTTS + playsound |
| Security logging | Python logging to `logs/app.log` |
| Embedding protection | Fernet encryption + SHA-256 checksum |

## Tools Used

| Area | Tools / Libraries |
| --- | --- |
| Programming language | Python |
| Computer vision | OpenCV, OpenCV Haar Cascade, OpenCV DNN |
| Object detection model | YOLOv5s ONNX |
| Face matching | NumPy, 64x64 grayscale pixel embeddings, cosine similarity |
| Desktop UI | PyQt5 |
| Screen capture and blur | PyAutoGUI, Pillow, OpenCV Gaussian blur |
| Audio alerts | gTTS, playsound |
| Security and integrity | cryptography/Fernet, SHA-256, Python logging |
| Optional liveness detection | dlib 68-point facial landmarks |
| Optional web frontend | FastAPI, Uvicorn, Jinja2, HTML, CSS, JavaScript |
| Packaging | PyInstaller, `SmartPrivacyGuardian.spec` |
| Testing / evaluation | `accuracy_test.py`, pytest-ready `tests/` package |

## Project Structure

```text
smart_privacy_guardian/
├── app.py
├── accuracy_test.py
├── config/
│   └── settings.py
├── src/
│   ├── core/
│   │   ├── audio_alert.py
│   │   ├── blur.py
│   │   ├── face_recog.py
│   │   └── liveness.py
│   ├── detection/
│   │   └── detector.py
│   └── ui/
│       └── main_window.py
├── frontend/
│   ├── main.py
│   └── static/
│       ├── index.html
│       ├── script.js
│       └── styles.css
├── models/
├── assets/
├── docs/
└── tests/
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

The app downloads the YOLOv5s ONNX model automatically on first run if it is
missing. To download it manually:

```bash
curl -L "https://github.com/doleron/yolov5-opencv-cpp-python/raw/main/config_files/yolov5s.onnx" -o models/yolov5s.onnx
```

## Run The Desktop App

```bash
python app.py
```

## Run The Optional Frontend

```bash
cd frontend
python -m pip install -r requirements.txt
python main.py
```

Then open `http://127.0.0.1:8000`.

## How To Use

1. Click `Enroll Admin` and capture your face.
2. Keep monitoring enabled while working.
3. If an unknown person or threat device is detected, the screen blurs and an
   alert sound plays.
4. Click `Stop Camera` to pause monitoring and clear the blur overlay.

## Privacy Logic

| Condition | Action |
| --- | --- |
| Admin face only | Screen remains visible |
| Unknown face detected | Screen blurs |
| Phone or laptop detected | Screen blurs |
| Person detected without matching face | Screen blurs |
| No person detected | Screen remains visible |
| Admin not enrolled | Enrollment prompt is shown |

## Security Notes

- `assets/admin_face.jpg`, `models/admin_emb.npy`, `models/admin_emb.npy.sha256`,
  and `models/emb.key` are personal runtime files and should not be committed.
- Existing plaintext embeddings are migrated to encrypted storage when
  `cryptography` is available.
- Liveness detection uses dlib when `models/shape_predictor_68_face_landmarks.dat`
  is present. By default, the app is configured to fail open if dlib is missing
  so demo usage is not blocked.

## Accuracy Test

```bash
python accuracy_test.py
```

Run the desktop app and enroll an admin before using the accuracy test.
