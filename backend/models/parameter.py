import uuid
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Parameter(Base):
    __tablename__ = "parameters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url_id: Mapped[str] = mapped_column(String(36), ForeignKey("urls.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_value: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attack_types: Mapped[list] = mapped_column(JSON, default=list)

    url = relationship("URL", back_populates="parameters")
    project = relationship("Project", back_populates="parameters")
