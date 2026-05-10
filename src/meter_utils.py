"""
meter_utils.py — Stress and meter utilities for MeterMind models 1, 2, and 3.

Lightweight: only depends on `re` and `pronouncing`. No PyTorch or heavy models.

Usage in Colab:
    from google.colab import files
    files.upload()          # upload meter_utils.py when prompted
    from meter_utils import *

For evaluation metrics (SP, grammaticality) also upload and import eval_metrics.py:
    files.upload()
    from eval_metrics import *

Functions
---------
tokenize          : lowercase + strip punctuation → word list
get_stress        : CMU stress sequence, with archaic suffix fallback
n_syllables       : CMU syllable count, with archaic suffix fallback
is_flexible       : True for monosyllabic words that fit either stress position
metrical_accuracy : fraction of iambic template positions correctly filled

Constants
---------
IAMBIC_TEMPLATE   : [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]  (10 positions)
"""

import re
import pronouncing

__all__ = [
    'IAMBIC_TEMPLATE',
    'tokenize',
    'get_stress',
    'n_syllables',
    'is_flexible',
    'metrical_accuracy',
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IAMBIC_TEMPLATE = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]   # 10 syllable positions


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

def tokenize(text):
    """Lowercase, strip punctuation, split into word tokens.

    Note: apostrophes are stripped along with other punctuation, so
    archaic contractions (o'er, ne'er) become single tokens (oer, neer).
    These won't be found in CMU and will default to stress [0]. This is
    a known limitation — do not 'fix' by splitting on apostrophes, as
    that produces worse token fragments.
    """
    return re.sub(r"[^a-zA-Z\s]", "", text.lower()).split()


# ---------------------------------------------------------------------------
# Stress extraction
# ---------------------------------------------------------------------------

def get_stress(word):
    """Return the syllable stress sequence for a word as a list of ints.

    1 = stressed, 0 = unstressed. CMU secondary stress (2) is treated as 1.

    For words not in CMU, tries stripping archaic suffixes '-est' and '-eth'
    and looking up the root (e.g. 'feedest' -> 'feed' + [0]).

    Monosyllabic words whose only stress is 1 (e.g. 'day', 'thee') return
    [0, 1] as a sentinel meaning "flexible -- fits either position". Use
    is_flexible() to test for this rather than comparing to [0, 1] directly,
    since genuine 2-syllable iambic words (e.g. 'compare') also have stress
    [0, 1] and must NOT be treated as flexible.

    Falls back to [0] (unstressed monosyllable) if nothing is found.
    """
    phones = pronouncing.phones_for_word(word)

    if not phones:
        # Archaic suffix fallback: feedest -> feed, knoweth -> know
        for suffix in ['est', 'eth']:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                root_phones = pronouncing.phones_for_word(word[:-len(suffix)])
                if root_phones:
                    stress = [1 if s == '2' else int(s)
                              for s in pronouncing.stresses(root_phones[0]) if s in '012']
                    return stress + [0]   # suffix syllable is unstressed
        return [0]

    stress = [1 if s == '2' else int(s)
              for s in pronouncing.stresses(phones[0]) if s in '012']

    # Monosyllabic stressed word -> flexible sentinel
    if len(stress) == 1 and stress[0] == 1:
        return [0, 1]

    return stress


def n_syllables(word):
    """Count syllables via CMU phone count. Returns 1 if word not found.

    Uses the same archaic suffix fallback as get_stress so that syllable
    counts are consistent (e.g. 'feedest' -> 2, not 1).
    """
    phones = pronouncing.phones_for_word(word)
    if not phones:
        for suffix in ['est', 'eth']:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                root_phones = pronouncing.phones_for_word(word[:-len(suffix)])
                if root_phones:
                    root_syls = len([p for p in root_phones[0].split() if p[-1].isdigit()])
                    return root_syls + 1   # +1 for the suffix syllable
        return 1
    return len([p for p in phones[0].split() if p[-1].isdigit()])


def is_flexible(word):
    """True if word is a monosyllable that can fill either stress position.

    Guards on n_syllables == 1 to avoid false positives for genuine 2-syllable
    iambic words like 'compare' or 'above', whose stress list [0, 1] coincides
    with the flexible sentinel but should NOT be treated as flexible.
    """
    return n_syllables(word) == 1 and get_stress(word) == [0, 1]


# ---------------------------------------------------------------------------
# Metrical Accuracy
# ---------------------------------------------------------------------------

def metrical_accuracy(words, template=IAMBIC_TEMPLATE):
    """Fraction of template syllable positions correctly filled (0.0 - 1.0).

    Flexible monosyllables score 1 in any position. Words that push beyond
    the template length are ignored (they don't affect the score).
    """
    correct = 0
    syl_pos = 0

    for word in words:
        if syl_pos >= len(template):
            break
        if is_flexible(word):
            correct += 1
            syl_pos += 1
        else:
            stress = get_stress(word)
            for s in stress:
                if syl_pos >= len(template):
                    break
                if s == template[syl_pos]:
                    correct += 1
                syl_pos += 1

    return correct / len(template)
