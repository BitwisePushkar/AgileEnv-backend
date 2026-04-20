# Agile Backend

A minimalist, Jira-inspired project management backend powered by **FastAPI**.
Designed around scalable Agile workflows — **workspaces → projects → boards (Kanban / Scrum) → issues → sprints**.

---

## Tech Stack

`FastAPI : Python : PostgreSQL : SQLAlchemy : Redis : Celery : Celery Beat : JWT : OAuth2 : AWS S3 : Docker`

---

## Core Functionality

### Auth

Register · Login · Logout · Refresh Token · Password Reset · Email Verification
**Google OAuth · GitHub OAuth (Web & App)**

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

File Uploads via **AWS S3**

### Notifications

Real-time Alerts · Preferences · Unread Counts

### Activity Logs

Issue History · Project Feed · Workspace Audit

### Sprints

Sprint Lifecycle · Issue Movement

### Chat

Workspace Chatrooms · Messaging · Member Control

### WhiteBoard

Live drawing & updates · Cursor tracking (multi-user) · Undo support · History tracking (last 30 days)

### Dashboard

Workspace & Project Stats · Personal Work Summary

---

## Background Tasks

Powered by **Celery + Redis**

Email Sending · Notifications · Scheduled Jobs · Reminder Emails

---
## Upcoming feature

Payments & Billing · Subscription plans (Free / Pro / Team) · Invoice generation · Payment history

---

## ▶ Setup (Local)

```bash
git clone <repo>
cd agile-backend

# Initialize and install dependencies with uv
uv sync

# Run the project
uv run uvicorn app.main:app --reload --port 80
```

Docs → http://psinghal01.me/api/docs (or http://localhost/api/docs)

---

## 🐳 Setup (Docker)

```bash
docker-compose up --build
```