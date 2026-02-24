# 🛡️ Smart Privacy Guardian

**AI-Based Multi-Modal Screen Privacy Protection System**

Smart Privacy Guardian is an AI-powered desktop security application designed to protect user privacy by detecting unauthorized viewers and automatically securing sensitive on-screen content. The system uses **computer vision, face recognition, and object detection** to identify human presence and apply intelligent privacy actions such as screen blurring, alerts, and logging.

---

## 🚀 Project Objective

The main goal of Smart Privacy Guardian is to:

* Prevent **shoulder surfing** and unauthorized viewing
* Protect **confidential data** on screens
* Provide **real-time AI-based privacy enforcement**
* Create a smart, automated **screen protection system**

---

## 🧠 Core Features

* 🔍 **Human Detection** using YOLO object detection
* 🧑‍💻 **Face Recognition** using DeepFace
* 🛡️ **Admin Face Verification System**
* 🌫️ **Automatic Screen Blur** on unauthorized detection
* 🔔 **Voice Alerts & Notifications**
* 📜 **Security Logs** for activity tracking
* ⏸️ **Auto Resume Logic** when admin is alone
* 🎛️ **Detection Toggle Controls**
* 🖥️ **Sensitive Window Protection**

---

## 🏗️ System Architecture

1. Webcam Feed Capture
2. Human Detection (YOLO)
3. Face Recognition (DeepFace)
4. Identity Verification (Admin vs Unknown)
5. Decision Engine
6. Privacy Action Layer

   * Screen Blur
   * Alerts
   * Logging

---

## 🧰 Tech Stack

### Programming Language

* Python

### Libraries & Frameworks

* OpenCV
* YOLO (Object Detection)
* DeepFace (Face Recognition)
* PyQt5 (Admin Face Registration Tool)
* Tkinter (Main Application UI)
* NumPy

### AI Components

* Computer Vision
* Facial Recognition
* Object Detection
* Real-Time Video Processing

---

## 📂 Project Structure

```
Smart-Privacy-Guardian/
│
├── admin_face_capture/        # PyQt5-based admin registration tool
├── main_app/                  # Tkinter-based main application
├── models/                    # YOLO models and configs
├── logs/                      # Security logs
├── utils/                     # Helper functions
├── assets/                    # UI assets
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-privacy-guardian.git

# Navigate to project directory
cd smart-privacy-guardian

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ How It Works

1. User registers admin face using the **Admin Face Capture Tool**
2. System continuously monitors webcam feed
3. YOLO detects human presence
4. DeepFace verifies identity
5. If **unauthorized person detected**:

   * Screen is blurred
   * Alert is triggered
   * Event is logged
6. If only admin is present:

   * Screen resumes normally

---

## 🔐 Privacy Logic

| Condition                | Action              |
| ------------------------ | ------------------- |
| Admin only               | Normal screen       |
| Unknown person detected  | Screen blur + alert |
| Multiple people detected | Screen blur + alert |
| No person detected       | Pause detection     |

---

## 📈 Use Cases

* Corporate office privacy
* Online exams
* Remote work security
* Banking and finance systems
* Personal system privacy
* Smart offices

---

## 🎯 Future Enhancements

* Multi-user authentication
* Mobile integration
* Cloud logging dashboard
* Mobile app integration
* Emotion detection
* Gesture-based privacy controls
* Encrypted activity logs

---

## 📜 License

This project is developed for **academic and research purposes**.

---

## 👨‍💻 Author

**Anurag Patel**
B.Tech CSE (AI & ML) Student

---

## ⭐ Why This Project Matters

Smart Privacy Guardian demonstrates the **practical application of AI in cybersecurity and privacy protection**, combining multiple AI technologies into a real-world intelligent system. It is suitable for:

* Academic projects
* Final year projects
* Research demonstrations
* Startup MVP concepts
* AI portfolio showcase

---

## 🔖 Keywords (for GitHub Search & ATS)

Artificial Intelligence, Machine Learning, Computer Vision, YOLO, DeepFace, Face Recognition, Screen Privacy, Cybersecurity, AI Security, Smart Surveillance, Python AI Project
