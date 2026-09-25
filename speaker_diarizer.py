"""
speaker_diarizer.py
Modulo avanzato per la diarizzazione e il riconoscimento vocale multi-interlocutore (Speaker 1 vs Speaker 2).
Funziona interamente in locale offline estraendo caratteristiche acustiche ad alta precisione:
- Voice Activity Detection (VAD) frame-by-frame per isolare solo il parlato voiced
- 13 Coefficienti Cepstrali su scala Mel (MFCC 1-12) e Delta-MFCC dinamici
- Analisi fondamentale del Pitch F0 (mediana, registro base al 10° percentile, escursione IQR)
- Rapporto Armonico-Rumore (HNR) e baricentro/dispersione spettrale delle formanti
- Clustering sferico K-Means++ con distanze coseno
- Modello a continuità temporale HMM / Viterbi sensibile ai gap e pause del discorso
"""
from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

import numpy as np
from rich.console import Console

console = Console(stderr=True)


def _read_wav_segment(wav_path: Path, start_sec: float, end_sec: float) -> tuple[np.ndarray, int]:
    """Legge un segmento temporale da un file WAV convertendolo in float32 mono [-1.0, 1.0]."""
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        total_frames = wf.getnframes()

        start_frame = max(0, int(start_sec * sr))
        end_frame = min(total_frames, int(end_sec * sr))
        count = end_frame - start_frame

        if count <= 0:
            return np.zeros(0, dtype=np.float32), sr

        wf.setpos(start_frame)
        raw_bytes = wf.readframes(count)

    if sampwidth == 2:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        samples = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    return samples, sr


