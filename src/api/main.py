import logging
import os 
import ee  
from uuid import UUID
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager  
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from shapely.geometry import shape
from shapely.errors import GEOSException
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import date
from fastapi.responses import Response

from src.api.schemas import HealthCheckRequest, HealthCheckResponse, HistoryPointResponse, NewRegionRequest, RegionResponse
from src.db.models import ForestRegion, SatelliteCheck
from src.db.session import get_database_connection
from src.cache.redis_client import build_cache_key, load_from_cache, save_to_cache
from src.api.health_check_service import run_full_forest_health_check
from src.ingestion.earth_engine_client import get_ndvi_tile_url
from src.processing.geometry_utils import _shape_to_geojson
from src.reporting.pdf_report import build_report_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Check for required environment variables
@asynccontextmanager
async def lifespan(app: FastAPI):
    service_account = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not service_account or not credentials_path:
        logging.error("Earth Engine configuration missing from environment variables!")
    else:
        try:
            credentials = ee.ServiceAccountCredentials(
                email=service_account,
                key_file=credentials_path
            )
            ee.Initialize(credentials)
            logging.info("Google Earth Engine successfully initialized!")
        except Exception as e:
            logging.error(f"Failed to initialize Google Earth Engine: {e}")
            
    yield


# Initialize FastAPI application
app = FastAPI(title="Forest Health Monitor", lifespan=lifespan)

# FastAPI application setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/regions", response_model=RegionResponse, status_code=201)
def register_new_forest_region(
    request: NewRegionRequest, db: Session = Depends(get_database_connection)
):
    try:
        border = shape(request.border_shape_geojson)
    except (GEOSException, ValueError):
        raise HTTPException(
            status_code=422, detail="The border shape is not a valid polygon"
        )

    try:
        new_region = ForestRegion(
            name=request.name,
            border_shape=from_shape(border, srid=4326)
        )
        db.add(new_region)
        db.commit()
        db.refresh(new_region)
        return new_region
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=f"A region named '{request.name}' already exists"
        )
    except Exception as e:
        db.rollback()
        print(f"Database insertion failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create region in database"
        )

@app.get("/regions", response_model=list[RegionResponse])
def list_all_forest_regions(db: Session = Depends(get_database_connection)):
    return db.query(ForestRegion).all()

@app.get("/regions/{region_id}", response_model=RegionResponse)
def get_one_forest_region(region_id: str, db: Session = Depends(get_database_connection)):
    cache_key = build_cache_key("region", region_id)
    cached_result = load_from_cache(cache_key)

    if cached_result is not None:
        return cached_result

    region = db.query(ForestRegion).filter(ForestRegion.id == region_id).first()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    result = RegionResponse.model_validate(region).model_dump()
    save_to_cache(cache_key, result)
    return result

@app.post("/regions/{region_id}/health-check", response_model=HealthCheckResponse, status_code=201)
def check_forest_health_now(
    region_id: UUID, 
    request: HealthCheckRequest, 
    db: Session = Depends(get_database_connection)
):
    try:
        region = db.query(ForestRegion).filter(ForestRegion.id == region_id).first()
    except Exception as e:
        print(f"Database lookup failed for region {region_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Database communication failure during region lookup"
        )

    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    try:
        result = run_full_forest_health_check(
            db, region, request.start_date, request.end_date, request.max_cloud_percent
        )
        return result
    except Exception as e:
        db.rollback()  
        print(f"Health check execution failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute health check analysis: {str(e)}"
        )

@app.get("/regions/{region_id}/history", response_model=list[HistoryPointResponse])
def get_forest_health_history(region_id: UUID, db: Session = Depends(get_database_connection)):
    try:
        region = db.query(ForestRegion).filter(ForestRegion.id == region_id).first()
    except Exception as e:
        print(f"Database lookup failed for region {region_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Database communication failure during region lookup"
        )

    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    try:
        history_points = (
            db.query(SatelliteCheck)
            .filter(SatelliteCheck.region_id == region_id)
            .order_by(SatelliteCheck.checked_on.asc())
            .all()
        )
        return history_points
    except Exception as e:
        print(f"Failed to retrieve health history for region {region_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve health history: {str(e)}"
        )

@app.get("/regions/{region_id}/ndvi-tiles")
def get_ndvi_tiles(region_id: UUID, start_date: date, end_date: date, db: Session = Depends(get_database_connection)):
    region = db.query(ForestRegion).filter(ForestRegion.id == region_id).first()
    if region is None:
        raise HTTPException(404, "Region not found")
    geojson = _shape_to_geojson(region.border_shape)   
    return {"tile_url": get_ndvi_tile_url(geojson, start_date, end_date)}

@app.get("/regions/{region_id}/report.pdf")
def download_report(region_id: UUID, db: Session = Depends(get_database_connection)):
    region = db.query(ForestRegion).filter(ForestRegion.id == region_id).first()
    latest = (db.query(SatelliteCheck).filter(SatelliteCheck.region_id == region_id)
              .order_by(SatelliteCheck.checked_on.desc()).first())
    if not region or not latest:
        raise HTTPException(404, "No report data yet for this region")
    pdf_bytes = build_report_pdf(region.name, {
        "checked_on": latest.checked_on, "greenness": latest.greenness_score,
        "burn_severity": latest.burn_severity_score, "moisture_stress": latest.moisture_stress_score,
        "canopy_density": latest.canopy_density_score, "status": latest.health_result.status.value,
    })
    return Response(pdf_bytes, media_type="application/pdf",
                     headers={"Content-Disposition": f'attachment; filename="{region.name}_report.pdf"'})