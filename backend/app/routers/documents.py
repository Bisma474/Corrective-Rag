from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import shutil
from app.core.config import settings
from app.core.database import get_db_connection
from app.routers.auth import get_current_user_id
from app.services.document_service import vector_db, extract_text_from_file

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("")
def list_documents(user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, uploaded_at FROM documents WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [{"id": r["id"], "filename": r["filename"], "uploaded_at": r["uploaded_at"]} for r in rows]

@router.post("/upload")
def upload_document(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".pdf", ".md"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported extensions: .pdf, .txt, .md")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save file metadata in db
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._- "]).strip()
    dest_path = os.path.join(settings.STORAGE_DIR, f"{user_id}_{safe_filename}")
    
    # Save file to disk
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"File save error: {e}")
        
    # Save database entry
    try:
        cursor.execute(
            "INSERT INTO documents (user_id, filename, file_path) VALUES (?, ?, ?)",
            (user_id, safe_filename, dest_path)
        )
        doc_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        os.remove(dest_path)
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database upload save error: {e}")
        
    # Chunk and embed
    try:
        text = extract_text_from_file(dest_path)
        if text.strip():
            vector_db.add_document(doc_id, text)
        else:
            raise Exception("File is empty or contains no extractable text.")
    except Exception as e:
        # Rollback
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=422, detail=f"Indexing failed: {e}")
        
    conn.close()
    return {"message": f"Successfully uploaded and indexed '{safe_filename}'."}

@router.delete("/{doc_id}")
def delete_document(doc_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_path FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=444, detail="Document not found or access denied")
        
    file_path = row["file_path"]
    
    # Delete from DB
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    
    # Delete from local vector db index
    vector_db.delete_document(doc_id)
    
    # Delete from disk
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return {"message": "Document deleted successfully."}
