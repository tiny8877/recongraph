import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class NucleiFinding(Base):
    __tablename__ = "nuclei_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    subdomain_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subdomains.id", ondelete="SET NULL"), nullable=True)
    template_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    matched_at: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="findings")
    subdomain = relationship("Subdomain", back_populates="findings")
