import os
import json
import re
import requests
from app.services.document_service import vector_db, extract_text_from_file
from app.services.llm_service import generate_answer_via_llm

def web_search(query: str, max_results: int = 4):
    try:
        from duckduckgo_search import DDGS
        for backend in ["api", "html", "lite"]:
            try:
                with DDGS(backend=backend, timeout=10) as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return [{"snippet": r["body"], "url": r["href"]} for r in results]
            except Exception:
                continue
    except Exception as e:
        print(f"DDG library not available: {e}")

    try:
        res = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "srprop": "snippet|titlesnippet",
            },
            timeout=10,
            headers={"User-Agent": "CRAG-App/1.0"},
        )
        data = res.json()
        results = []
        for item in data.get("query", {}).get("search", []):
            snippet = re.sub(r'<[^>]+>', "", item.get("snippet", ""))
            title = item.get("title", "")
            page_id = item.get("pageid", "")
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            if snippet:
                results.append({"snippet": snippet[:500], "url": url})
        if results:
            return results
    except Exception as e:
        print(f"Wikipedia search failed: {e}")

    return []

def query_rewriter(query: str) -> str:
    clean = re.sub(r'\b(please|tell|me|about|what|is|find|search|for|how|do|i|can|you)\b', '', query, flags=re.IGNORECASE)
    clean = re.sub(r'[?]+', '', clean)
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


def run_crag_pipeline(query: str, user_id: int, conn, history: list = None):
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
        score = c["score"]
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
        logs.append({"step": "WEB_SEARCH", "message": f"Web search returned {len(web_results)} results."})
        
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
    llm_result = generate_answer_via_llm(query, final_contexts, history)
    answer = llm_result["answer"]
    provider = llm_result["provider"]
    model = llm_result["model"]
    if not final_contexts:
        logs.append({
            "step": "GENERATION",
            "message": "No context found from documents or web. Using Groq's general knowledge to answer."
        })
    else:
        logs.append({
            "step": "GENERATION",
            "message": f"Synthesized final response using {provider} ({model})."
        })
    
    return {
        "answer": answer,
        "logs": logs,
        "contexts": final_contexts
    }
