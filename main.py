import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Form
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db import get_db,engine,Base
from models import Note
import cloudinary.uploader
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Be specific to your Vite port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"message": "API working good"}




@app.post("/add_notes")
def add_notes(
    title: str = Form(...),
    unit: str = Form(None),
    subject: str = Form(...),
    semester: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    result = cloudinary.uploader.upload(
        file=file.file,
        resource_type="raw",
        public_id=f"user_docs/{title.replace(' ', '_')}",
        overwrite=True,
    )

    db_notes = Note(
        title=title,
        unit=unit,
        subject=subject,
        semester=semester,
        pdf_url=result.get("secure_url"),
    )
    db.add(db_notes)
    db.commit()
    db.refresh(db_notes)

    return {"message": "Notes added successfully"}

@app.get("/notes/{note_id}")
def get_note(note_id: uuid.UUID, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.pdf_url

@app.get("/notes")
def get_all_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return notes