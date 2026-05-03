import os
import tempfile
import uuid
import gtts
import fitz  # PyMuPDF
import requests
from fastapi import FastAPI, Depends, File, HTTPException, BackgroundTasks, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import cloudinary.uploader
from db import get_db, engine, Base
from models import Note
from db import SessionLocal

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from db import SessionLocal # Import your SessionLocal factory directly

def process_tts_task(note_id: str): # Note: Use str or int based on your DB type
    """Heavy background task to convert PDF text to Audio."""
    # Create a fresh session specifically for this background thread
    db = SessionLocal() 
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note or not note.pdf_url:
            print("Note not found or PDF URL missing")
            return

        # 1. Get PDF Content
        response = requests.get(note.pdf_url, timeout=30)
        pdf_doc = fitz.open(stream=response.content, filetype="pdf")
        text = "\n".join([page.get_text() for page in pdf_doc])
        pdf_doc.close()

        if not text.strip():
            print("No text found in PDF")
            return

        # 2. TTS Generation
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            temp_path = tmp.name
            tts = gtts.gTTS(text[:15000], lang='en') 
            tts.save(temp_path)

        # 3. Cloudinary Upload (using 'video' resource_type for audio)
        with open(temp_path, "rb") as f:
            upload = cloudinary.uploader.upload(
                f, 
                resource_type="video", 
                public_id=f"audio_summaries/note_{note_id}",
                overwrite=True
            )

        # 4. Update Record
        note.audio_url = upload.get("secure_url")
        db.commit()
        print(f"TTS Success for note {note_id}")

    except Exception as e:
        print(f"Background TTS Failure: {e}")
    finally:
        db.close() # Always close the session in background tasks

@app.post("/notes/{note_id}/text-to-speech")
async def start_tts(note_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note.audio_url:
        return {"status": "ready", "audio_url": note.audio_url}

    # Trigger task - don't pass 'db' session from the request, 
    # let the task create its own.
    background_tasks.add_task(process_tts_task, note_id)
    
    return {
        "status": "processing", 
        "estimated_time": "20-40 seconds",
        "message": "AI voice generation started."
    }

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
        resource_type="image",
        public_id=f"user_docs/{title.replace(' ', '_')}",
        overwrite=True,
        format="pdf"
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



# @app.delete("/notes/{note_id}")
# def delete_note(note_id: str, db: Session = Depends(get_db)):
#     note = db.query(Note).filter(Note.id == note_id).first()
#     if not note:
#         raise HTTPException(status_code=404, detail="Note not found")
    
#     db.delete(note)
#     db.commit()
    
#     return {"message": "Note deleted successfully"}