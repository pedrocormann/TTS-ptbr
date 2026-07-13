#!/usr/bin/env python3
"""
Trilha A — Bateria de experimentos (Treino 2).

Construído sobre os APRENDIZADOS do Treino 1 (2026-06-17):
  ✓ Voz do Pedro = PROVADA (não mexer): WER 12%, para 14/14, voz 3.4/5
  ✓ EOS label=0 + LR 5e-5 + áudio real funcionam
  ✗ Sotaque gringo = problema #1 (28× marcado, 'nativo' ~2.8/5 em TODOS)
  ✗ Entonação robótica = problema #2 (18× marcado, naturalidade baixa)
  ✗ Números quebram (front-end, não voz)
  ✗ Carioca quase não transfere (base CML formal domina)

Roadmap: quick-wins sem GPU (normalização) → baseline limpo (curação) →
ablações (G2P, proporção base, base carioca).

Cada ARM é declarativo (dataset, recipe override, text_fn) e reutiliza
recipe.STAGE_B. Função run_arm(name) encadeia o treino existente (train_voice.py).

Edição necessária: em train_bateria.py build_prep(), wirar text_frontend para
injetar a normalização (e G2P quando testado).
"""
import json
from pathlib import Path
from recipe import STAGE_B, check_config, text_frontend

# ─────────────────────────── ARMS DECLARATIVAS ───────────────────────────────

