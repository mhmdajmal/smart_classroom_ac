# Teachable Machine Edge AI Smart Classroom Telemetry System

A full-stack, local Edge AI telemetry system and glassmorphism dashboard built with **FastAPI**, **LiteRT / TFLite Interpreter**, **Next.js**, **TailwindCSS**, and **Recharts**.

Powered by your custom Google Teachable Machine model (`model_unquant.tflite` & `labels.txt`).

---

## 🌟 Key System Capabilities

1. **Local TFLite Inference Engine**:
   - Zero-Keras lightweight execution (`ai-edge-litert` / TFLite Interpreter).
   - High-throughput video frame processing with high FPS.
   - Preprocessing: BGR -> RGB 224×224 normalization `(img / 127.5) - 1.0`.

2. **Automated Smart AC Cooling Control**:
   - **LOW Occupancy**: Power `OFF`, Fan `OFF`, Temp `None`.
   - **MEDIUM Occupancy**: Power `ON`, Fan `MED`, Temp `24°C`, Mode `ECO`.
   - **HIGH Occupancy**: Power `ON`, Fan `HIGH`, Temp `20°C`, Mode `COOL`.

3. **100% Visual & Logic Parity with `cheqe` Dashboard**:
   - **Real-time Command Center (`/`)**: Telemetry metrics, live MJPEG video stream (`/api/stream`), real-time line charts, system resource meters.
   - **Video Workbench (`/video`)**: Drag-and-drop video uploader and playback control panel.
   - **Analytics & Statistics (`/statistics`)**: Historical occupancy distributions, average inference latency, cumulative AC runtime.
   - **Live Console Logs (`/logs`)**: System logger viewer with download option.
   - **Control Settings (`/settings`)**: Interactive threshold configuration.

---

## 📁 Project Architecture

```text
smart-classroom-telemetry/
├── models/                        # Deep Learning & ML Models Directory
│   ├── keras_model.h5             # Google Teachable Machine Keras H5 Model
│   ├── best.pt                    # Custom Trained YOLO Bounding Box Model
│   └── labels.txt                 # Class labels (0 low, 1 middle, 2 High)
├── backend/                       # FastAPI Edge Server
│   ├── app/
│   │   ├── api/                   # REST & Streaming endpoints
│   │   │   └── router.py
│   │   ├── core/                  # Core config & logging
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── schemas/               # Pydantic data schemas
│   │   │   └── payload.py
│   │   ├── services/              # AI Inference & Business Logic Services
│   │   │   ├── ac_service.py
│   │   │   ├── occupancy_service.py
│   │   │   ├── statistics_service.py
│   │   │   ├── tflite_service.py
│   │   │   ├── video_processor.py
│   │   │   └── yolo_service.py
│   │   └── main.py                # FastAPI entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                      # Next.js 14 Glassmorphism Dashboard
│   ├── src/
│   │   ├── app/                   # App Router pages (Dashboard, Video, Stats, Logs, Settings)
│   │   ├── components/            # UI & Layout components
│   │   ├── services/              # Telemetry API client
│   │   └── types/                 # TypeScript interfaces
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── uploads/                       # Video upload storage (.gitkeep preserved)
├── logs/                          # System log output directory (.gitkeep preserved)
├── .gitignore                     # Git ignore rules for clean repository state
├── README.md                      # Comprehensive project documentation
└── run_project.bat                # 1-Click Windows Launcher Script
```

---

## 🚀 Step-by-Step Instructions to Run

### Method 1: 1-Click Windows Launcher (Recommended)
Double-click `run_project.bat` in the project root directory. It will start both backend and frontend servers automatically!

### Method 2: Manual Terminal Commands

#### 1. Start FastAPI Backend:
```bash
pip install opencv-python numpy ai-edge-litert fastapi uvicorn pydantic psutil pydantic-settings
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **MJPEG Live Feed**: `http://localhost:8000/api/stream`

#### 2. Start Next.js Frontend Dashboard:
```bash
cd frontend
npm run dev
```
- **UI Dashboard**: `http://localhost:3000`

---

## 🛠️ API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/stream` | `GET` | Live HTTP MJPEG video stream with prediction HUD card |
| `/api/dashboard` | `GET` | Real-time telemetry state (Occupancy, AC status, FPS, Memory/CPU) |
| `/api/timeline` | `GET` | Frame history timeline for live Recharts charts |
| `/api/statistics` | `GET` | Aggregated analytics & cumulative AC runtime |
| `/api/upload` | `POST` | Upload custom classroom video files |
| `/api/control` | `POST` | Control playback (pause, resume, stop, remove) |
| `/api/settings` | `POST` | Dynamically update thresholds & AC temperature rules |
| `/api/logs` | `GET` | Stream live system log lines |
