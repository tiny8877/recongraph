import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subdomain_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subdomains.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    full_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, default="/")
    source: Mapped[str] = mapped_column(String(50), default="waybackurls")

    project = relationship("Project", back_populates="urls")
    subdomain = relationship("Subdomain", back_populates="urls")
    parameters = relationship("Parameter", back_populates="url", cascade="all, delete-orphan")