ARMS = {
    # B2: baseline — dataset curado (sem Whisper errors, sem fragmentos ruidosos)
    # Entrada: texto via text_frontend() com normalize_numbers=True, g2p=None
    'b2_clean': {
        'label': 'Estágio B · baseline limpo (curado)',
        'recipe': {**STAGE_B, 'note': 'stage_b_final com dataset curado (transcribed_clean.jsonl)'},
        'dataset': 'transcribed_clean.jsonl',  # gerado pelo curate_app.py
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score'],  # padrão + perceptual
        'hyp': 'Dataset curado → WER ≤16% (vs 12% sujo), menos artefato/sotaque errado',
        'gate': 'spk_sim ≥0.70, WER <20%, escuta cega prefere vs B1',
    },

    # B2_G2P: fonemizar a entrada (paper: arXiv 2410.14997, 2306.00535)
    # G2P pt-BR no front-end ataca o "gringo" #1
    'b2_g2p': {
        'label': 'Estágio B · G2P pt-BR (fonemizar entrada)',
        'recipe': {**STAGE_B, 'note': 'stage_b_final com entrada fonemizada (G2P pt-BR)'},
        'dataset': 'transcribed_clean.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=_g2p_ptbr),
        'g2p_impl': 'phonemizer pt-BR hardened (TODO: usar g2p-pt ou g2p_en com lexicon pt)',
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score', 'bipa_pronunciation'],
        'hyp': 'Condicionar em fonemas melhora alinhamento/pronúncia; reduz "gringo" (arXiv)',
        'gate': 'Perceptual soa nativo sobe vs B2_clean; WER não regride',
    },

    # B2_PROP_30_70: mix 30% base (CML) + 70% voz do Pedro
    # Teste: aumentar peso da voz do Pedro (proporção no mini-batch durante Stage B)
    'b2_prop_30_70': {
        'label': 'Estágio B · proporção 30% base, 70% Pedro',
        'recipe': {**STAGE_B, 'note': 'ablação: 30% CML dataset, 70% voz do Pedro em cada época'},
        'dataset': 'transcribed_clean.jsonl',
        'dataset_mix': {'base_weight': 0.3, 'pedro_weight': 0.7},
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score'],
        'hyp': 'Mais peso em voz real → prosódia mais natural, sotaque carioca transfere melhor',
        'gate': 'Nativo score sobe vs 50/50 baseline; WER não regride muito (até 15%)',
    },

    # B2_PROP_50_50: baseline da proporção — controle
    'b2_prop_50_50': {
        'label': 'Estágio B · proporção 50% base, 50% Pedro (baseline)',
        'recipe': {**STAGE_B, 'note': 'ablação: 50% CML dataset, 50% voz do Pedro (baseline)'},
        'dataset': 'transcribed_clean.jsonl',
        'dataset_mix': {'base_weight': 0.5, 'pedro_weight': 0.5},
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score'],
        'hyp': 'Baseline da proporção (referência para 30/70 e 100/0)',
        'gate': 'Métrica padrão',
    },

    # B2_PROP_100_PEDRO: 100% voz do Pedro (nenhuma base CML)
    # Teste: consegue manter o português sem base CML?
    'b2_prop_100_pedro': {
        'label': 'Estágio B · proporção 100% Pedro (ablação extrema)',
        'recipe': {**STAGE_B, 'lr': 2e-5, 'note': 'ablação: SÓ voz do Pedro, sem base CML (LR mais frio)'},
        'dataset': 'transcribed_clean.jsonl',
        'dataset_mix': {'base_weight': 0.0, 'pedro_weight': 1.0},
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score'],
        'hyp': 'SÓ dados do Pedro mantém português? Esperado: overfit/degradação em WER (>20%)',
        'gate': 'Diagnóstico: se WER não piora muito (<25%), a base não era tão crítica; se pior, base é essencial',
    },

    # B2_BASE_CARIOCA: trocar base CML (formal) por base carioca/espontânea
    # Dep: NURC-MIT confirmado (ou fallback ablação de proporção)
    'b2_base_carioca': {
        'label': 'Estágio B · base carioca/espontânea (em vez de CML formal)',
        'recipe': {**STAGE_B, 'note': 'Stage A com base CARIOCA (espontânea) + Stage B sobre ela'},
        'dataset': 'transcribed_clean.jsonl',
        'dataset_cml': None,  # trocar por NURC-MIT ou fallback
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score', 'sotaque_carioca_classifier'],
        'hyp': 'Base carioca + voz carioca → sotaque transfere melhor (CML formal bloqueava)',
        'gate': 'Nativo score +0.5 vs baseline; sotaque classifier discrimina carioca >=70%',
    },

    # ═══════════════════ ARMS DO SWEEP arch-addons (13/jul/2026) ═══════════════════
    # Fonte: research/dossier-2026-07/85-arquiteturas-addons.md (matriz de experimentos).
    # Marcadas com verdict (ADOPT/TEST) + stage + runner. Algumas precisam de runner
    # PRÓPRIO (spine bake-off, decoder-FM) — declaradas aqui como fonte de verdade; o
    # train_voice.py atual só roda as CSM/Stage-B. text_fn seguro (frontend padrão).

    # SPINE BAKE-OFF ★ — o arm de maior alavancagem: base pt-nativa dissolve o Estágio A?
    'spine_qwen3_base': {
        'label': 'Bake-off spine · Qwen3-TTS-0.6B-Base + LoRA Pedro (vs CSM)',
        'stage': 'spine', 'verdict': 'TEST', 'runner': 'external:qwen3_tts_finetune',
        'recipe': {'lr': 5e-5, 'note': 'Qwen3-TTS-12Hz-0.6B-Base (Apache, pt-nativo, 12.5Hz como o Mimi)'},
        'dataset': 'transcribed_clean.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'accent_scorecard', 'nativo_score'],
        'hyp': 'Base pt-nativa (Qwen3) mata o Estágio A e o gap #1 (gringo) vs CSM base-EN',
        'gate': 'accent_scorecard(carioca) e nativo_score > CSM+EstágioA no MESMO eval; spk-sim ≥0.70',
        'todo': 'usar repo Qwen3-TTS-Finetuning; mesma voz curada; comparar cego no rate_app',
    },
    'spine_kyutai_pt': {
        'label': 'Bake-off spine · Kyutai-TTS-pt (CC-BY, sobre Mimi)',
        'stage': 'spine', 'verdict': 'TEST', 'runner': 'external:kyutai_dsm',
        'recipe': {'note': 'Kyutai-TTS 1.6B streaming, pt desde abr/2026; mesmo codec Mimi'},
        'dataset': 'transcribed_clean.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'accent_scorecard', 'nativo_score'],
        'hyp': '3º competidor do bake-off; CC-BY passa no gate',
        'gate': 'idem spine_qwen3_base',
    },
    # DECODER FM CHUNK-WISE ★ — troca só o detokenizer do Mimi, mantém o LM AR do CSM
    'decode_fm_chunk': {
        'label': 'Decoder flow-matching chunk-wise sobre tokens do Mimi (mantém o LM do CSM)',
        'stage': 'decoder', 'verdict': 'TEST', 'runner': 'external:fm_detokenizer',
        'recipe': {'note': 'treinar SÓ o detokenizer FM em áudio carioca; LM do CSM intocado'},
        'dataset': 'transcribed_clean.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['f0_rmse_iu', 'nativo_score', 'ttsds2'],
        'hyp': 'Detokenizer FM ataca #1/#2 (sotaque/robótico) SEM retreinar o LM (padrão CosyVoice/Kimi)',
        'gate': 'F0-RMSE por IU e nativo_score sobem vs decode Mimi padrão',
    },
    # DADO — contexto de turno (ADOPT) e synth+DPO anti-erosão (TEST, par obrigatório)
    'b_context_turn': {
        'label': 'Estágio B · alvo=enunciado condicionado no turno anterior (áudio+texto)',
        'stage': 'voice', 'verdict': 'ADOPT', 'runner': 'train_voice',
        'recipe': {**STAGE_B, 'note': 'condicionar cada alvo no(s) turno(s) anterior(es); loss só no alvo'},
        'dataset': 'transcribed_clean.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'spk_sim', 'nativo_score'],
        'hyp': 'Utterance-com-contexto > conversa-inteira (que alucina similaridade de locutor) — arXiv 2505.07202',
        'gate': 'naturalidade/nativo sobe sem regredir spk-sim',
    },
    'data_synth_dpo': {
        'label': 'Dado sintético do NOSSO CSM + DPO anti-erosão (par obrigatório)',
        'stage': 'data', 'verdict': 'TEST', 'runner': 'external:synth+dpo',
        'recipe': {'note': 'LLM→texto carioca → nosso CSM → filtro WER; DPO duplo-objetivo contra o próprio synth'},
        'dataset': 'synth_carioca.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['wer', 'token_entropy', 'nativo_score', 'f0_rmse_iu'],
        'hyp': 'synth multiplica volume e ataca #1/#3, MAS achata prosódia >50% razão → DPO devolve a alma (arXiv 2605.27383)',
        'gate': 'entropia de token e F0 não caem vs baseline; WER melhora; NUNCA rodar synth sem o DPO',
        'todo': 'sintetizar SÓ com peso do nosso gate (CSM Apache), nunca XTTS (CPML)',
    },
    # EMOÇÃO — sequência do mais barato ao mais caro (F2/F3); todas preservam o timbre
    'emo_dualref': {
        'label': 'Emoção · dual-reference (ref timbre Pedro + ref só-emoção) — ZERO treino',
        'stage': 'emotion', 'verdict': 'TEST', 'runner': 'inference_only',
        'recipe': {'note': 'usa o audio-conditioning nativo do CSM; 2ª ref pode ser de outra voz/idioma (só estilo)'},
        'dataset': None,
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['ser_uar_independent', 'spk_sim'],
        'hyp': 'CSM transfere estilo por áudio-ref em pt-BR sem treinar (intuição IndexTTS2) — n=0 hoje',
        'gate': 'SER-UAR da emoção-alvo sobe sem cair spk-sim; 1º arm por custar $0',
    },
    'emo_cspft_probe': {
        'label': 'Emoção · CSP-FT (probe: em que camada do CSM mora a emoção; congela locutor)',
        'stage': 'emotion', 'verdict': 'TEST', 'runner': 'external:cspft_probe',
        'recipe': {'note': 'probing de camada (arXiv 2501.14273); FT só das camadas de emoção, congela as de locutor'},
        'dataset': 'g2_emotions.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['ser_uar_independent', 'spk_sim'],
        'hyp': 'Disentangle por localização de camada preserva a voz do Pedro; publicável com USP',
        'gate': 'controle de emoção sobe com spk-sim preservado (≥ baseline)',
    },
    'emo_taskvector_alpha': {
        'label': 'Emoção · botão α por task-vector (diff de pesos emo−neutro, backbone congelado)',
        'stage': 'emotion', 'verdict': 'TEST', 'runner': 'external:taskvector',
        'recipe': {'note': 'arXiv 2606.05367 (CC-BY, autor BR, LM-based); α contínuo, aditivo, preserva locutor'},
        'dataset': 'g2_emotions.jsonl',
        'text_fn': lambda t: text_frontend(t, normalize_numbers=True, g2p=None),
        'eval_metrics': ['ser_uar_independent', 'spk_sim', 'intensity_vad'],
        'hyp': 'α por aritmética de pesos dá intensidade fina sem retreinar; precisa de dado emo p/ montar o vetor',
        'gate': 'intensidade monotônica com α; spk-sim intacto',
    },
}

