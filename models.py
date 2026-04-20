from db import Base
from sqlalchemy import Column,Integer,String,DateTime,UUID
from sqlalchemy.sql import func
import uuid

class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String,nullable=False)
    unit = Column(String)
    subject = Column(String,nullable=False)
    semester = Column(String,nullable=False)
    pdf_url = Column(String,nullable=False)
    audio_url = Column(String,nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())