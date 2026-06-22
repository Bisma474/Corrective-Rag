from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.database import get_db_connection
from app.routers.auth import get_current_user_id
from app.services.crag_service import run_crag_pipeline
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])

class QuerySchema(BaseModel):
    query: str
    conversation_id: int

class ConversationCreateSchema(BaseModel):
    title: str

@router.get("/sessions")
def list_conversations(user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"]} for r in rows]

@router.post("/sessions")
def create_conversation(data: ConversationCreateSchema, user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (user_id, data.title))
        conv_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database conversation creation error: {e}")
    conn.close()
    return {"id": conv_id, "title": data.title}

@router.get("/sessions/{conv_id}/messages")
def get_messages(conv_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Authenticate ownership
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    cursor.execute("SELECT role, content, logs, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conv_id,))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        messages.append({
            "role": r["role"],
            "content": r["content"],
            "logs": json.loads(r["logs"]) if r["logs"] else None,
            "created_at": r["created_at"]
        })
    return messages

@router.post("/query")
def submit_query(data: QuerySchema, user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Authenticate ownership
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (data.conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Save User message
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (data.conversation_id, "user", data.query)
    )
    conn.commit()
    
    # Execute CRAG Pipeline
    pipeline_result = run_crag_pipeline(data.query, user_id, conn)
    
    # Save Assistant message
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, logs) VALUES (?, ?, ?, ?)",
        (data.conversation_id, "assistant", pipeline_result["answer"], json.dumps(pipeline_result["logs"]))
    )
    conn.commit()
    conn.close()
    
    return {
        "answer": pipeline_result["answer"],
        "logs": pipeline_result["logs"]
    }