# ─────────── GUARDRAILS do sweep 13/jul (regras que o método PROVOU) ───────────
# Aplicar em build_prep/train; ver dossiê 85 §matriz e arch-map/.
SWEEP_GUARDRAILS = {
    'mixed_replay': 'No FT de voz (C2), misturar 25–30% do dado de pré-treino (experience replay) + canary de '
                    'frases pt fixas. Single-speaker sem mistura degrada 40–50% fora-de-domínio (arXiv 2603.10904). '
                    'É o gotcha #6 (WER 300%) formalizado. Canary vira gate automático no watchdog.',
    'synthetic_erosion': 'NUNCA usar dado sintético sem alinhamento de preferência de duplo objetivo. Synth cura '
                         'fonética/sotaque mas achata a prosódia a partir de ~50% de razão (arXiv 2605.27383). '
                         'Monitorar entropia de token como proxy de diversidade prosódica.',
    'rl_order': 'RL: DPO-humano de prosódia ANTES de GRPO. GRPO sobre WER/spk-sim COLAPSA a prosódia em fala '
                'monótona (reward hacking, arXiv 2509.18531). GRPO só escopado a número/#3, com KL forte.',
    'quant_codec_conservative': 'Quantização: backbone AR agressivo (Q4/Q8), mas codec Mimi (GAN) CONSERVADOR '
                                '(Q8/FP16) — quantizar o codec forte degrada timbre mais que o backbone.',
    'dsp_aug_scope': 'DSP-aug (pitch/tempo) SÓ em C0/C1 (língua/robustez). Na camada de VOZ carioca (C2), '
                     'pitch/formant-shift CORROMPE a identidade que estamos clonando (spk-sim cai).',
    'eval_no_mos_oracle': 'NÃO rankear checkpoints por MOS automático (cego a prosódia + viés F0, arXiv 2606.19951). '
                          'Régua = win-rate/CMOS carioca + TTSDS2 + accent_scorecard. Ver eval/README.',
}


