"""
A "forest record" looks like inside the database. Each class below as one table, and each line inside a class as one column in that table.
"""

import enum
import uuid
from datetime import datetime, timezone
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

class DatabaseBase(DeclarativeBase):
    """ Base class that registers and connects all database tables to SQLAlchemy ORM """
    pass

class ForestHealthStatus(str, enum.Enum):
    HEALTHY = "healthy"
    MODERATE_STRESS = "moderate_stress"
    SEVERE_STRESS = "severe_stress"
    UNKNOWN = "unknown"
class User(DatabaseBase):
    """ one person who can log in and register forests """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    scrambled_password = Column(String(255), nullable=False)
    joined_on = Column(DateTime, default=datetime.utcnow)
    
class ForestRegion(DatabaseBase):
    """ One forest area the user is tracking """
    __tablename__ = "forest_regions"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(255), nullable=False, unique=True)
    border_shape = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    added_on     = Column(DateTime, default=datetime.now(timezone.utc))

    satellite_checks = relationship("SatelliteCheck", back_populates="region")

class SatelliteCheck(DatabaseBase):
    """ One satellite reading for one region, on one date """
    __tablename__ = "satellite_checks"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id = Column(UUID(as_uuid=True), ForeignKey("forest_regions.id"), nullable=False)
    checked_on  = Column(DateTime, nullable=False)

    greenness_score       = Column(Float, nullable=False)
    burn_severity_score   = Column(Float, nullable=True)
    moisture_stress_score = Column(Float, nullable=True)
    canopy_density_score  = Column(Float, nullable=True)
    cloud_cover_percent   = Column(Float, default=0.0)

    region        = relationship("ForestRegion", back_populates="satellite_checks")
    health_result = relationship("HealthAssessment", back_populates="satellite_check", uselist=False)

class HealthAssessment(DatabaseBase):
    """ The final health decision for one satellite check """
    __tablename__ = "health_assessments"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    satellite_check_id = Column(UUID(as_uuid=True), ForeignKey("satellite_checks.id"), nullable=False)

    status             = Column(
                            Enum(
                                ForestHealthStatus,
                                name="foresthealthstatus",
                                values_callable=lambda enum_class: [member.value for member in enum_class],
                            ),
                            nullable=False,
                            default=ForestHealthStatus.UNKNOWN,
                        )
    steps_away_from_normal = Column(Float, nullable=False)
    decided_on             = Column(DateTime, default=datetime.now(timezone.utc))

    satellite_check = relationship("SatelliteCheck", back_populates="health_result") 