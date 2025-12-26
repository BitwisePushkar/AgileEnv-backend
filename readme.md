# 🚀 Jira-Inspired Project Management Backend (FastAPI)

A backend service inspired by **Jira**, built with **FastAPI**, supporting **JWT authentication**, **Google & GitHub OAuth**, and **AWS S3 profile storage**.
The project is designed to be modular and scalable, with more features planned.

---

## ✨ Features (Current)

* 🔐 Authentication

  * JWT-based authentication
  * Google OAuth
  * GitHub OAuth
* 👤 User Profile

  * Profile management
  * Profile image upload using AWS S3
---

## 🏗️ Tech Stack

* **FastAPI**
* **Python**
* **JWT**
* **OAuth 2.0 (Google, GitHub)**
* **AWS S3**
* **Docker / Docker Compose**
* **Redis** 
* **PostgreSQL / SQLAlchemy** 

---

## 📂 Project Structure

```
.
│── .env
│── .env.example
│── config.py
│── main.py
│
├── auth
│   ├── crud.py
│   ├── router.py
│   ├── githubrouter.py
│   ├── googlerouter.py
│   ├── models.py
│   └── schemas.py
│
├── workspace
│   ├── crud.py
│   ├── model.py
│   ├── routers.py
│   └── schemas.py
│
├── utils
│   ├── dbUtil.py
│   ├── emailUtil.py
│   ├── githubUtil.py
│   ├── googleUtil.py
│   ├── JWTUtil.py
│   ├── passUtil.py
│   ├── redisUtils.py
│   └── S3Util.py
│
└── __pycache__
```

---

## ⚙️ Environment Variables

Create a `.env` file using `.env.example` as reference.

Example:

```
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BUCKET_NAME=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

---

## ▶️ Running the Project (Local)

### 1️⃣ Install dependencies

```
pip install -r app/requirements.txt
```

### 2️⃣ Run the server

```
uvicorn app.main:app --reload
```

API will be available at:

```
http://127.0.0.1:8000
```

Swagger Docs:

```
http://127.0.0.1:8000/docs
```

---

## 🐳 Running with Docker

### Build & start containers

```
docker-compose up --build
```

---

## 🧠 Planned Features

* Boards, issues, and task management
* Role-based access control
* Activity logs
* Notifications
* Team collaboration
* WebSocket updates

---