# ──────────────────────── G2P PLACEHOLDER ──────────────────────────────────

def _g2p_ptbr(text):
    """TODO: implementar G2P pt-BR real.
    
    Candidatos (em ordem de prioridade):
    1. g2p-pt (https://pypi.org/project/g2p-pt/) — rule-based, CC-BY
    2. g2p_en customizado com lexicon pt-BR (g2p_en + custom dicionário)
    3. phonemizer com modelo pt-BR (precisa treinar/validar)
    
    Por enquanto: placeholder que retorna o texto intacto (desativa a ablação).
    Quando implementado: entrada de texto → IPA/SAMPA fonêmico.
    
    Exemplo esperado:
        "O CEP é 22290-160" → "O tsEpE é vintedOjs mil duzEntOs novEntO sEntO E sEsEntO"
    """
    # TODO: substituir por g2p real
    return text


# ─────────────────────────── RUNNER ──────────────────────────────────────

def run_arm(arm_name, out_root='/workspace/TTS-ptbr-data', push_hub=''):
    """Executa um ARM: carrega receita, valida, roda o treino (train_voice.py).
    
    Args:
        arm_name: chave de ARMS (ex: 'b2_clean')
        out_root: raiz de saída (Network Volume)
        push_hub: repo_id HF pra salvar resultados (opcional)
    
    Retorna:
        resultado do treino: {'name', 'wer', 'spk_sim', 'min', ...}
    """
    import subprocess, time, sys
    
    if arm_name not in ARMS:
        raise ValueError(f"ARM desconhecida: {arm_name}. Opções: {list(ARMS.keys())}")
    
    arm = ARMS[arm_name]
    recipe = arm['recipe']
    
    # Guardrails
    check_config(recipe)
    print(f"\n{'='*70}")
    print(f"▶ {arm['label']}")
    print(f"  receita: {recipe['note']}")
    print(f"  dataset: {arm['dataset']}")
    print(f"  hipótese: {arm['hyp']}")
    print(f"{'='*70}\n")
    
    # TODO: montar a chamada exata pro train_voice.py com overrides
    # Por enquanto: dry-run (print o que SERIA executado)
    
    cmd = [
        'python', 'runpod/train_voice.py',
        '--exp-name', arm_name,
        '--dataset', str(Path(out_root) / arm['dataset']),
        '--lr', str(recipe['lr']),
        '--minutes', str(recipe['minutes']),
        '--lora-r', str(recipe['lora_r']),
        '--lora-alpha', str(recipe['lora_alpha']),
        '--out-root', out_root,
    ]
    
    if push_hub:
        cmd.extend(['--push-hub', push_hub])
    
    print(f"Comando (ainda não rodando, dry-run):\n  {' '.join(cmd)}\n")
    
    # TODO: chamar subprocess.run(cmd) de verdade quando train_voice.py estiver pronto
    # Por enquanto, retornamos um placeholder
    
    return {
        'name': arm_name,
        'label': arm['label'],
        'status': 'TODO_implement',
        'hyp': arm['hyp'],
        'gate': arm['gate'],
    }


def batch_run(arm_names, **kwargs):
    """Roda múltiplas ARMs em sequência, coletando resultados."""
    results = []
    for name in arm_names:
        try:
            r = run_arm(name, **kwargs)
            results.append(r)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append({'name': name, 'status': 'ERROR', 'error': str(e)})
    return results


# ───────────────────────────── smoke-test ────────────────────────────────

if __name__ == '__main__':
    print("Smoke-test: validar todas as ARMs…\n")
    for name, arm in ARMS.items():
        try:
            check_config(arm['recipe'])
            print(f"✓ {name:20} | {arm['label']}")
        except AssertionError as e:
            print(f"✗ {name:20} | {str(e)[:50]}…")
    
    print("\n\nARMs disponíveis (para usar em EXPERIMENTS-proximos.md):")
    for name in ARMS.keys():
        print(f"  • {name}")
