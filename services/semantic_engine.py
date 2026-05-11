"""
Layer 3: Semantic Matching Engine
Uses sentence-transformers to compute embedding-based cosine similarity
between resume content and job description requirements.
Runs locally — no API calls. Fully deterministic.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.logger import get_logger

logger = get_logger(__name__)

# Load model once at module level (lazy singleton)
_model = None

def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence-transformers model loaded successfully.")
    return _model

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

def compute_semantic_score(resume_text: str, jd_text: str) -> float:
    """
    Compute overall semantic similarity score between resume and JD.
    Returns a score between 0 and 100.
    """
    model = _get_model()
    
    # Chunk texts into meaningful segments for better similarity
    resume_chunks = _chunk_text(resume_text, max_chunk_size=512)
    jd_chunks = _chunk_text(jd_text, max_chunk_size=512)
    
    if not resume_chunks or not jd_chunks:
        logger.warning("Empty text provided to semantic engine.")
        return 0.0
    
    # Encode all chunks
    resume_embeddings = model.encode(resume_chunks, show_progress_bar=False)
    jd_embeddings = model.encode(jd_chunks, show_progress_bar=False)
    
    # Compute average similarity: for each JD chunk, find best matching resume chunk
    similarities = []
    for jd_emb in jd_embeddings:
        chunk_sims = [cosine_similarity(jd_emb, res_emb) for res_emb in resume_embeddings]
        best_sim = max(chunk_sims) if chunk_sims else 0.0
        similarities.append(best_sim)
    
    # Average of best matches (weighted by JD importance)
    avg_similarity = float(np.mean(similarities)) if similarities else 0.0
    
    # Convert from [-1, 1] cosine range to [0, 100] score
    # In practice, resume-JD similarities for MiniLM typically fall between 0.2 and 0.7.
    if avg_similarity > 0.2:
        # Scale 0.2 -> 0.7 to 0 -> 100
        score = ((avg_similarity - 0.2) / 0.55) * 100
    else:
        # Penalize severely below 0.2
        score = (avg_similarity / 0.2) * 10
    
    score = max(0.0, min(100.0, score))
    
    logger.info(f"Semantic matching complete: raw_avg={avg_similarity:.3f}, score={score:.1f}")
    return round(score, 1)

def compute_skill_level_similarity(resume_skills: list, jd_skills: list) -> dict:
    """
    Compute per-skill semantic similarity.
    Returns dict mapping each JD skill to its best resume match and score.
    """
    if not resume_skills or not jd_skills:
        return {}
    
    model = _get_model()
    resume_embs = model.encode(resume_skills, show_progress_bar=False)
    jd_embs = model.encode(jd_skills, show_progress_bar=False)
    
    result = {}
    for i, jd_skill in enumerate(jd_skills):
        best_score = 0.0
        best_match = ""
        for j, res_skill in enumerate(resume_skills):
            sim = cosine_similarity(jd_embs[i], resume_embs[j])
            if sim > best_score:
                best_score = sim
                best_match = res_skill
        result[jd_skill] = {
            "best_match": best_match,
            "similarity": round(best_score, 3)
        }
    
    return result

def _chunk_text(text: str, max_chunk_size: int = 512) -> list:
    """Split text into meaningful chunks for embedding."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += " " + para
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Ensure at least one chunk
    if not chunks and text.strip():
        chunks = [text[:max_chunk_size].strip()]
    
    return chunks
