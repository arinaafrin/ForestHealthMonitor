# 🌲 Forest Health Monitor

Forest Health Monitor is a full-stack system that checks forest condition using free satellite data — no site visit needed. Draw a boundary on a map, pick a date range, and the system pulls Sentinel-2 satellite imagery via Google Earth Engine, calculates vegetation health indices, and flags stress by comparing the result against that region's own historical baseline.

## Features

- **Forest Registration** — Save forest regions with a name and boundary polygon (PostGIS).
- **Health Index Calculation** — Computes NDVI (greenness), NBR (burn severity), NDMI (moisture stress), and EVI (canopy density) directly from satellite bands.
- **Anomaly Detection** — Compares current scores against a region's own historical average to catch stress early.
- **History & Trends** — Every check is saved; a trend endpoint and chart show how a region changes over time.
- **PDF Reports** — Download a formatted health report for any check.
- **Caching** — Redis caches repeat queries for the same region and date range.
- **Docker-Ready, Multi-Service** — Backend, frontend, database, and cache each run as independent containers.
- **CI/CD** — Automated testing and image publishing via GitHub Actions.

## System Architecture

Browser
  │
  ▼
┌─────────────┐ /api/*            ┌──────────────┐
│ forest_web  │ ───────────────▶ │ forest_api    │
│ (Nginx + │  │                   | (FastAPI +   │      
│ React app)  │                   │ Gunicorn)    │
└─────────────┘                   └──────┬───────┘
                                         │
                    ┌────────────────────┼───────────────────┐
                    ▼                    ▼                   ▼
               ┌─────────────┐ ┌───────────────┐ ┌──────────────┐
               │forest_cache │ │forest_database│ │ Google Earth │
               │ (Redis)     │ │ (PostGIS)     │ │ Engine       │
               └─────────────┘ └───────────────┘ └──────────────┘


Only the frontend/proxy is internet-facing. The database, cache, and API communicate over a private Docker network.

## Project Structure

forest-health-monitor/
├── Dockerfile # Backend image (FastAPI + Gunicorn)
├── docker-compose.yml # Orchestrates all 4 services
├── requirements.txt
├── src/
│ ├── api/ # FastAPI routes, schemas, health check service
│ ├── db/ # SQLAlchemy models & session
│ ├── processing/ # Vegetation index math & anomaly detection
│ ├── ingestion/ # Google Earth Engine client
│ ├── cache/ # Redis client
│ └── reporting/ # PDF report generation
├── frontend/
│ ├── Dockerfile # Frontend image (Nginx + built React app)
│ ├── nginx.conf
│ └── src/
│ ├── pages/ # Dashboard, About
│ ├── components/ # MapDrawer, charts, badges
│ └── api/ # API client
├── tests/
│ ├── unit/
│ └── integration/
└── .github/workflows/ # CI/CD pipeline


## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Gunicorn + Uvicorn |
| Database | PostgreSQL + PostGIS |
| ORM | SQLAlchemy, GeoAlchemy2 |
| Cache | Redis |
| Satellite data | Google Earth Engine (Sentinel-2) |
| Frontend | React, Vite, Tailwind CSS, Chart.js |
| PDF reports | WeasyPrint |
| Testing | Pytest, Robot Framework (end-to-end) |
| Infrastructure | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Prerequisites

- Docker and Docker Compose
- A Google Earth Engine service account (`credentials/gee-key.json`) — see [Earth Engine setup docs](https://developers.google.com/earth-engine/guides/service_account)
- Python 3.12+ (only needed for running tests outside Docker)

## Quick Start

1. **Clone the repository:**
```bash
   git clone https://github.com/arinaafrin/ForestHealthMonitor.git
   cd ForestHealthMonitor
```

2. **Set up environment variables:**
   Create a `.env` file at the project root with your database, Redis, and Earth Engine credentials.

3. **Start all services:**
```bash
   docker compose up -d --build
```

4. **Open the app:**
   Visit `http://localhost` for the dashboard.

5. **Check the API directly (optional):**
```bash
   curl http://localhost/api/health
```

## Running Tests

```bash
docker compose up -d forest_database forest_cache
DATABASE_HOST=localhost REDIS_HOST=localhost REDIS_PORT=6380 pytest tests/ -v
```

## API Overview

| Endpoint | Description |
|---|---|
| `POST /regions` | Register a new forest region |
| `GET /regions` | List all saved regions |
| `POST /regions/{id}/health-check` | Run a health check for a date range |
| `GET /regions/{id}/history` | Get all past checks for a region, oldest to newest |
| `GET /regions/{id}/report.pdf` | Download a PDF report of the latest check |
| `GET /health` | Liveness check |

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
*Drawing a forest boundary and running a health check*

![Trend Chart](docs/screenshots/trend-chart.png)
*Tracking vegetation health over time*

![About Page](docs/screenshots/about-page.png)
*Project overview and system architecture*

## Future Work
JWT authentication, NDVI heatmap overlays, scheduled automatic checks, and an alerts system for regions that turn unhealthy. See the in-app About page for the full roadmap.

## License
MIT
