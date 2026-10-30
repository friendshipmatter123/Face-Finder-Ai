# 🔍 Find Ur Photos — AI Face Recognition Photo Search Platform

> Upload all photos → Scan your face → Get only YOUR photos instantly!

## 🎯 What is FaceFind?

Find Ur Photos is an AI-powered web application that allows event organizers to upload event photos, and users can find photos containing their face by scanning via webcam or uploading a selfie.

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js + Tailwind CSS |
| Backend | Python FastAPI |
| AI/CV | OpenCV + face_recognition (dlib) |
| Database | Local MongoDB |
| Image storage | Local filesystem (`backend/uploads/`, `backend/thumbnails/`) |
| Processing storage | Local filesystem (`backend/temp/`) |
| Deployment | Local development (offline-capable) |

## 📁 Project Structure

```
FaceFind/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment & settings
│   ├── database.py          # MongoDB client and indexes
│   ├── models.py            # MongoDB collection names
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── face_engine.py       # AI face detection & matching
│   ├── routes/
│   │   ├── admin.py         # Admin auth endpoints
│   │   ├── events.py        # Event CRUD
│   │   ├── photos.py        # Photo upload & processing
│   │   ├── search.py        # Face search API
│   │   ├── registrations.py # Consent-based multi-angle registration
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

### Multi-angle registration

The public search flow supports an optional camera registration at
`/api/registrations/`. The browser uses MediaPipe Face Mesh landmarks to
estimate yaw, displays real pose progress, and captures only after a stable
pose. The front image is required; left and right images may be skipped.
The API validates one detectable face, lighting, sharpness, and encoding before
storing separate angle records. Search accepts the returned registration ID and
deduplicates matches by photo. The returned deletion token is required by
`DELETE /api/registrations/{registration_id}`.

The existing `face_recognition`/dlib model remains the matching model. This
feature does not claim improved side-angle accuracy; actual performance depends
on the configured detector/model and capture conditions.

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

- Email: value of `ADMIN_EMAIL`
- Password: value of `ADMIN_PASSWORD`

### Local prerequisites

Local development requires:

- Python 3.11+
- Node.js 18+
- A local MongoDB service

Create `backend/.env` from `backend/.env.example`. Do not commit `backend/.env`; it contains credentials.
Public admin registration is disabled. Configure the initial admin using `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `backend/.env`.

## 🔄 System Workflow

1. **Admin** creates an event and uploads photos
2. **System** detects faces & generates encodings (background)
3. **User** visits event page → scans face (webcam/upload)
4. **AI** matches face against all stored encodings
5. **System** displays all matching photos
6. **User** downloads selected photos (single/bulk ZIP)

### Storage and processing

- Original photos are stored in `backend/uploads/<event-id>/`.
- Generated thumbnails are stored in `backend/thumbnails/`.
- MongoDB stores event, photo metadata, and face encodings in the local `facefind` database.
- No Cloudinary, MongoDB Atlas, or internet connection is required in local-only mode.
- Processing images are resized to `MAX_PROCESSING_DIM` (default `1000`) to reduce memory usage.
- Upload batches are limited by `MAX_BULK_UPLOAD` (default `25`). Smaller batches are recommended on Render's free instance.
- If the local process stops during processing, open the event and use **Restart processing**. Unprocessed photos remain on the local disk.
- The dashboard's storage figure is the sum of uploaded photo sizes recorded in MongoDB.

Events are accessed using their event code. The admin UI does not expose a public-event/no-code option.

---

## 🌐 Deployment Guide

### Local offline mode

The application is configured for local-only mode by default:

```env
LOCAL_ONLY=true
MONGODB_URL=mongodb://127.0.0.1:27017
MONGODB_DATABASE=facefind
```

Start the **MongoDB** Windows service before starting the backend:

```powershell
Get-Service MongoDB
Start-Service MongoDB
```

Verify that these local folders exist; the application creates them automatically:

```text
backend/uploads/
backend/thumbnails/
backend/temp/
```

The local database and image files are persistent across application restarts. Back up the MongoDB `facefind` database and the three backend folders if the computer or disk could fail.

### Online deployment

The backend currently stores uploaded originals, thumbnails, and temporary files on
the local filesystem. For a real deployment, use a backend host with a persistent
disk (VPS, Azure VM, or a Render paid persistent disk) and MongoDB Atlas. The
free Render filesystem is ephemeral, so it is suitable only for testing; uploaded
photos can be lost after a restart or redeploy. Cloudinary variables are not used
by the current storage implementation.

Do not set `LOCAL_ONLY=true` on Render. Render does not run MongoDB inside the web service, so `127.0.0.1:27017` will always be refused there.

