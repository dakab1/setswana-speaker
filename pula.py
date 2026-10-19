"""Pula, an open Setswana LLM, run in-process with llama.cpp: translation and word-by-word meanings."""
import re
import threading

from llama_cpp import Llama

PUNCTUATION = ".,?!:;\"'()"
LIST_MARKER = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")  # Pula sometimes numbers or bullets its lines

GLOSS_PROMPT = """Explain each Setswana word in the translation below. Write one line per Setswana word, in order, as: word = English meaning. Small grammar words get their grammatical meaning.

Example
English: We are eating bread.
Setswana: Re ja borotho.
Re = we
ja = eat
borotho = bread

Now do this one
English: {english}
Setswana: {setswana}
"""


class Pula:
    def __init__(self, model_path):
        self._model_path = str(model_path)
        self._model = None
        self._lock = threading.Lock()  # llama.cpp contexts are not thread-safe; also guards the one-time load

    def _ask(self, question, repeat_penalty):
        # Plain Llama 3 prompt (BOS is added by llama.cpp); output matches Ollama's. The GGUF's own 3.1 template
        # injects a dated system message that makes Pula answer the question instead of translating it.
        prompt = (f"<|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|>"
                  "<|start_header_id|>assistant<|end_header_id|>\n\n")
        with self._lock:
            if self._model is None:  # ponytail: lazy load, so the first translation takes a few extra seconds
                self._model = Llama(self._model_path, n_ctx=2048, n_gpu_layers=-1, verbose=False)
            out = self._model.create_completion(prompt, temperature=0, repeat_penalty=repeat_penalty,
                                                max_tokens=300, stop=["<|eot_id|>"])
        return out["choices"][0]["text"].strip()

    def translate(self, english):
        # repeat_penalty 1.1 matches Ollama's default; at 1.0 Pula can loop ("kae kae kae ...").
        return self._ask("Translate the following English text into Setswana. "
                         f"Reply with only the Setswana translation.\n\n{english}", repeat_penalty=1.1)

    def gloss(self, english, setswana):
        # 1.0 here: the reply legitimately repeats words ("moso = tomorrow" twice), which a penalty distorts.
        reply = self._ask(GLOSS_PROMPT.format(english=english, setswana=setswana), repeat_penalty=1.0)
        return align_gloss(setswana, reply)

    def close(self):
        """Free the model before exit; llama.cpp's Metal backend aborts if it is still loaded when the process ends."""
        with self._lock:
            if self._model is not None:
                self._model.close()
                self._model = None


def align_gloss(setswana, reply):
    """Match Pula's 'word = meaning' lines to the sentence's own words, in order.

    Pula sometimes skips, merges or adds lines, so each sentence word takes the next line whose word matches;
    a word with no match gets an empty meaning instead of shifting every later meaning by one.
    """
    lines = []
    for line in reply.splitlines():
        if "=" in line:
            word, meaning = line.split("=", 1)
            lines.append((LIST_MARKER.sub("", word).strip().strip(PUNCTUATION).lower(), meaning.strip()))
    words, next_line = [], 0
    for token in setswana.split():
        bare = token.strip(PUNCTUATION)
        if not bare:
            continue
        meaning = ""
        for i in range(next_line, len(lines)):
            if lines[i][0] == bare.lower():
                meaning, next_line = lines[i][1], i + 1
                break
        words.append({"setswana": bare, "english": meaning})
    return words