def _compute_mel_filterbank(sr: int = 16000, n_fft: int = 512, n_mels: int = 26, fmin: float = 80.0, fmax: float = 7600.0) -> np.ndarray:
    """Costruisce il banco di filtri Mel triangolari (n_mels x (n_fft//2 + 1))."""
    def hz_to_mel(hz: float) -> float:
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel: float) -> float:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    fmax = min(fmax, sr / 2.0)
    mel_min = hz_to_mel(fmin)
    mel_max = hz_to_mel(fmax)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    num_bins = n_fft // 2 + 1
    filterbank = np.zeros((n_mels, num_bins), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_left = min(num_bins - 1, max(0, bin_points[m - 1]))
        f_center = min(num_bins - 1, max(0, bin_points[m]))
        f_right = min(num_bins - 1, max(0, bin_points[m + 1]))

        if f_center > f_left:
            filterbank[m - 1, f_left:f_center] = (np.arange(f_left, f_center) - f_left) / float(f_center - f_left)
        if f_right > f_center:
            filterbank[m - 1, f_center:f_right] = (f_right - np.arange(f_center, f_right)) / float(f_right - f_center)

    return filterbank


def _compute_dct_matrix(n_mfcc: int = 13, n_mels: int = 26) -> np.ndarray:
    """Matrice di Trasformata Coseno Discreta (DCT-II ortonormale)."""
    dct_m = np.zeros((n_mfcc, n_mels), dtype=np.float32)
    for k in range(n_mfcc):
        for m in range(n_mels):
            dct_m[k, m] = math.cos(math.pi * k * (m + 0.5) / float(n_mels))
    dct_m[0, :] *= math.sqrt(1.0 / n_mels)
    dct_m[1:, :] *= math.sqrt(2.0 / n_mels)
    return dct_m


# Cache globale filtri Mel e DCT per massime prestazioni
_MEL_FB_CACHE: dict[int, np.ndarray] = {}
_DCT_CACHE: np.ndarray | None = None


def _get_dsp_bases(sr: int) -> tuple[np.ndarray, np.ndarray]:
    global _DCT_CACHE
    if sr not in _MEL_FB_CACHE:
        _MEL_FB_CACHE[sr] = _compute_mel_filterbank(sr=sr, n_fft=512, n_mels=26)
    if _DCT_CACHE is None:
        _DCT_CACHE = _compute_dct_matrix(n_mfcc=13, n_mels=26)
    return _MEL_FB_CACHE[sr], _DCT_CACHE


def _extract_voice_features(samples: np.ndarray, sr: int = 16000) -> np.ndarray:
    """
    Estrae un vettore di feature acustiche ad alta dimensionalità (42 dimensioni)
    specificamente progettato per distinguere il timbro e l'interlocutore:
    - 12 MFCC (1-12) mediati sui frame parlati
    - 12 MFCC deviazioni standard (varianza del timbro)
    - 12 Delta-MFCC mediati (dinamica delle formanti)
    - 3 statistiche di pitch F0: mediana, registro base (10° perc), escursione IQR
    - 1 Harmonics-to-Noise Ratio (HNR) medio
    - 2 Centroide e Rolloff spettrali medi
    """
    total_dim = 42
    if len(samples) < int(sr * 0.08):  # Meno di 80ms
        return np.zeros(total_dim, dtype=np.float32), 160.0

    # Rimozione offset DC
    samples = samples - np.mean(samples)
    rms = float(np.sqrt(np.mean(samples**2) + 1e-9))
    if rms < 1e-4:  # Silenzio
        return np.zeros(total_dim, dtype=np.float32), 160.0

    # Pre-enfasi per esaltare le risonanze delle formanti vocali
    pre_emph = 0.97
    samples_emph = np.append(samples[0], samples[1:] - pre_emph * samples[:-1])

    # Parametri framing: finestra 25ms, hop 10ms
    win_len = int(sr * 0.025)  # 400 campioni a 16kHz
    hop_len = int(sr * 0.010)  # 160 campioni a 16kHz
    n_fft = 512

    if len(samples_emph) < win_len:
        samples_emph = np.pad(samples_emph, (0, win_len - len(samples_emph)))
        samples = np.pad(samples, (0, win_len - len(samples)))

    n_frames = max(1, (len(samples_emph) - win_len) // hop_len + 1)
    window = np.hanning(win_len).astype(np.float32)

    mel_fb, dct_m = _get_dsp_bases(sr)

    # Range lag per pitch F0 (65 Hz a 400 Hz)
    min_lag = max(2, int(sr / 400.0))
    max_lag = min(win_len - 1, int(sr / 65.0))

    frame_mfccs = []
    frame_pitches = []
    frame_hnrs = []
    frame_centroids = []
    frame_rolloffs = []
    frame_energies = []
    is_voiced_list = []

    freq_bins = np.fft.rfftfreq(n_fft, d=1.0 / sr)

    for i in range(n_frames):
        st = i * hop_len
        fr_raw = samples[st : st + win_len]
        fr_emph = samples_emph[st : st + win_len]

        energy = float(np.sum(fr_raw**2)) + 1e-9
        frame_energies.append(energy)

        # 1. Pitch e Harmonicity tramite autocorrelazione normalizzata sul segnale non enfatizzato
        fr_centered = fr_raw - np.mean(fr_raw)
        acorr = np.correlate(fr_centered, fr_centered, mode="full")
        acorr = acorr[len(fr_centered) - 1 :]
        r0 = acorr[0] if acorr[0] > 0 else 1e-9

        voiced = False
        f0 = 0.0
        hnr = 0.0
        if max_lag < len(acorr):
            search = acorr[min_lag : max_lag + 1] / r0
            if len(search) > 0:
                best_rel_idx = int(np.argmax(search))
                best_val = float(search[best_rel_idx])
                if best_val > 0.28:  # Voicing threshold
                    voiced = True
                    best_lag = min_lag + best_rel_idx
                    f0 = sr / float(best_lag)
                    # HNR stimato in dB
                    harm_ratio = max(1e-4, min(0.999, best_val))
                    hnr = 10.0 * math.log10(harm_ratio / (1.0 - harm_ratio))

        is_voiced_list.append(voiced)
        if voiced:
            frame_pitches.append(f0)
            frame_hnrs.append(hnr)

        # 2. Spettrogramma e MFCC sul frame con pre-enfasi
        spec = np.abs(np.fft.rfft(fr_emph * window, n=n_fft))
        tot_spec = float(np.sum(spec)) + 1e-9

        # Centroide
        centroid = float(np.sum(freq_bins * spec) / tot_spec)
        frame_centroids.append(centroid)

        # Rolloff (85%)
        cum = np.cumsum(spec)
        r_idx = np.searchsorted(cum, 0.85 * cum[-1])
        rolloff = float(freq_bins[min(r_idx, len(freq_bins) - 1)])
        frame_rolloffs.append(rolloff)

        # Mel spectrum e MFCC
        mel_energies = np.dot(mel_fb, spec)
        log_mel = np.log(np.maximum(mel_energies, 1e-5))
        mfcc = np.dot(dct_m, log_mel)
        frame_mfccs.append(mfcc)

    frame_mfccs_arr = np.array(frame_mfccs, dtype=np.float32)  # shape (n_frames, 13)

    # Delta MFCCs
    if len(frame_mfccs_arr) >= 3:
        deltas = np.zeros_like(frame_mfccs_arr)
        deltas[1:-1] = (frame_mfccs_arr[2:] - frame_mfccs_arr[:-2]) / 2.0
        deltas[0] = frame_mfccs_arr[1] - frame_mfccs_arr[0]
        deltas[-1] = frame_mfccs_arr[-1] - frame_mfccs_arr[-2]
    else:
        deltas = np.zeros_like(frame_mfccs_arr)

    # Voice Activity Detection (VAD) Filtering:
    # Seleziona i frame con energia superiore al 25° percentile che sono voiced.
    # Se i frame voiced sono troppo pochi (<3), allarga la selezione ai frame più energetici.
    e_arr = np.array(frame_energies)
    e_thresh = float(np.percentile(e_arr, 25))
    voiced_mask = np.array(is_voiced_list) & (e_arr >= e_thresh)

    if np.sum(voiced_mask) < 3:
        top_half = e_arr >= np.median(e_arr)
        voiced_mask = top_half if np.sum(top_half) >= 1 else np.ones(len(e_arr), dtype=bool)

    selected_mfccs = frame_mfccs_arr[voiced_mask, 1:13]  # MFCC 1..12 (escludiamo c0 per invarianza volume)
    selected_deltas = deltas[voiced_mask, 1:13]

    mfcc_mean = np.mean(selected_mfccs, axis=0)
    mfcc_std = np.std(selected_mfccs, axis=0)
    delta_mean = np.mean(selected_deltas, axis=0)

    # Statistiche Pitch F0
    if len(frame_pitches) >= 2:
        f0_arr = np.array(frame_pitches, dtype=np.float32)
        p_med = float(np.median(f0_arr))
        p_floor = float(np.percentile(f0_arr, 10))
        p_iqr = float(np.percentile(f0_arr, 75) - np.percentile(f0_arr, 25))
        hnr_mean = float(np.mean(frame_hnrs))
    elif len(frame_pitches) == 1:
        p_med = float(frame_pitches[0])
        p_floor = p_med
        p_iqr = 10.0
        hnr_mean = float(frame_hnrs[0])
    else:
        p_med = 160.0
        p_floor = 140.0
        p_iqr = 15.0
        hnr_mean = 5.0

    cent_mean = float(np.mean(np.array(frame_centroids)[voiced_mask]))
    roll_mean = float(np.mean(np.array(frame_rolloffs)[voiced_mask]))

    # Composizione vettore a 42 feature con scala acustica assoluta calibrata
    # (NON dipende da standardizzazioni per-video che distruggono l'invarianza del singolo speaker)
    mfcc_scaled = (mfcc_mean / 15.0) * 1.5
    mfcc_std_scaled = (mfcc_std / 5.0) * 0.8
    delta_scaled = (delta_mean / 4.0) * 0.6

    # Pitch su scala logaritmica assoluta in ottave (distanza di genere e registro vocale)
    log_pitch = math.log2(max(50.0, p_med) / 100.0) * 1.5
    log_pitch_floor = math.log2(max(50.0, p_floor) / 100.0) * 1.5

    feat = np.concatenate([
        mfcc_scaled,                     # 12 dims (risonanze vocaliche stabili)
        mfcc_std_scaled,                 # 12 dims (variabilità timbrica)
        delta_scaled,                    # 12 dims (dinamica articolatoria)
        np.array([
            log_pitch,                   # 1 dim: F0 mediana su scala ottave
            log_pitch_floor,             # 1 dim: F0 registro basso
            (p_iqr / 100.0) * 0.5,       # 1 dim: F0 escursione
            (hnr_mean / 20.0) * 0.8,     # 1 dim: Purezza armonica
            (cent_mean / 4000.0) * 0.8,  # 1 dim: Centroide
            (roll_mean / 6000.0) * 0.8,  # 1 dim: Rolloff
        ], dtype=np.float32)
    ])
    norm = float(np.linalg.norm(feat))
    if norm > 1e-9:
        feat = feat / norm

    return feat, p_med


def _cosine_kmeans_cluster(features: np.ndarray, k: int = 2, max_iters: int = 40, n_inits: int = 15) -> np.ndarray:
    """
    K-Means sferico basato sulla distanza del Coseno con K-means++ initialization
    e restart multipli per trovare la migliore separazione timbrica globale.
    """
    n_samples, n_features = features.shape
    if n_samples <= k:
        return np.arange(n_samples) % k

    # Normalizza ogni campione sulla sfera unitaria
    norms = np.linalg.norm(features, axis=1, keepdims=True) + 1e-9
    unit_feats = features / norms

    best_inertia = -float("inf")
    best_labels = np.zeros(n_samples, dtype=int)

    for _ in range(n_inits):
        # K-Means++ initialization
        first_idx = np.random.randint(0, n_samples)
        centers = [unit_feats[first_idx]]

        for _ in range(1, k):
            # Calcola minima distanza coseno rispetto ai centri esistenti (1 - cos_sim)
            cos_sims = np.array([np.dot(unit_feats, c) for c in centers])  # shape (len(centers), n_samples)
            min_dists = np.clip(1.0 - np.max(cos_sims, axis=0), 0.0, 2.0) ** 2
            tot_dist = float(np.sum(min_dists))
            if tot_dist > 1e-9:
                probs = min_dists / tot_dist
                next_idx = np.random.choice(n_samples, p=probs)
            else:
                next_idx = np.random.randint(0, n_samples)
            centers.append(unit_feats[next_idx])

        centers = np.array(centers, dtype=np.float32)

        # Iterazioni EM
        labels = np.zeros(n_samples, dtype=int)
        for _ in range(max_iters):
            # Similarità coseno con ogni centro
            sim_matrix = np.dot(unit_feats, centers.T)  # shape (n_samples, k)
            new_labels = np.argmax(sim_matrix, axis=1)

            if np.array_equal(new_labels, labels):
                break
            labels = new_labels

            for j in range(k):
                mask = (labels == j)
                if np.any(mask):
                    mean_v = np.mean(unit_feats[mask], axis=0)
                    centers[j] = mean_v / (np.linalg.norm(mean_v) + 1e-9)

        # Calcola similarità coseno totale (inerzia sferica)
        sim_matrix = np.dot(unit_feats, centers.T)
        inertia = float(np.sum([sim_matrix[i, labels[i]] for i in range(n_samples)]))
        if inertia > best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()

    return best_labels


def _viterbi_temporal_smoothing(
    features: np.ndarray,
    raw_labels: np.ndarray,
    chunks: list[dict[str, Any]],
    k: int = 2,
) -> np.ndarray:
    """
    Raffina le etichette con decodifica Viterbi (HMM a stati discreti).
    Modella la probabilità di emissione basandosi sulla somiglianza timbrica ai centroidi
    e la probabilità di transizione penalizzando cambi speaker improvvisi, ma consentendo
    i turni di conversazione naturali dopo pause e silenzi.
    """
    n_samples = len(features)
    if n_samples < 3 or k <= 1:
        return raw_labels

    norms = np.linalg.norm(features, axis=1, keepdims=True) + 1e-9
    unit_feats = features / norms

    # Calcola i centroidi timbrici
    centers = np.zeros((k, unit_feats.shape[1]), dtype=np.float32)
    for j in range(k):
        mask = (raw_labels == j)
        if np.any(mask):
            mean_v = np.mean(unit_feats[mask], axis=0)
            centers[j] = mean_v / (np.linalg.norm(mean_v) + 1e-9)
        else:
            centers[j] = unit_feats[j % n_samples]

    # Similarità coseno dei campioni rispetto a ciascun centro: shape (n_samples, k)
    sims = np.dot(unit_feats, centers.T)
    # Emission log-likelihood scalata: pondera fortemente la fedeltà acustica
    emission_log = sims * 18.0

    # Viterbi DP
    viterbi = np.zeros((n_samples, k), dtype=np.float32)
    backpointer = np.zeros((n_samples, k), dtype=int)

    # Inizializzazione
    viterbi[0] = emission_log[0]

    for t in range(1, n_samples):
        # Calcola gap temporale dal blocco precedente
        prev_end = float(chunks[t - 1].get("end", 0.0))
        cur_start = float(chunks[t].get("start", prev_end))
        gap = max(0.0, cur_start - prev_end)

        # In un dialogo o intervista reale, il turn-taking tra oratori avviene frequentemente
        # con pause brevi (150ms-400ms). Le transizioni devono essere naturali.
        if gap < 0.15:
            p_switch = 0.18
        elif gap < 0.6:
            p_switch = 0.28
        elif gap < 1.2:
            p_switch = 0.38
        else:
            p_switch = 0.48

        stay_log = math.log(max(1e-6, 1.0 - p_switch))
        switch_log = math.log(max(1e-6, p_switch / max(1, k - 1)))

        for curr_st in range(k):
            # Calcola max su prev_st
            trans_scores = [
                viterbi[t - 1, prev_st] + (stay_log if prev_st == curr_st else switch_log)
                for prev_st in range(k)
            ]
            best_prev = int(np.argmax(trans_scores))
            viterbi[t, curr_st] = trans_scores[best_prev] + emission_log[t, curr_st]
            backpointer[t, curr_st] = best_prev

    # Backtracking
    best_last = int(np.argmax(viterbi[-1]))
    best_path = [best_last]
    for t in range(n_samples - 1, 0, -1):
        best_last = backpointer[t, best_last]
        best_path.append(best_last)
    best_path.reverse()

    result_arr = np.array(best_path, dtype=int)
    # Controllo anti-soppressione: se il smoothing ha azzerato completamente un cluster
    # mentre raw_labels conteneva entrambi gli speaker, ripristina raw_labels
    if len(np.unique(result_arr)) < k and len(np.unique(raw_labels)) >= k:
        return raw_labels

    return result_arr


def _evaluate_two_clusters(feat_weighted: np.ndarray, labels: np.ndarray) -> tuple[float, float, float]:
    """Valuta la separabilità acustica tra 2 cluster (distanza centroidi, silhouette score, bilanciamento)."""
    norms = np.linalg.norm(feat_weighted, axis=1, keepdims=True) + 1e-9
    unit_feats = feat_weighted / norms

    n_samples = len(unit_feats)
    m0 = (labels == 0)
    m1 = (labels == 1)

    n0 = int(np.sum(m0))
    n1 = int(np.sum(m1))
    if n0 == 0 or n1 == 0:
        return 0.0, -1.0, 0.0

    c0 = np.mean(unit_feats[m0], axis=0)
    c0 = c0 / (np.linalg.norm(c0) + 1e-9)
    c1 = np.mean(unit_feats[m1], axis=0)
    c1 = c1 / (np.linalg.norm(c1) + 1e-9)

    centroid_dist = float(1.0 - np.dot(c0, c1))
    min_ratio = min(n0, n1) / float(n_samples)

    if n_samples < 4 or min(n0, n1) < 2:
        return centroid_dist, 0.0, min_ratio

    silhouettes = []
    for i in range(n_samples):
        same_mask = m0 if labels[i] == 0 else m1
        other_mask = m1 if labels[i] == 0 else m0

        dists_same = 1.0 - np.dot(unit_feats[same_mask], unit_feats[i])
        a_i = float(np.mean(dists_same)) if len(dists_same) > 1 else 0.0

        dists_other = 1.0 - np.dot(unit_feats[other_mask], unit_feats[i])
        b_i = float(np.mean(dists_other)) if len(dists_other) > 0 else 1.0

        denom = max(a_i, b_i, 1e-6)
        silhouettes.append((b_i - a_i) / denom)

    mean_sil = float(np.mean(silhouettes)) if silhouettes else 0.0
    return centroid_dist, mean_sil, min_ratio


def diarize_audio(
    wav_path: Path,
    chunks: list[dict[str, Any]],
    num_speakers: int | str = "auto",
) -> list[dict[str, Any]]:
    """
    Esegue la diarizzazione automatica ad alta precisione dei chunk basandosi sul segnale audio.
    Rileva automaticamente se l'audio contiene 1 solo interlocutore (monologo) o più interlocutori distinti.
    Assegna 'speaker' ("Speaker 1", "Speaker 2", ...) e 'speaker_id' (0, 1, ...) a ogni chunk.

    Args:
        wav_path: Percorso del file audio WAV 16kHz.
        chunks: Lista di dizionari con i sottotitoli (devono contenere 'start' ed 'end').
        num_speakers: Numero di interlocutori ("auto", 1, 2, 3, default "auto").

    Returns:
        Lista di chunk arricchita con le informazioni sullo speaker.
    """
    if not chunks:
        return []

    is_auto = False
    if num_speakers is None or str(num_speakers).strip().lower() in ("auto", "0", "automatico"):
        is_auto = True
        target_k = 2
    else:
        try:
            target_k = max(1, min(4, int(num_speakers)))
            if target_k == 1:
                for c in chunks:
                    c["speaker"] = "Speaker 1"
                    c["speaker_id"] = 0
                return chunks
        except Exception:
            is_auto = True
            target_k = 2

    if len(chunks) < 2:
        for c in chunks:
            c["speaker"] = "Speaker 1"
            c["speaker_id"] = 0
        return chunks

    if not wav_path.exists():
        console.log(f"[yellow]⚠ File WAV non trovato per diarizzazione: {wav_path}[/]")
        for c in chunks:
            if "speaker" not in c:
                c["speaker"] = "Speaker 1"
                c["speaker_id"] = 0
        return chunks

    console.log(f"[cyan]🎙️ Avvio analisi acustica avanzata su {len(chunks)} blocchi (modalità: {'auto-detect' if is_auto else f'target {target_k}'})...[/]")

    feature_list = []
    pitch_list = []
    for i, chunk in enumerate(chunks):
        c_start = float(chunk.get("start", 0.0))
        c_end = float(chunk.get("end", c_start + 1.0))

        # Margine contestuale di 60ms
        seg_start = max(0.0, c_start - 0.06)
        seg_end = c_end + 0.06

        try:
            samples, sr = _read_wav_segment(wav_path, seg_start, seg_end)
            feats, p_med = _extract_voice_features(samples, sr=sr)
            feature_list.append(feats)
            pitch_list.append(p_med)
        except Exception as exc:
            console.log(f"[yellow]⚠ Errore analisi acustica blocco #{i}: {exc}[/]")
            feature_list.append(np.zeros(42, dtype=np.float32))
            pitch_list.append(160.0)

    feat_matrix = np.array(feature_list, dtype=np.float32)

    # I vettori sono già calibrati in scala acustica fisica assoluta e normalizzati sulla sfera unitaria.
    # NON applichiamo standardizzazioni per-video (z-score) perché trasformerebbero
    # le minime fluttuazioni prosodiche di un singolo speaker in cluster artificiali.
    weights = np.ones(42, dtype=np.float32)
    weights[0:4] = 2.2       # MFCC 1-4 (formanti base)
    weights[4:12] = 1.4      # MFCC 5-12
    weights[12:24] = 1.2     # MFCC std
    weights[24:36] = 1.0     # Delta MFCC
    weights[36:38] = 3.0     # Pitch mediana e registro base logaritmici (ottima discriminazione tra interlocutori)
    weights[38] = 1.2        # Pitch IQR
    weights[39] = 1.4        # HNR
    weights[40:42] = 1.2     # Centroide e Rolloff

    feat_weighted = feat_matrix * weights
    # Rinormalizza i vettori pesati sulla sfera unitaria
    norms = np.linalg.norm(feat_weighted, axis=1, keepdims=True) + 1e-9
    feat_weighted = feat_weighted / norms

    # Valutazione clustering a 2 cluster per auto-detection
    raw_labels = _cosine_kmeans_cluster(feat_weighted, k=2, n_inits=20)
    c_dist, sil, ratio = _evaluate_two_clusters(feat_weighted, raw_labels)

    # Calcola la differenza di frequenza fondamentale F0 mediana tra i due ipotetici cluster
    p0_list = [pitch_list[i] for i in range(len(chunks)) if raw_labels[i] == 0]
    p1_list = [pitch_list[i] for i in range(len(chunks)) if raw_labels[i] == 1]
    f0_c0 = float(np.median(p0_list)) if p0_list else 160.0
    f0_c1 = float(np.median(p1_list)) if p1_list else 160.0
    pitch_diff = abs(f0_c0 - f0_c1)

    console.log(
        f"[cyan]📊 Valutazione acustica separazione: distanza={c_dist:.4f}, silhouette={sil:.3f}, "
        f"bilanciamento={ratio:.2f}, delta_pitch={pitch_diff:.1f}Hz[/]"
    )

    # Criterio acustico calibrato per distinguere 1 speaker (monologo) da 2 o più speaker (dialogo).
    # In dialoghi reali con interlocutori dello stesso sesso o registrati dallo stesso microfono,
    # la distanza spettrale c_dist si attesta tra 0.055 e 0.12 e il delta pitch può essere anche di 10-18 Hz.
    # L'algoritmo non deve collassare arbitrariamente in monologo se vi sono evidenze di cambi voce.
    if len(chunks) <= 2:
        is_genuine_dialogue = (
            c_dist >= 0.18 or (pitch_diff >= 22.0 and c_dist >= 0.10)
        )
    else:
        is_genuine_dialogue = (
            c_dist >= 0.055 and ratio >= 0.06 and (sil >= 0.08 or pitch_diff >= 10.0 or c_dist >= 0.085)
        )

    if is_auto:
        actual_k = 2 if is_genuine_dialogue else 1
    else:
        # Quando l'utente specifica target_k (es. 2 o 3 speaker), rispetta rigorosamente la sua scelta
        # a meno che il numero totale di chunk sia inferiore a target_k.
        if target_k <= 1:
            actual_k = 1
        else:
            actual_k = min(target_k, len(chunks))

    if actual_k == 1:
        console.log("[green]✓ Rilevato singolo speaker (monologo). Assegnato Speaker 1 a tutti i blocchi.[/]")
        for c in chunks:
            c["speaker_id"] = 0
            c["speaker"] = "Speaker 1"
        return chunks

    # Se sono 2 o più speaker, applica Viterbi per continuità temporale
    smoothed_labels = _viterbi_temporal_smoothing(feat_weighted, raw_labels, chunks, k=actual_k)

    # Normalizza l'identità del primo speaker parlante a "Speaker 1" (ID 0)
    first_label = smoothed_labels[0]
    mapping = {first_label: 0}
    next_id = 1
    for lbl in smoothed_labels:
        if lbl not in mapping:
            mapping[lbl] = next_id
            next_id += 1

    final_labels = np.array([mapping[l] for l in smoothed_labels], dtype=int)

    # Assegna le etichette ai blocchi
    speaker_names = [f"Speaker {j + 1}" for j in range(actual_k)]
    for idx, chunk in enumerate(chunks):
        spk_id = int(final_labels[idx])
        chunk["speaker_id"] = spk_id
        chunk["speaker"] = speaker_names[spk_id]

    counts = {spk: sum(1 for c in chunks if c.get("speaker") == spk) for spk in speaker_names}
    console.log(f"[green]✓ Diarizzazione acustica completata con successo ({actual_k} speaker): {counts}[/]")
    return chunks
