import requests
import json
import re
from app.core.config import settings

SYSTEM_PROMPT = """You are a highly capable QA Assistant for a Corrective RAG (CRAG) system.
Answer the user query based on the provided context chunks.
Do NOT make up any information.
Format your response using clean, well-spaced markdown:
- Use bullet points, bold text, or numbered lists for structure.
- Add clear spacing (empty lines) between paragraphs and sections.
- Be factual and concise.
- Cite the sources in your response by adding bracketed numbers like [1] or [2] matching the source index numbers.

If the context chunks do not contain enough information to answer the query, explain that you couldn't find the answer in the uploaded files, but answer using your own knowledge if possible, and make it clear that the information is from your own general knowledge.
"""

def generate_answer_via_llm(query: str, contexts: list, history: list = None) -> dict:
    if not contexts:
        return {
            "answer": "I could not find any relevant documents or search results to answer your query.",
            "provider": "none",
            "model": "none"
        }

    context_str = ""
    seen_sources = set()
    source_mapping = []
    
    ref_idx = 1
    for ctx in contexts:
        src = ctx.get("source") or "Local Document"
        if src not in seen_sources:
            seen_sources.add(src)
            source_mapping.append((ref_idx, src))
            ref_idx += 1
        curr_ref = [idx for idx, name in source_mapping if name == src][0]
        context_str += f"[{curr_ref}] {ctx.get('chunk') or ctx.get('snippet')}\n\n"

    user_content = f"Context chunks:\n{context_str}\nQuery: {query}\n\nAnswer:"

    if settings.GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if history:
                for h in history:
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_content})
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                answer = res.json()["choices"][0]["message"]["content"]
                answer = append_citations(answer, source_mapping)
                return {"answer": answer, "provider": "Groq", "model": "llama-3.3-70b-versatile"}
            else:
                print(f"Groq API error (status {res.status_code}): {res.text}")
        except Exception as e:
            print(f"Groq API connection failed: {e}")

    answer = generate_fallback_polished(query, contexts, source_mapping)
    return {"answer": answer, "provider": "Heuristics Engine (Fallback)", "model": "Rule-based Extractor"}

def generate_fallback_polished(query: str, contexts: list, source_mapping: list) -> str:
    """Heuristic summarizer fallback with improved spacing and structure."""
    keywords = [w.lower() for w in query.split() if len(w) > 3]
    sentences_found = []
    
    for ctx in contexts:
        chunk = ctx.get("chunk") or ctx.get("snippet") or ""
        chunk = re.sub(r'&[a-z]+;', ' ', chunk)
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        for s in sentences:
            s = s.strip()
            if len(s) < 25:
                continue
            if any(k in s.lower() for k in keywords):
                if s not in sentences_found:
                    sentences_found.append(s)

    lines = ["## Answer\n"]
    lines.append("> ⚠️ **Note:** No LLM API keys are configured or reachable in the backend `.env` file. Falling back to keyphrase extractions.\n")
    
    if sentences_found:
        lines.append("**Extracted key facts from sources:**\n")
        for s in sentences_found[:5]:
            lines.append(f"- {s}\n")
    else:
        lines.append("**Summary from documents:**\n")
        for ctx in contexts[:3]:
            chunk = (ctx.get("chunk") or ctx.get("snippet") or "").strip()
            if chunk:
                lines.append(f"- {chunk[:300]}...\n")
                
    return append_citations("\n".join(lines), source_mapping)

def append_citations(answer_body: str, source_mapping: list) -> str:
    """Append a nicely formatted Sources section to the answer."""
    citations = ["\n---\n**Sources:**\n"]
    for ref_idx, src in source_mapping:
        is_url = src.startswith("http") or src.startswith("//") or "www." in src or ".com" in src or ".org" in src
        if is_url:
            link = src if src.startswith("http") else ("https:" + src if src.startswith("//") else "https://" + src)
            label = link
            m = re.match(r'https?://([^/]+)', link)
            if m:
                label = m.group(1)
            citations.append(f"`[{ref_idx}]` [{label}]({link})\n")
        else:
            citations.append(f"`[{ref_idx}]` (Local Document) {src}\n")
    return answer_body + "\n" + "\n".join(citations)
