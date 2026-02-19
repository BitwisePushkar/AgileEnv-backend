# Agile Backend

A minimalist, Jira-inspired project management backend powered by **FastAPI**.
Designed around scalable Agile workflows — workspaces → projects → boards → issues → sprints.

---

## Tech Stack

`FastAPI : Python : PostgreSQL : SQLAlchemy : Redis : JWT : OAuth2 : AWS S3 : Docker`

---

## Core Functionality

### Auth

Register · Login · Logout · Refresh Token · Password Reset · Email Verification

### Users

Profile Management · Avatar Upload · Public Profiles · Account Control

### Workspace

Create · Manage · Invite · Roles · Member Control · Ownership Transfer

### Projects

Workspace Projects · Members & Roles · Archive Control

### Boards

Kanban / Scrum Boards · Columns · Reordering

### Issues

Create · Assign · Prioritize · Filter · Move Across Columns
Subtasks · Epics · Status Flow · Archive

### Labels

Tagging System · Color-coded Labels

### Comments

Threaded Discussions on Issues

### Attachments

File Uploads via S3

### Notifications

Real-time Alerts · Preferences · Unread Counts

### Activity Logs

Issue History · Project Feed · Workspace Audit

### Sprints

Sprint Lifecycle · Issue Movement

### Chat

Workspace Chatrooms · Messaging · Member Control

### Dashboard

Workspace & Project Stats · Personal Work Summary

---

## Structure

```
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── readme.md
└── app/
    ├── main.py
    ├── config.py
    ├── auth/
    ├── chat/
    ├── workspace/
    └── utils/
```

---

## ▶ Setup (Local)

```bash
git clone <repo>
cd agile-backend
python -m venv venv
source venv/bin/activate   # windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs → `http://127.0.0.1:8000/api/docs`

---

## 🐳 Setup (Docker)

```bash
docker-compose up --build
```
---