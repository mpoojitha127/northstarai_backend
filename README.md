# NorthStar AI - Backend

## Overview

NorthStar AI Backend is a FastAPI-based REST API that powers the NorthStar AI application. It provides authentication, goal management, AI chat, dashboard data, recommendations, and strategic alignment features.

---

## Features

- User Authentication (JWT)
- Goal Management
- AI Chat Integration
- Dashboard APIs
- Recommendation Engine
- Strategic Alignment Engine
- Semantic Memory
- RESTful APIs
- SQLAlchemy ORM
- Alembic Database Migrations

---

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- ChromaDB
- Google Gemini API
- Pydantic

---

## Project Structure

backend/
├── app/
│ ├── api/
│ ├── core/
│ ├── db/
│ ├── models/
│ ├── schemas/
│ ├── services/
│ └── main.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md

---

## Installation

### Clone Repository

```bash
git clone https://github.com/mpoojitha127/northstarai-backend.git
cd northstarai-backend