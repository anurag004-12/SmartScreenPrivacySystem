# 🛡️ Smart Privacy Guardian

**AI-Based Real-Time Screen Privacy Protection System**

Smart Privacy Guardian is an AI-powered desktop security application that protects your screen from unauthorized viewers using computer vision and object detection. It monitors your webcam in real time, verifies the admin's identity, detects intruders and threat devices, and automatically blurs the screen with an audio alert.

---

## 🚀 Project Objective

- Prevent **shoulder surfing** and unauthorized screen viewing
- Protect **confidential on-screen data** in real time
- Detect **recording devices** (phones, laptops) pointed at the screen
- Provide **automated AI-based privacy enforcement**

---

## 🧠 Core Features

| Feature | Technology |
|---|---|
| 👤 Admin Face Enrollment | OpenCV Haar Cascade + Pixel Embedding |
| 🔍 Face Recognition | 64×64 Grayscale Embedding + Cosine Similarity |
| 📱 Phone / Device Detection | YOLOv5s ONNX via OpenCV DNN |
| 🕵️ Shoulder Surfer Detection | YOLO Person Class (body detection) |
| 🌫️ Automatic Screen Blur | PyQt5 Fullscreen Overlay |
| 🔔 Voice Alert | gTTS + playsound |
| 📜 Security Logging | Python logging to `logs/app.log` |
| 🔒 Embedding Integrity | SHA-256 checksum tamper detection |
| 🎛️ Stop / Start Camera | UI toggle button |

---

## 🏗️ System Architecture

```
Webcam Feed
    │
    ├── Haar Cascade ──► Face Detected?
    │                        ├── Yes ──► Pixel Embedding ──► Cosine Similarity ──► Admin / Intruder
    │                        └── No  ──► (YOLO handles body detection)
    │
    └── YOLOv5s ONNX ──► Phone / Laptop / Person Detected?
                              ├── Threat Device ──► Instant Screen Blur + Alert
                              ├── Unknown Person ──► Screen Blur + Alert
                              └── Admin Only ──► Screen Normal
```

---

## 🧰 Tech Stack

- **Language:** Python 3.10
- **GUI:** PyQt5
- **Computer Vision:** OpenCV 4.12
- **Object Detection:** YOLOv5s ONNX (OpenCV DNN backend)
- **Face Recognition:** Custom 64×64 pixel embedding (NumPy + OpenCV)
- **Audio Alerts:** gTTS + playsound
- **Screen Capture:** pyautogui

---

## 📂 Project Structure

```
smart_privacy_guardian/
│
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
│
├── gui/
│   └── main_window.py       # PyQt5 UI — video feed, buttons, blur overlay
│
├── modules/
│   ├── detection.py         # Haar face detection + YOLOv5s threat detection
│   ├── face_recog.py        # Face embedding + cosine similarity verification
│   ├── liveness.py          # Liveness detector (always True — placeholder)
│   ├── blur.py              # Screen blur overlay
│   └── audio_alert.py       # Voice alert via gTTS
│
├── models/
│   └── yolov8n.onnx         # YOLOv5s ONNX model (download separately)
│
├── assets/
│   └── alert.mp3            # Alert audio file
│
├── logs/
│   └── app.log              # Runtime security logs
│
└── frontend/                # Optional web landing page (FastAPI)
    ├── main.py
    └── static/
```

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/smart-privacy-guardian.git
cd smart-privacy-guardian

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download YOLOv5s ONNX model
curl -L "https://github.com/doleron/yolov5-opencv-cpp-python/raw/main/config_files/yolov5s.onnx" -o models/yolov8n.onnx
```

---

## ▶️ How to Run

```bash
python main.py
```

---

## 🖥️ How to Use

1. **Enroll Admin** — Click `Enroll Admin`, position your face in the green box, press `C` to capture
2. **Monitor** — App continuously monitors webcam for faces and devices
3. **Threat Detected** — Screen blurs automatically + audio alert plays
4. **Stop Camera** — Click `Stop Camera` to pause detection and clear blur
5. **Re-enroll** — Click `Enroll Admin` anytime to update your face

---

## 🔐 Privacy Logic

| Condition | Action |
|---|---|
| Admin face only | ✅ Screen normal |
| Unknown face detected | 🔒 Screen blur + alert |
| Phone / laptop pointed at screen | 🔒 Screen blur + alert |
| Person detected (no face visible) | 🔒 Screen blur + alert |
| No person detected | ✅ Screen normal |
| Admin not enrolled | ⚠️ Enrollment prompt shown |

---

## 🔒 Security Features

- **SHA-256 checksum** on admin embedding — detects file tampering
- **Path traversal protection** — embedding paths validated against allowed directories
- **URL scheme validation** — only HTTPS allowed for model downloads
- **Secure enroll flow** — saves face crop only, not full frame

---

## 📈 Use Cases

- Corporate office privacy
- Online exam monitoring
- Remote work security
- Banking and finance terminals
- Personal laptop privacy

---

## 🎯 Future Enhancements

- DeepFace / FaceNet deep learning recognition
- Real liveness detection (blink detection)
- Multi-user admin support
- Encrypted activity logs
- Cloud dashboard via WebSocket
- Mobile app integration

---

## 📜 License

This project is developed for **academic and research purposes**.

---

## 👨‍💻 Author

**Anurag Patel**
B.Tech CSE (AI & ML)

---

## 🔖 Keywords

`Python` `OpenCV` `YOLOv5` `Face Recognition` `Computer Vision` `Screen Privacy` `Cybersecurity` `AI Security` `PyQt5` `Object Detection` `Real-Time` `Shoulder Surfing Prevention`
