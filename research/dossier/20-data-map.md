# Dossier 20 — pt-BR + emotional speech data map (web research, 2026-05-17)

> Autonomous research pass (Pedro away). License verdicts explicit. Confirms
> `mission.md` risk #3 and the Apache/CC-BY/CC0-only constraint. Bottom line:
> open pt-BR is plentiful for *intelligibility* (~1,500h+ CC-BY/CC0) but the
> *spontaneous/conversational* slice is **CC-BY-NC-ND (commercial-vetoed)** and
> **emotion-labeled pt-BR ≈ 0h usable**. emotion×accent for Brazil = empty ⇒
> that gap IS the moat; must be filled in-house.

## 1. pt-BR general corpora

| Dataset | pt hours | Type | Emotion | License | Commercial | Fit |
|---|---|---|---|---|---|---|
| **CML-TTS (pt)** | ~1,200 h | read (audiobook) | no | CC-BY-4.0 | ✅ | **primary intelligibility seed** (Edresson) |
| **MLS pt** | ~160–284 h | read | no | CC-BY-4.0 | ✅ | add to base, same lineage |
| **Common Voice pt** | ~170+ h | read crowd | no | CC0 | ✅ | best accent diversity, noisy, zero friction |
| **TTS-Portuguese** | ~10 h | read, 1 spk, 48k | no | CC-BY-4.0 | ✅ | clean single-spk seed (vendored) |
| **CORAA-ASR v1.1** | ~290 h | spontaneous+prepared | no | **CC-BY-NC-ND** | ❌ | spontaneous gold, **vetoed** (research probe only) |
| **CORAA NURC-SP** | ~239 h | 100% spontaneous | no | **CC-BY-NC-ND** | ❌ | largest spontaneous pt-BR, NC-vetoed |
| **MUPE** (via CORAA) | ~365 h | spontaneous interview | no | NC-ND | ❌ | conversational register, vetoed |
| **C-ORAL-BRASIL** | ~21 h | spontaneous dialogue | prosody-tag | CC-BY-NC-SA | ❌ | rare true dialogue, mineiro, method-ref only |
| **NURC-Recife** | tens h | spontaneous | no | academic, varies | ⚠️ contact | only sizeable **nordestino** spontaneous |
| BRSpeech/LaPS/CETUC/Spoltech/WestPoint-pt/VoxForge-pt | 1–20 h ea | read | no | mixed | ⚠️ | legacy filler, low priority |

**Hard fact:** no commercial-safe spontaneous *casual* conversational pt-BR corpus at scale.

> **CORRECTION (2026-05-17, see dossier 21):** there IS a commercial-safe 2-party
> pt-BR lane this pass missed — **Câmara dos Deputados** plenary/committee audio is
> **CC-BY-4.0** and **court/CNJ/STF hearings** are non-copyrightable as official
> acts (**Lei 9.610 Art. 8º**, public-domain). Both are mono (need diarization,
> `tools/data/to_stereo.py`) and **formal/adversarial register** (not casual SAC —
> that register gap stays a moat). ⚠️ **Senado/TV Senado is the OPPOSITE: proprietary,
> commercial use forbidden** — do not confuse with Câmara. Synthetic 2-party
> (Kokoro/Chatterbox + LLM) is the other commercial-safe lane; **never XTTS/F5
> to generate training data — NC poisons the output.**

## 2. Emotional speech datasets (any language — method/transfer)

| Dataset | Lang | Hours | License | Commercial | Fit |
|---|---|---|---|---|---|
| **VERBO** | pt-BR | ~1.4 h | research, unclear | ⚠️ | only pt-BR emotional set, tiny/acted, prototype only |
| CORAA SER | pt-BR | ~0.7 h | NC-ND | ❌ | PoC scale only |
| Expresso (Meta) | EN | 40 h | CC-BY-NC | ❌ | best expressive-dialogue *method* ref |
| EARS | EN | 100+ h | CC-NC (verify) | ❌ likely | 22 emotions, method ref |
| **MSP-Podcast** | EN | ~409 h | academic lic., source CC commercial-permitting | ⚠️ **academic, commercial-capable** | best naturalistic emotion at scale; sign UTD |
| MSP-Conversation | EN | ~74 h | academic | ⚠️ | dyadic conversation+emotion, method gold |
| IEMOCAP | EN | ~12 h | research-only | ❌ | canonical SER ref |
| ESD | EN+ZH | ~29 h | research-only | ❌ | emotion-transfer method |
| **EmoV-DB** | EN/FR | ~9 h | CC0/Apache mix | ✅ likely | rare commercial-OK emotional, small |
| **CREMA-D** | EN | ~5 h | ODbL | ✅ (share-alike) | commercial-safe emotion method data |
| RAVDESS | EN | ~2 h | CC-BY-NC-SA | ❌ | vetoed |
| **JL-Corpus** | EN-NZ | ~3.6 h | CC-BY-4.0 (verify) | ✅ likely | small commercial-safe option |
| **LibriTTS-R** | EN | ~585 h | CC-BY-4.0 | ✅ | hi-q EN style/prosody pretrain, no emotion labels |

