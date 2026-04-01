# 🏙️ CivicPulse — Crowdsourced Civic Reporting Platform

A full-stack web application where citizens can **report**, **upvote**, and **track** civic issues in their community — built with Python (Flask) and a modern HTML/CSS/JS frontend.

---

## 📁 Project Structure

```
civic-report/
├── app.py                  ← Flask backend (API + routes)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── instance/
│   └── civic_reports.db    ← SQLite database (auto-created)
└── templates/
    ├── base.html           ← Shared layout (nav, modals, auth)
    ├── index.html          ← Landing page
    ├── dashboard.html      ← Report browser with sidebar filters
    └── map.html            ← Interactive map view (Leaflet.js)
```

---

## 🚀 Setup & Run Instructions

### Step 1: Install Python
Make sure Python 3.9+ is installed:
```bash
python --version
```

### Step 2: Create a Virtual Environment (recommended)
```bash
# Create virtualenv
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the App
```bash
python app.py
```

### Step 5: Open in Browser
```
http://localhost:5000
```

That's it! The database and sample data are auto-created on first run.

---

## 🔑 Demo Accounts

Two accounts are pre-seeded for testing:

| Username       | Email             | Password     |
|----------------|-------------------|--------------|
| alex_citizen   | alex@city.com     | password123  |
| maria_reports  | maria@city.com    | password123  |

---

## ✨ Features

### For Citizens
- **Submit Reports** — Title, description, category, priority, location
- **Upvote Issues** — Vote on reports that affect you (one vote per user)
- **Add Comments** — Discuss issues and share updates
- **Track Status** — Open → In Progress → Resolved

### Pages
| Page        | URL          | Description |
|-------------|--------------|-------------|
| Landing     | `/`          | Hero, stats, recent reports, how-it-works |
| Dashboard   | `/dashboard` | Full report browser with filters + detail panel |
| Map         | `/map`       | Interactive Leaflet.js map of all geolocated issues |

### Categories
- 🛣 Roads & Potholes
- 💡 Street Lighting
- 🗑 Sanitation
- 🌊 Flooding & Drainage
- 🌳 Parks & Recreation
- 🎨 Vandalism
- ❓ Other

### Priority Levels
- Low / Medium / High / **Critical**

---

## 🛠 Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Python, Flask |
| Database   | SQLite via Flask-SQLAlchemy |
| Auth       | Flask sessions + Werkzeug password hashing |
| Frontend   | HTML5, CSS3, Vanilla JavaScript |
| Maps       | Leaflet.js + OpenStreetMap tiles |
| Icons      | Font Awesome 6 |
| Fonts      | Google Fonts (Syne + DM Sans) |

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/me` | Current user |
| GET | `/api/reports` | List reports (filter: category, status, sort) |
| POST | `/api/reports` | Create report (auth required) |
| GET | `/api/reports/<id>` | Get report + comments |
| POST | `/api/reports/<id>/vote` | Toggle upvote |
| POST | `/api/reports/<id>/comment` | Add comment |
| PATCH | `/api/reports/<id>/status` | Update status (owner only) |
| GET | `/api/stats` | Dashboard statistics |

---

## 🔧 Customization

### Change Port
```python
app.run(debug=True, port=8080)  # in app.py last line
```

### Use PostgreSQL (production)
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/civicpulse'
```

### Add Real Map Coordinates
When submitting reports via API, pass `latitude` and `longitude` fields and they'll appear on the map automatically.

---

## 📦 Production Deployment (Optional)

```bash
pip install gunicorn
gunicorn -w 4 app:app
```

Use Nginx as reverse proxy and set `SECRET_KEY` to a secure random string in production.
