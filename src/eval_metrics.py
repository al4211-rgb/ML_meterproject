"""
eval_metrics.py — Evaluation metrics for MeterMind models 1, 2, and 3.

Heavy: requires sentence-transformers, transformers, and torch.

Usage in Colab (after meter_utils.py is already imported):
    from google.colab import files
    files.upload()          # upload eval_metrics.py when prompted
    from eval_metrics import *

    # Trigger downloads before the eval loop
    load_sp_model()
    load_gpt2()

Functions
---------
load_sp_model         : load (or return cached) SentenceTransformer
semantic_preservation : cosine similarity of sentence embeddings, clamped to [0, 1]
load_gpt2             : load (or return cached) GPT-2 model + tokenizer
grammaticality        : GPT-2 perplexity normalised to (0, 1]
"""

import math

__all__ = [
    'load_sp_model',
    'semantic_preservation',
    'load_gpt2',
    'grammaticality',
]

# ---------------------------------------------------------------------------
# Semantic Preservation
# ---------------------------------------------------------------------------

_sp_model = None   # module-level cache


def load_sp_model():
    """Load SentenceTransformer (cached after first call)."""
    global _sp_model
    if _sp_model is None:
        from sentence_transformers import SentenceTransformer
        print('Loading SentenceTransformer (first run downloads ~90 MB)...')
        _sp_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sp_model


def semantic_preservation(original, output):
    """Cosine similarity between sentence embeddings, clamped to [0, 1].

    Both strings should be cleaned to the same surface form before calling --
    use ' '.join(tokenize(text)) on raw inputs so casing and punctuation
    differences don't artificially lower the score.

    Returns a float in [0, 1]; higher = more meaning retained.
    """
    from sentence_transformers import util
    model = load_sp_model()
    emb = model.encode([original, output], convert_to_tensor=True)
    return float(max(0.0, util.cos_sim(emb[0], emb[1])))


# ---------------------------------------------------------------------------
# Grammaticality
# ---------------------------------------------------------------------------

_gpt2_model     = None   # module-level cache
_gpt2_tokenizer = None


def load_gpt2():
    """Load GPT-2 model and tokenizer (cached after first call)."""
    global _gpt2_model, _gpt2_tokenizer
    if _gpt2_model is None:
        import torch
        from transformers import GPT2LMHeadModel, GPT2TokenizerFast
        print('Loading GPT-2 (first run downloads ~500 MB)...')
        _gpt2_tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')
        _gpt2_model     = GPT2LMHeadModel.from_pretrained('gpt2')
        _gpt2_model.eval()
    return _gpt2_model, _gpt2_tokenizer


def grammaticality(text):
    """GPT-2 perplexity normalised to (0, 1].

    G = 1 / (1 + log(perplexity))

    Higher = more fluent/grammatical. Perplexity >= 1 always (cross-entropy
    loss >= 0), so G is safely in (0, 1].
    """
    import torch
    model, tokenizer = load_gpt2()
    inputs = tokenizer(text, return_tensors='pt')
    with torch.no_grad():
        loss = model(**inputs, labels=inputs['input_ids']).loss
    perplexity = math.exp(loss.item())
    return 1 / (1 + math.log(perplexity))
