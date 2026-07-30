# MediAssist AI

MediAssist AI is a production-quality, responsive web application designed to help users during medical emergencies by providing AI symptom classification, Leaflet mapping for nearby hospital search, first aid directives, and emergency dials.

---

## Technical Architecture

*   **Frontend:** React (Vite) + TailwindCSS v4 + Leaflet Maps + Axios + Lucide Icons
*   **Backend:** FastAPI (Python) + SQLAlchemy ORM + SQLite / PostgreSQL
*   **AI:** Gemini Pro AI integration
*   **Maps:** Nominatim OpenStreetMap (Geocoding) + Overpass QL API (Hospital search)

---

## Folder Structure

```text
mediassist-ai/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints (analyze, hospitals, conditions, contacts)
│   │   ├── core/                   # Base configurations
│   │   ├── db/                     # ORM Models and SQLite Connection
│   │   ├── schemas/                # Pydantic validation structures
│   │   ├── services/               # Gemini AI & OpenStreetMap Overpass scripts
│   │   ├── data/                   # conditions.json (100 unique rows) and contacts
│   │   └── main.py                 # FastAPI application
│   ├── requirements.txt            # Python environments
│   └── generate_conditions.py      # Seed generator
└── frontend/
    ├── src/
    │   ├── components/             # Navbar, Footer, Chat, Maps, Contacts components
    │   ├── pages/                  # Home, Analyzer, Hospitals, KnowledgeBase page views
    │   ├── services/               # Axios API client wrapper
    │   └── App.jsx                 # View state container
```

---

## Local Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.9+** and **Node.js 18+** installed.

### 2. Run the Backend
Navigate to the `backend` folder:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 generate_conditions.py # Generates conditions.json
# Create .env and set GEMINI_API_KEY if desired
uvicorn app.main:app --reload
```
The backend will launch on `http://127.0.0.1:8000`.

### 3. Run the Frontend
Navigate to the `frontend` folder:
```bash
cd ../frontend
npm install
npm run dev
```
The client will start on `http://localhost:5173`.

---

## Deployment Guidelines

### 1. Database Setup (Supabase)
1. Register/Login to [Supabase](https://supabase.com/).
2. Create a new project and select **PostgreSQL**.
3. Under Database Settings, copy the URI string `postgresql://...`
4. Set the backend connection config:
   `DATABASE_URL=postgresql+asyncpg://postgres:[your-password]@db.[ref].supabase.co:5432/postgres`

### 2. Backend Deployment (Render)
1. Log in to [Render](https://render.com/).
2. Click **New +** -> **Web Service**.
3. Link your Github Repository containing the project folder.
4. Set settings:
   *   **Runtime:** `Python`
   *   **Build Command:** `pip install -r requirements.txt`
   *   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. In Environment Variables, set:
   *   `DATABASE_URL` = (Your Supabase PostgreSQL Connection String)
   *   `GEMINI_API_KEY` = (Your Gemini API Key)
   *   `FRONTEND_URL` = (Your production frontend URL)

### 3. Frontend Deployment (Vercel)
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New** -> **Project**.
3. Import your project repository.
4. Set settings:
   *   **Framework Preset:** `Vite`
   *   **Root Directory:** `frontend`
   *   **Build Command:** `npm run build`
   *   **Output Directory:** `dist`
5. Add Environment Variables:
   *   `VITE_API_URL` = (Your deployed Render backend API URL + `/api`)
