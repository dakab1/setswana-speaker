"""Generate Setswana pronunciation audio for "Bathong ba Modimo" (MMS-TTS + espeak-ng)."""
import os
import subprocess
import sys

import soundfile as sf
import torch
from transformers import AutoTokenizer, VitsModel

TEXT = "Bathong ba Modimo"
# espeak-ng phoneme input (Kirshenbaum-ish): aspirated t, velar nasal, penultimate stress.
PHONEMES = "[[ba'th_hUN ba mU'dimU]]"
OUT = "output"


def mms():
    model_id = "facebook/mms-tts-tsn"
    token = os.environ.get("HF_TOKEN")  # public model; only passed through if set
    tok = AutoTokenizer.from_pretrained(model_id, token=token)
    model = VitsModel.from_pretrained(model_id, token=token)
    torch.manual_seed(0)  # VITS is stochastic; fix seed for repeatable output
    with torch.no_grad():
        wav = model(**tok(TEXT.lower(), return_tensors="pt")).waveform[0].numpy()
    path = f"{OUT}/bathong_ba_modimo.wav"
    sf.write(path, wav, model.config.sampling_rate)
    return path


def espeak():
    paths = []
    for name, text in [("espeak", TEXT), ("espeak_phonemes", PHONEMES)]:
        path = f"{OUT}/bathong_ba_modimo_{name}.wav"
        subprocess.run(["espeak-ng", "-v", "tn", "-s", "130", "-w", path, text], check=True)
        paths.append(path)
    return paths


def report(path):
    info = sf.info(path)
    assert info.duration > 0, f"{path} has zero duration"
    print(f"{path}: {info.duration:.2f}s @ {info.samplerate} Hz")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    paths = []
    try:
        paths.append(mms())
    except Exception as e:
        print(f"MMS failed: {e!r}", file=sys.stderr)
    paths += espeak()
    for p in paths:
        report(p)
