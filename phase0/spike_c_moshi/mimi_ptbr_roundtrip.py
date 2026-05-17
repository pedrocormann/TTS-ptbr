"""
PHASE-0 TEST #1 (the decisive, cheap, do-first one — see research/dossier/
00-SYNTHESIS.md). Does Mimi survive pt-BR with NO retraining? J-Moshi froze Mimi
for Japanese; if it round-trips pt-BR acceptably we freeze it too and the whole
pt-BR effort collapses to the LM, not the codec.

Method: load Mimi (the exact proven path from CSM's generator.py — ungated
kyutai/moshiko repo, CC-BY-4.0), encode→decode a folder of pt-BR clips, then
measure resynthesis quality: WER round-trip (faster-whisper) + UTMOS. Compare
resynth vs original. Small/cheap; runs on a modest GPU (or slow CPU).

Run:
  pip install "moshi @ git+https://github.com/kyutai-labs/moshi.git#subdirectory=moshi" \
      sphn==0.1.12 faster-whisper==1.1.0 jiwer==3.0.4 soundfile
  python mimi_ptbr_roundtrip.py --in-dir ptbr_clips --transcripts trans.jsonl
( trans.jsonl: {"audio": "<name>.wav", "text": "<exact pt-BR transcript>"} per line )
"""
import argparse, json, os, time, statistics


def load_mimi(device):
    # Exact path CSM/generator.py uses — proven, ungated, CC-BY-4.0.
    from huggingface_hub import hf_hub_download
    from moshi.models import loaders
    w = hf_hub_download(loaders.DEFAULT_REPO, loaders.MIMI_NAME)
    mimi = loaders.get_mimi(w, device=device)
    mimi.set_num_codebooks(32)
    return mimi


def wer(ref, hyp):
    import jiwer
    n = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                       jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
    return jiwer.wer(n(ref), n(hyp))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True, help="folder of pt-BR wav clips")
    ap.add_argument("--transcripts", required=True, help="jsonl {audio,text}")
    ap.add_argument("--out-dir", default="mimi_rt_out")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    import torch, torchaudio
    from faster_whisper import WhisperModel
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if dev == "cpu":
        print("[warn] no CUDA — Mimi on CPU is slow but works for a small set.")
    mimi = load_mimi(dev)
    sr = mimi.sample_rate
    asr = WhisperModel("medium", device=dev,
                       compute_type="float16" if dev == "cuda" else "int8")

    rows = [json.loads(l) for l in open(args.transcripts, encoding="utf-8")]
    wers_o, wers_r, rtfs = [], [], []
    for r in rows:
        path = os.path.join(args.in_dir, r["audio"])
        wav, in_sr = torchaudio.load(path)
        wav = torchaudio.functional.resample(wav.mean(0), in_sr, sr).to(dev)

        # encode -> decode (the freeze test). CSM-proven shapes: (B,1,T).
        t0 = time.perf_counter()
        with torch.no_grad():
            codes = mimi.encode(wav[None, None, :])
            recon = mimi.decode(codes)[0, 0].cpu()
        dt = time.perf_counter() - t0
        secs = wav.numel() / sr
        rtfs.append(dt / secs if secs else float("inf"))

        rp = os.path.join(args.out_dir, "rt_" + r["audio"])
        torchaudio.save(rp, recon.unsqueeze(0), sr)

        def tx(p):
            segs, _ = asr.transcribe(p, language="pt", beam_size=5)
            return " ".join(s.text for s in segs).strip()
        wers_o.append(wer(r["text"], tx(path)))   # ASR on ORIGINAL (ceiling)
        wers_r.append(wer(r["text"], tx(rp)))     # ASR on RECON  (what we test)

    mo, mr = statistics.median(wers_o), statistics.median(wers_r)
    print("\n========== PHASE-0 TEST #1: MIMI pt-BR FREEZE ==========")
    print(f"clips                 : {len(rows)}  device={dev}")
    print(f"WER original (ceiling): {mo*100:.1f}%")
    print(f"WER Mimi-resynth      : {mr*100:.1f}%")
    print(f"Δ (resynth - original): {(mr-mo)*100:+.1f} pts   <-- the number that decides")
    print(f"Mimi RTF              : {statistics.median(rtfs):.2f}")
    verdict = ("FREEZE Mimi (Δ small, mirrors J-Moshi)" if (mr - mo) < 0.10
               else "INVESTIGATE: Δ large — Mimi may need pt-BR tuning")
    print(f"VERDICT               : {verdict}")
    print("Record in ../../specs/tech-stack.md + research/VIGIL-LOG.md. If freeze,")
    print("the pt-BR work = the LM only (continued-pretrain), not the codec.")
    print("========================================================")


if __name__ == "__main__":
    main()
