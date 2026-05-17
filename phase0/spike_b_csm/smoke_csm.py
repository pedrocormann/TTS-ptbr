"""
Spike B smoke test — CSM-1B (the bet). Written against the REAL API in
research/repos/csm/generator.py (load_csm_1b / Generator.generate / Segment).

Produces the go/no-go numbers:
  - latency (s) and RTF (gen_time / audio_seconds) on this GPU
  - pt-BR intelligibility WER via faster-whisper round-trip (no fine-tune)
  - optional in-context voice-clone smoke from a reference wav

Run (from Colab or a CUDA box), after `huggingface-cli login` with
meta-llama/Llama-3.2-1B AND sesame/csm-1b licenses accepted:

  python smoke_csm.py --csm-repo /path/to/research/repos/csm \
      [--ref-wav ref.wav --ref-text "transcrição do ref"]
"""
import argparse, os, sys, time, statistics
os.environ.setdefault("NO_TORCH_COMPILE", "1")  # required by Mimi (CSM README)

import torch
import torchaudio


def _load_generator(csm_repo: str):
    sys.path.insert(0, csm_repo)  # csm uses flat imports: `from generator import ...`
    try:
        from generator import load_csm_1b, Segment  # noqa
    except Exception as e:
        sys.exit(f"[FATAL] could not import csm generator from {csm_repo}: {e}")
    if not torch.cuda.is_available():
        sys.exit("[FATAL] no CUDA GPU. CSM needs CUDA (Colab T4/L4/A100).")
    try:
        gen = load_csm_1b(device="cuda")
    except Exception as e:
        sys.exit(
            f"[FATAL] load_csm_1b failed: {e}\n"
            ">> Most common cause: HF licenses not accepted. You need BOTH "
            "meta-llama/Llama-3.2-1B (gated) and sesame/csm-1b, and `huggingface-cli login`."
        )
    return gen, Segment


def _gen_and_time(gen, text, speaker=0, context=None, max_ms=10_000):
    context = context or []
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    audio = gen.generate(text=text, speaker=speaker, context=context,
                          max_audio_length_ms=max_ms)
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    secs = audio.numel() / gen.sample_rate
    rtf = dt / secs if secs > 0 else float("inf")
    return audio, dt, secs, rtf


def _wer(reference: str, hypothesis: str) -> float:
    import jiwer
    norm = jiwer.Compose([
        jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(), jiwer.Strip(),
    ])
    return jiwer.wer(norm(reference), norm(hypothesis))


def _asr_ptbr(wav_path: str) -> str:
    from faster_whisper import WhisperModel
    model = WhisperModel("medium", device="cuda", compute_type="float16")
    segs, _ = model.transcribe(wav_path, language="pt", beam_size=5)
    return " ".join(s.text for s in segs).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csm-repo", required=True, help="path to research/repos/csm")
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--ref-wav", default=None, help="optional pt-BR reference wav for in-context clone")
    ap.add_argument("--ref-text", default=None, help="transcript of --ref-wav")
    ap.add_argument("--runs", type=int, default=3, help="repeats for latency stats")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    gen, Segment = _load_generator(args.csm_repo)
    print(f"[ok] CSM-1B loaded. sample_rate={gen.sample_rate} device={gen.device}")

    PT_TEXT = "Olá, tudo bem? Eu sou uma voz brasileira em teste, sem nenhum ajuste fino."
    EN_TEXT = "Hello from Sesame. This is a baseline latency check."

    # 1) EN baseline + 2) pt-BR, repeated for latency stats
    rtfs, lats = [], []
    for i in range(args.runs):
        _, dt_en, _, rtf_en = _gen_and_time(gen, EN_TEXT)
        a_pt, dt_pt, secs_pt, rtf_pt = _gen_and_time(gen, PT_TEXT)
        rtfs.append(rtf_pt); lats.append(dt_pt)
        print(f"  run {i+1}: EN rtf={rtf_en:.2f} | PT lat={dt_pt:.2f}s "
              f"audio={secs_pt:.2f}s rtf={rtf_pt:.2f}")
    pt_wav = os.path.join(args.out_dir, "ptbr_nofinetune.wav")
    torchaudio.save(pt_wav, a_pt.unsqueeze(0).cpu(), gen.sample_rate)

    # 3) pt-BR intelligibility (the key Spike-B metric)
    try:
        hyp = _asr_ptbr(pt_wav)
        wer = _wer(PT_TEXT, hyp)
        print(f"[asr] heard: {hyp!r}")
    except Exception as e:
        hyp, wer = None, None
        print(f"[warn] ASR round-trip skipped: {e}")

    # 4) optional in-context voice clone
    clone_note = "skipped (no --ref-wav)"
    if args.ref_wav and args.ref_text:
        wav, sr = torchaudio.load(args.ref_wav)
        wav = torchaudio.functional.resample(wav.squeeze(0), sr, gen.sample_rate)
        ref_seg = Segment(text=args.ref_text, speaker=0, audio=wav)
        a_cl, dt_cl, _, rtf_cl = _gen_and_time(
            gen, "Esta é a mesma voz, agora falando uma frase nova em português.",
            speaker=0, context=[ref_seg])
        cl_wav = os.path.join(args.out_dir, "ptbr_clone.wav")
        torchaudio.save(cl_wav, a_cl.unsqueeze(0).cpu(), gen.sample_rate)
        clone_note = f"ok -> {cl_wav} (lat={dt_cl:.2f}s rtf={rtf_cl:.2f})"

    # ---- go/no-go table ----
    print("\n================ SPIKE B — GO/NO-GO ================")
    print(f"GPU                : {torch.cuda.get_device_name(0)}")
    print(f"pt-BR latency p50  : {statistics.median(lats):.2f} s "
          f"(min {min(lats):.2f} / max {max(lats):.2f})")
    print(f"pt-BR RTF  p50     : {statistics.median(rtfs):.2f}  (<1.0 = faster than real time)")
    print(f"pt-BR WER (no FT)  : {('%.1f%%' % (wer*100)) if wer is not None else 'n/a'}  "
          f"(high = pt-BR needs fine-tune, expected per CSM README)")
    print(f"in-context clone   : {clone_note}")
    print(f"pt-BR sample wav   : {pt_wav}  (LISTEN to it — numbers don't capture prosody)")
    print("Record these in ../../specs/tech-stack.md + Dev KB before deciding the bet.")
    print("====================================================")


if __name__ == "__main__":
    main()
