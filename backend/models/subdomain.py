import uuid
from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Subdomain(Base):
    __tablename__ = "subdomains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(512), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    technologies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="subfinder")

    project = relationship("Project", back_populates="subdomains")
    urls = relationship("URL", back_populates="subdomain", cascade="all, delete-orphan")
    findings = relationship("NucleiFinding", back_populates="subdomain", cascade="all, delete-orphan")
