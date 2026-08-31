# Forest Health Monitor

Forest Health Monitor is a lightweight tool that helps track forest condition using free satellite data. It calculates vegetation health indices and flags potential stress by comparing new data with a forest's historical baseline.

## Features

- **Forest Registration:** Save forest regions using a name and boundary coordinates (PostGIS polygon support).
- **Health Index Calculation:** Compute core vegetation health metrics directly from satellite bands.
- **Anomaly Detection:** Compare current vegetation levels against historical regional data to identify stress early.
- **Data Persistence:** Store checks over time to build a history for each registered forest.
- **Docker Ready:** Built to run consistently in a containerized setup.

## Project Structure

- `Module 1: Vegetation Health Index Calculator` - Pure math module for computing health scores.
- `Module 2: Health Anomaly Detector` - Logic to evaluate current scores against historical averages.
- `Module 3: Forest Data Storage` - PostgreSQL + PostGIS integration for saving boundary shapes and check history.

## Tech Stack

- **Language:** Python 3.11+
- **Database:** PostgreSQL with PostGIS extension
- **ORM:** SQLAlchemy & GeoAlchemy2
- **Testing:** Pytest

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for the PostGIS database)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/forest-health-monitor.git](https://github.com/your-username/forest-health-monitor.git)
   cd forest-health-monitor