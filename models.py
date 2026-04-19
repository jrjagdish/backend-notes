from .db import Base
from sqlalchemy import Column,Integer,String,DateTime,UUID
from sqlalchemy.sql import func

class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID,primary_key=True,nullable=False)
    title = Column(String,nullable=False)
    subject = Column(String,nullable=False)
    semester = Column(String,nullable=False)
    pdf_url = Column(String,nullable=False)
    audio_url = Column(String,nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())