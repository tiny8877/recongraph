import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    root_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    subdomains = relationship("Subdomain", back_populates="project", cascade="all, delete-orphan")
    urls = relationship("URL", back_populates="project", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="project", cascade="all, delete-orphan")
    findings = relationship("NucleiFinding", back_populates="project", cascade="all, delete-orphan")
    scan_jobs = relationship("ScanJob", back_populates="project", cascade="all, delete-orphan")