## 3. Conversational / full-duplex (method/transfer)
Fisher (~2000h EN, LDC paid), Switchboard (~300h EN, LDC paid), CANDOR (~850h EN, research lic — verify commercial), Moshi recipe (the transfer, code MIT/Apache), Expresso (also expressive-dialogue ref), GigaSpeech 2 (scale pattern). All EN; none pt-BR; method/architecture transfer only.

## 4. Accent coverage for Brazil
| Accent | Commercial-safe | Reality |
|---|---|---|
| Paulista | CV (CC0), CML/MLS (read) | OK read; spontaneous = NURC-SP (vetoed) |
| Carioca | thin | **record in-house (Pedro = M)** |
| Nordestino | NURC-Recife (unclear) | **uncovered commercially** |
| Gaúcho | none | **uncovered** |
| Mineiro | C-ORAL (NC) | **uncovered commercially** |

Commercial-safe **emotion-labeled pt-BR per accent ≈ 0 h**. 100% of expressive pt-BR is an in-house build ⇒ defensible moat.

## 5. Bootstrapping / in-house math
- TTS-bootstrap: good for intelligibility/prosody, weak for *authentic emotion* (circular — emotion is the thing we lack).
- VC + augmentation: ×3–5 multiplier on in-house takes.
- LLM-scripted emotion prompts → directed-recording targets (cheap, high-leverage; the recording-script generator).
- **In-house rules of thumb:** in-context clone per voice = **20–40 min** clean (1–3 h robust); per emotion per voice = **~20–40 min** categorical (~1 h with intensity). 2 voices × 6 emotions × ~0.5 h ≈ ~6 h core directed; +2–4 h/voice neutral base ⇒ **~12–16 h raw in-house total for MVP** (×3 aug).

## 6. Realistic data plan
- **(a) Intelligible pt-BR:** CML-TTS + MLS-pt + CV-pt + TTS-Portuguese, all CC-BY/CC0, ~500–1,000 h is plenty for LoRA/CPT. Zero new recording. (Qwen3-Omni native pt ⇒ light tuning only.)
- **(b) Emotion control:** no open commercial pt-BR emotion data. Method from Expresso/MSP (study only); *content* = in-house directed (~0.5h×6×2), labeled via Phase-1 tool. The proprietary "gold."
- **(c) 2 signature voices:** in-house only (Pedro/carioca + hired F), 1–3 h conversational each + LGPD consent.

## Decision-relevant
1. Plan sound/unchanged: open → intelligibility; in-house → emotion+voices. ~12–16 h directed recording = critical path (not data-scarcity panic).
2. **License wall:** CORAA/NURC-SP/MUPE/C-ORAL/CORAA-SER all NC/ND ⇒ research probe only, never trained into shippable weights. (Correction vs earlier specs: CORAA-family is CC-BY-**NC-ND**, not plain CC-BY.)
3. emotion×accent = greenfield ⇒ genuinely defensible proprietary dataset.
4. **MSP-Podcast** is the one high-value gettable emotion-*method* lever with a plausible commercial path (sign UTD) — worth it for transfer even though EN.

## Park (needs license/sign/contact/pay — DO NOT ACT)
MSP-Podcast/MSP-Conversation (sign UTD/Busso academic license, verify commercial clause); CORAA/NURC authors (NILC/C4AI-USP/UFPE) only if a commercial carve-out/partnership wanted (Phase B); C-ORAL-BRASIL (UFMG) NC; LDC Fisher/Switchboard (paid) only if Moshi recipe insufficient; CANDOR (confirm terms); re-verify EARS/Expresso exact tags; CREMA-D/EmoV-DB/JL/LibriTTS-R commercial-safe but track attribution/share-alike.

Sources: CORAA arXiv 2110.15731 + nilc-nlp/CORAA; CML-TTS OpenSLR146 + arXiv 2306.10097; MLS OpenSLR94; Common Voice; MSP-Podcast lab-msp.com + arXiv 2509.09791; Expresso (Meta) + HF ylacombe/expresso; EARS arXiv 2406.06185; VERBO github jrtorresneto; IEMOCAP USC SAIL; SER-datasets SuperKogito; Portuguese-NLP list (ajdavidl).
