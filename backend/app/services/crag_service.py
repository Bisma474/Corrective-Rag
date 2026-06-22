import os
import json
import urllib.parse
import urllib.request
import re
from app.services.document_service import vector_db, get_embedding_model, extract_text_from_file
from app.services.llm_service import generate_answer_via_llm
import numpy as np

# A lightweight free search client utilizing DuckDuckGo HTML search
def web_search(query: str, max_results: int = 4):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Parse links and snippets
        links = re.findall(r'class="result__snippet"[^>]*href="([^"]+)"', html)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)
        
        results = []
        for i in range(min(len(snippets), max_results)):
            snippet_clean = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            snippet_clean = urllib.parse.unquote(snippet_clean)
            
            raw_link = links[i] if i < len(links) else ""
            clean_link = raw_link
            
            # Clean up DuckDuckGo redirect link wrapping
            if "uddg=" in raw_link:
                match = re.search(r'uddg=([^&]+)', raw_link)
                if match:
                    clean_link = urllib.parse.unquote(match.group(1))
            elif raw_link.startswith("//"):
                clean_link = "https:" + raw_link
                
            results.append({
                "snippet": snippet_clean,
                "url": clean_link
            })
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []

def evaluate_relevance(query: str, chunk: str) -> float:
    # Use embedding cosine similarity between query and chunk as a basic evaluator
    model = get_embedding_model()
    q_emb = model.encode([query])[0]
    c_emb = model.encode([chunk])[0]
    
    q_norm = np.linalg.norm(q_emb)
    c_norm = np.linalg.norm(c_emb)
    if q_norm == 0 or c_norm == 0:
        return 0.0
    return float(np.dot(q_emb, c_emb) / (q_norm * c_norm))

def query_rewriter(query: str) -> str:
    # Basic rule-based cleaner to remove conversational filler words for search optimization
    clean = re.sub(r'\b(please|tell|me|about|what|is|find|search|for|how|do|i)\b', '', query, flags=re.IGNORECASE)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else query

def _shorten_source(source: str) -> str:
    """Return a readable label for a source URL or filename."""
    if source.startswith("http"):
        # Extract domain name only
        m = re.match(r'https?://([^/]+)', source)
        return m.group(1) if m else source[:60]
    return source

# generate_answer_local has been removed; generation is now handled by llm_service.py


def run_crag_pipeline(query: str, user_id: int, conn):
    logs = []
    logs.append({"step": "RETRIEVAL", "message": "Initiating local database vector search."})
    
    # Fetch file metadata mapping for citations and vector search isolation
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename FROM documents WHERE user_id = ?", (user_id,))
    doc_mapping = {row["id"]: row["filename"] for row in cursor.fetchall()}

    # 1. Retrieve candidates — use top_k=5 for more coverage
    candidates = vector_db.search(query, top_k=5, doc_ids=list(doc_mapping.keys()))
    
    graded_candidates = []
    best_score = 0.0
    
    for c in candidates:
        score = evaluate_relevance(query, c["chunk"])
        filename = doc_mapping.get(c["doc_id"], "Local File")
        graded_candidates.append({
            "chunk": c["chunk"],
            "score": score,
            "source": filename
        })
        if score > best_score:
            best_score = score

    logs.append({
        "step": "EVALUATION",
        "message": f"Retrieved {len(candidates)} local passages. Best relevance score: {best_score:.3f} (threshold: 0.18)"
    })

    # CRAG Grading — threshold lowered to 0.18 so conversational questions are matched
    RELEVANCE_THRESHOLD = 0.18
    is_correct = best_score >= RELEVANCE_THRESHOLD

    if is_correct:
        # Use all chunks above a soft lower threshold (0.15) for more context
        final_contexts = [c for c in graded_candidates if c["score"] >= 0.15]
        logs.append({
            "step": "DECISION",
            "message": f"PASSED (score {best_score:.3f} >= {RELEVANCE_THRESHOLD}). Answering from your uploaded documents."
        })
    else:
        logs.append({
            "step": "DECISION",
            "message": f"FAILED (score {best_score:.3f} < {RELEVANCE_THRESHOLD}). No relevant local content found — triggering web search fallback."
        })
        
        # Rewrite query for search
        rewritten_query = query_rewriter(query)
        logs.append({"step": "QUERY_REWRITE", "message": f"Query rewritten to: '{rewritten_query}'"})
        
        # Web search fallback
        web_results = web_search(rewritten_query, max_results=4)
        logs.append({"step": "WEB_SEARCH", "message": f"DuckDuckGo search returned {len(web_results)} web results."})
        
        final_contexts = []
        for w in web_results:
            final_contexts.append({
                "chunk": w["snippet"],
                "source": w["url"] or "Web Result"
            })
            
        # Merge any partially relevant local chunks (score > 0.3)
        for c in graded_candidates:
            if c["score"] > 0.3:
                final_contexts.append(c)

    # 4. Generate Answer
    llm_result = generate_answer_via_llm(query, final_contexts)
    answer = llm_result["answer"]
    provider = llm_result["provider"]
    model = llm_result["model"]
    logs.append({
        "step": "GENERATION",
        "message": f"Synthesized final response using {provider} ({model})."
    })
    
    return {
        "answer": answer,
        "logs": logs,
        "contexts": final_contexts
    }
