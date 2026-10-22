# 🔍 FaceFind — AI Face Recognition Photo Search Platform

> Upload all photos → Scan your face → Get only YOUR photos instantly!

## 🎯 What is FaceFind?

FaceFind is an AI-powered web application that allows event organizers to upload bulk photos (weddings, college fests, conferences), and users can then find all photos containing their face by simply scanning via webcam or uploading a selfie.

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js + Tailwind CSS |
| Backend | Python FastAPI |
| AI/CV | OpenCV + face_recognition (dlib) |
| Database | SQLite (upgradable to PostgreSQL) |
| Storage | Local filesystem (upgradable to AWS S3) |

## 📁 Project Structure

```
FaceFind/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment & settings
│   ├── database.py          # SQLAlchemy DB setup
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── face_engine.py       # AI face detection & matching
│   ├── routes/
│   │   ├── admin.py         # Admin auth endpoints
│   │   ├── events.py        # Event CRUD
│   │   ├── photos.py        # Photo upload & processing
│   │   ├── search.py        # Face search API
│   │   └── download.py      # Photo download / ZIP
│   ├── utils/
│   │   ├── storage.py       # File storage handler
│   │   └── helpers.py       # Utility functions
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   ├── start.bat            # Quick-start (Windows)
│   └── start.ps1            # Quick-start (PowerShell)
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, PhotoGrid, WebcamCapture
│   │   ├── pages/           # Home, Login, Dashboard, EventDetail
│   │   ├── services/api.js  # Axios API client
│   │   ├── context/         # AuthContext (JWT)
│   │   ├── App.jsx          # Router & layout
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   ├── vite.config.js       # Dev server & proxy config
│   └── tailwind.config.js
├── start-all.ps1            # Launch backend + frontend
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### First Time Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
```

**Frontend:**
```bash
cd frontend
npm install
```

### 🎯 Start Application (Choose One)

#### Option 1: Start Everything at Once (Easiest)
```powershell
# From project root directory
.\start-all.ps1
```

#### Option 2: Start Backend Only
```bash
cd backend
.\start.bat         # Double-click or run in terminal
# OR
.\start.ps1         # PowerShell version
```

#### Option 3: Start Manually
**Backend:**
```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Default Admin

- Email: admin
- Password: (set in backend/.env → ADMIN_PASSWORD)

## 🔄 System Workflow

1. **Admin** creates event & uploads bulk photos
2. **System** detects faces & generates encodings (background)
3. **User** visits event page → scans face (webcam/upload)
4. **AI** matches face against all stored encodings
5. **System** displays all matching photos
6. **User** downloads selected photos (single/bulk ZIP)

---

## 🌐 Deployment Guide

### Option 1: Render.com + Vercel (FREE — Recommended)

This is the **easiest free deployment** for a college project.

#### Step A: Deploy Backend on Render.com

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "FaceFind initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/facefind.git
   git push -u origin main
   ```

2. **Go to [render.com](https://render.com)** → Sign up with GitHub

3. **New → Web Service** → Connect your GitHub repo

4. **Configure:**
   | Setting | Value |
   |---------|-------|
   | Name | `facefind-backend` |
   | Root Directory | `backend` |
   | Runtime | `Docker` |
   | Instance Type | Free |

5. **Add Environment Variables** (in Render dashboard):
   ```
   SECRET_KEY=your-strong-random-secret-key-here
   ADMIN_EMAIL=admin@facefind.com
   ADMIN_PASSWORD=your-strong-admin-password
   FACE_TOLERANCE=0.5
   FACE_MODEL=hog
   CORS_ORIGINS=https://your-frontend.vercel.app
   PORT=8001
   DEBUG=False
   ```

6. Click **Deploy** → Wait 5-10 min (dlib compilation takes time on first build)

7. Your backend URL will be: `https://facefind-backend.onrender.com`

#### Step B: Deploy Frontend on Vercel

1. **Go to [vercel.com](https://vercel.com)** → Sign up with GitHub

2. **New Project** → Import your GitHub repo

3. **Configure:**
   | Setting | Value |
   |---------|-------|
   | Framework | Vite |
   | Root Directory | `frontend` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |

4. **Add Environment Variable:**
   ```
   VITE_API_URL=https://facefind-backend.onrender.com/api
   ```

5. Click **Deploy** → Done in 1-2 min!

6. Your live URL: `https://facefind.vercel.app`

---

### Option 2: Railway.app (Full-Stack, Easiest)

1. Go to [railway.app](https://railway.app) → Sign up with GitHub
2. **New Project** → Deploy from GitHub repo
3. Railway auto-detects Dockerfile for backend
4. Add frontend as second service
5. Set environment variables same as above
6. Done! Both services get public URLs

---

### Option 3: Quick Demo with ngrok (Instant — No Deployment)

Perfect for **college demo/presentation** — share your local app via internet URL.

1. **Download ngrok**: [ngrok.com/download](https://ngrok.com/download)

2. **Start your app locally:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   .\start.bat

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

3. **Expose backend:**
   ```bash
   ngrok http 8001
   ```

4. **Copy the URL** (e.g., `https://abc123.ngrok-free.app`)

5. **Update frontend temporarily** — set `VITE_API_URL` to the ngrok URL

6. **Share** the frontend URL with anyone — it works from any device!

---

### Option 4: Docker Deployment (Any Cloud / VPS)

```bash
# Build backend Docker image
cd backend
docker build -t facefind-backend .

# Run backend container
docker run -d \
  -p 8001:8001 \
  -v facefind-data:/app/uploads \
  -v facefind-thumbs:/app/thumbnails \
  -e SECRET_KEY=your-secret-key \
  -e CORS_ORIGINS=http://your-frontend-url \
  --name facefind-api \
  facefind-backend

# Build and serve frontend
cd frontend
npm run build
# Serve dist/ folder with any static host (Nginx, Apache, etc.)
```

---

### ⚠️ Important Deployment Notes

| Point | Details |
|-------|---------|
| **dlib compilation** | Takes 5-15 min on first deploy (one-time) |
| **Free tier limits** | Render free = sleeps after 15 min inactivity |
| **Wake-up time** | First request after sleep takes ~30 sec |
| **Storage** | Free tiers have limited disk — use S3 for production |
| **HTTPS** | Both Render & Vercel give free SSL certificates |
| **Database** | SQLite works for demo; switch to PostgreSQL for production |

## 📜 License

MIT License — Free for academic and personal use.