#### Step A: Deploy Backend on Render.com

1. **Push code to GitHub**

   From the repository root (`Facefinder AI`):
   ```bash
   git checkout main
   git pull --rebase origin main
   git add .
   git commit -m "Prepare FaceFind for deployment"
   git push -u origin main
   ```

   If this is a new clone without a remote, add it once:
   ```bash
   git remote add origin https://github.com/friendshipmatter123/Face-Finder-Ai.git
   ```

2. **Go to [render.com](https://render.com)** → Sign up with GitHub

3. **New → Web Service** → Connect your GitHub repo

4. **Configure:**
   | Setting | Value |
   |---------|-------|
   | Name | `facefind-backend` |
   | Root Directory | `backend` |
   | Runtime | `Docker` |
   | Instance Type | Free for demos; upgrade if face processing restarts |

5. **Add Environment Variables** (in Render dashboard):
   ```
   LOCAL_ONLY=false
   MONGODB_URL=mongodb+srv://<user>:<password>@<cluster-host>/facefind?retryWrites=true&w=majority
   MONGODB_DATABASE=facefind
   SECRET_KEY=your-strong-random-secret-key
   ADMIN_EMAIL=your-admin-email
   ADMIN_PASSWORD=your-strong-admin-password
   FACE_TOLERANCE=0.5
   FACE_MODEL=hog
   MAX_PROCESSING_DIM=1000
   MAX_BULK_UPLOAD=25
   CORS_ORIGINS=https://your-frontend.vercel.app
   DEBUG=False
   ```

6. Click **Deploy** → Wait for the Docker build and deployment to complete

7. Your backend URL will be similar to: `https://facefind-backend.onrender.com`

8. Verify the deployment at:
   - `https://facefind-backend.onrender.com/health`
   - `https://facefind-backend.onrender.com/docs`

9. Render free instances can sleep and can restart under memory pressure. Upload 5-10 photos at a time, keep `FACE_MODEL=hog`, and use a paid instance with persistent disk (or a VPS) before storing production photos.

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

6. Your live URL will be shown by Vercel. Add that exact URL to Render's `CORS_ORIGINS` and redeploy the backend if necessary.

7. Open the live frontend URL and verify admin login, event creation, a small
   photo upload, processing, public search, and multi-angle registration.

> Set `VITE_API_URL` before the Vercel build. It is embedded into the frontend
> at build time; changing it later requires a redeploy.

---

### Option 2: Railway.app (Alternative)

1. Go to [railway.app](https://railway.app) → Sign up with GitHub
2. **New Project** → Deploy from GitHub repo
3. Railway auto-detects Dockerfile for backend
4. Add frontend as second service
5. Set the MongoDB, JWT, face-processing, and CORS variables listed above
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
  -e MONGODB_URL=your-mongodb-url \
  -e MONGODB_DATABASE=facefind \
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
| **Face recognition** | Docker installs pre-built `dlib-bin` before `face-recognition`; keep `FACE_MODEL=hog` on small instances |
| **Free tier limits** | Render free instances can sleep after inactivity and have limited memory |
| **Processing** | Upload small batches; a restart stops in-process background tasks |
| **Persistent database** | MongoDB Atlas stores events, photo metadata, and encodings |
| **Persistent images** | Use a persistent backend disk or add object storage before production |
| **Render disk** | Free disk is temporary; never rely on it for permanent uploads |
| **HTTPS** | Both Render & Vercel give free SSL certificates |
| **CORS** | Set the exact Vercel URL in Render's `CORS_ORIGINS` |
| **Secrets** | Keep `backend/.env` out of Git and rotate credentials if exposed |

### Troubleshooting

#### Processing is stuck

Render restarts terminate FastAPI in-process background tasks. Deploy the latest code, open the event, and click **Restart processing**. If the service keeps restarting, reduce `MAX_PROCESSING_DIM` to `800`, set `MAX_BULK_UPLOAD=10`, upload smaller batches, and check Render logs for `free(): invalid size` or memory-limit messages.

#### Search returns 502 or a CORS error

Check Render logs first. A native face-recognition crash can produce a 502 response without CORS headers; the browser then reports it as a CORS error. Confirm the backend is healthy at `/health`, verify the event code, and ensure the frontend URL exactly matches `CORS_ORIGINS`.

#### Storage shows 0 MB

The dashboard reports the sum of photo sizes stored in MongoDB metadata. The
uploaded files themselves are read from the backend filesystem, so that
filesystem must be persistent for production use.

## 📜 License

MIT License — Free for academic and personal use.
