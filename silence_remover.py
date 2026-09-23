"""
silence_remover.py
Rilevamento e rimozione fisica dei segmenti di silenzio da video e audio,
con risincronizzazione deterministica dei sottotitoli e delle parole.
"""
from __future__ import annotations

import copy
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable


def _log(msg: str) -> None:
    sys.stderr.write(f"[silence_remover] {msg}\n")
    sys.stderr.flush()


def detect_silence_segments(
    video_path: Path,
    min_silence_duration: float = 0.3,
    noise_threshold_db: float = -30.0,
) -> list[tuple[float, float]]:
    """
    Rileva gli intervalli di silenzio (start, end) analizzando la traccia audio con FFmpeg silencedetect.
    Ritorna una lista di tuple [(start, end), ...] con durata >= min_silence_duration.
    """
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(video_path.resolve()),
        "-vn",
        "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]
    r = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    lines = r.stderr.splitlines()

    silences: list[tuple[float, float]] = []
    current_start: float | None = None

    for line in lines:
        if "silencedetect" not in line:
            continue
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            current_start = float(start_match.group(1))
            continue

        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match and current_start is not None:
            silence_end = float(end_match.group(1))
            dur = silence_end - current_start
            if dur >= (min_silence_duration - 0.02):
                silences.append((round(current_start, 3), round(silence_end, 3)))
            current_start = None

    _log(f"{len(silences)} silenzi rilevati >= {min_silence_duration}s a {noise_threshold_db}dB")
    return silences


def calculate_keep_intervals(
    total_duration: float,
    silence_intervals: list[tuple[float, float]],
    min_keep_duration: float = 0.05,
) -> list[tuple[float, float]]:
    """
    Inverte gli intervalli di silenzio calcolando i segmenti di parlato/suono da preservare.
    Fonde eventuali silenzi adiacenti o sovrapposti.
    Ritorna una lista di [(keep_start, keep_end), ...].
    """
    if not silence_intervals:
        return [(0.0, total_duration)] if total_duration > 0 else []

    sorted_silences = sorted(silence_intervals, key=lambda x: x[0])
    merged_silences: list[list[float]] = []
    for s_start, s_end in sorted_silences:
        s_start = max(0.0, min(s_start, total_duration))
        s_end = max(0.0, min(s_end, total_duration))
        if s_end <= s_start:
            continue
        if not merged_silences:
            merged_silences.append([s_start, s_end])
        else:
            prev = merged_silences[-1]
            if s_start <= prev[1] + 0.02:
                prev[1] = max(prev[1], s_end)
            else:
                merged_silences.append([s_start, s_end])

    keeps: list[tuple[float, float]] = []
    cur_pos = 0.0
    for s_start, s_end in merged_silences:
        if s_start > cur_pos:
            dur = s_start - cur_pos
            if dur >= min_keep_duration:
                keeps.append((round(cur_pos, 3), round(s_start, 3)))
        cur_pos = max(cur_pos, s_end)

    if total_duration - cur_pos >= min_keep_duration:
        keeps.append((round(cur_pos, 3), round(total_duration, 3)))

    return keeps


def build_timestamp_mapper(
    keep_intervals: list[tuple[float, float]]
) -> Callable[[float], float]:
    """
    Crea una funzione di mapping continuo original_time -> output_time.
    Se un punto cade in un intervallo conservato, viene compattato.
    Se cade all'interno di un silenzio eliminato, viene proiettato sul punto di taglio.
    """
    mapped_segments = []
    accumulated_out = 0.0
    for k_start, k_end in keep_intervals:
        dur = k_end - k_start
        mapped_segments.append((k_start, k_end, accumulated_out, accumulated_out + dur))
        accumulated_out += dur

    def remap(t: float) -> float:
        if not mapped_segments:
            return 0.0
        if t <= mapped_segments[0][0]:
            return 0.0
        last_seg = mapped_segments[-1]
        if t >= last_seg[1]:
            return round(last_seg[3], 3)

        for k_start, k_end, out_start, out_end in mapped_segments:
            if k_start <= t <= k_end:
                return round(out_start + (t - k_start), 3)

        for i in range(len(mapped_segments) - 1):
            cur = mapped_segments[i]
            nxt = mapped_segments[i + 1]
            if cur[1] < t < nxt[0]:
                return round(cur[3], 3)

        return round(accumulated_out, 3)

    return remap


def remap_chunks_and_words(
    chunks: list[dict],
    keep_intervals: list[tuple[float, float]],
    min_chunk_duration: float = 0.15,
) -> list[dict]:
    """
    Rimappa start ed end di ogni chunk e di ogni singola parola usando la timeline compattata.
    """
    mapper = build_timestamp_mapper(keep_intervals)
    new_chunks = []

    for c in chunks:
        c_copy = copy.deepcopy(c)
        orig_s = float(c_copy.get("start", 0.0))
        orig_e = float(c_copy.get("end", orig_s + 0.5))

        new_s = mapper(orig_s)
        new_e = mapper(orig_e)

        if new_e <= new_s + 0.05:
            new_e = round(new_s + min_chunk_duration, 3)

        c_copy["start"] = new_s
        c_copy["end"] = new_e

        if "words" in c_copy and isinstance(c_copy["words"], list):
            new_words = []
            for w in c_copy["words"]:
                w_copy = dict(w)
                w_s = float(w_copy.get("start", orig_s))
                w_e = float(w_copy.get("end", orig_e))
                new_ws = mapper(w_s)
                new_we = mapper(w_e)
                if new_we < new_ws:
                    new_we = new_ws + 0.05
                w_copy["start"] = new_ws
                w_copy["end"] = new_we
                new_words.append(w_copy)
            c_copy["words"] = new_words

        new_chunks.append(c_copy)

    new_chunks.sort(key=lambda x: x["start"])
    for i in range(len(new_chunks) - 1):
        cur = new_chunks[i]
        nxt = new_chunks[i + 1]
        if cur["end"] > nxt["start"]:
            cur["end"] = max(cur["start"] + 0.05, nxt["start"])

    return new_chunks


def cut_and_compact_video_audio(
    video_path: Path,
    keep_intervals: list[tuple[float, float]],
    output_path: Path,
    use_hw: bool = True,
    quality: str = "high",
) -> tuple[Path, float]:
    """
    Taglia fisicamente ed in modo perfettamente sincronizzato sia il flusso video che il flusso audio
    rimuovendo gli intervalli di silenzio ed unificando i segmenti conservati.
    """
    if not keep_intervals:
        raise ValueError("Nessun intervallo di parlato da conservare trovato nel video.")

    from video_renderer import get_video_duration
    orig_dur = get_video_duration(video_path)

    total_keep_dur = sum(k_end - k_start for k_start, k_end in keep_intervals)
    _log(f"Compattamento: {len(keep_intervals)} segmenti. Durata stimata: {orig_dur:.2f}s → {total_keep_dur:.2f}s")

    filter_parts = []
    concat_inputs = []
    for i, (k_start, k_end) in enumerate(keep_intervals):
        v_label = f"v{i}"
        a_label = f"a{i}"
        filter_parts.append(f"[0:v]trim=start={k_start}:end={k_end},setpts=PTS-STARTPTS[{v_label}];")
        filter_parts.append(f"[0:a]atrim=start={k_start}:end={k_end},asetpts=PTS-STARTPTS[{a_label}];")
        concat_inputs.append(f"[{v_label}][{a_label}]")

    num_segments = len(keep_intervals)
    concat_filter = f"{''.join(concat_inputs)}concat=n={num_segments}:v=1:a=1[outv][outa]"
    filter_parts.append(concat_filter)
    full_filter_complex = "".join(filter_parts)

    if use_hw:
        q_val = "95" if quality == "max" else ("85" if quality == "standard" else "90")
        vcodec = ["-c:v", "h264_videotoolbox", "-q:v", q_val]
    else:
        crf_val = "14" if quality == "max" else ("18" if quality == "standard" else "16")
        vcodec = ["-c:v", "libx264", "-crf", crf_val, "-preset", "fast", "-pix_fmt", "yuv420p"]

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path.resolve()),
        "-filter_complex", full_filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        *vcodec,
        "-c:a", "aac",
        "-b:a", "320k",
        str(output_path.resolve())
    ]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        _log(f"Errore ffmpeg compattamento: {r.stderr}")
        raise RuntimeError(f"Errore durante il taglio e ricompattamento: {r.stderr[-400:]}")

    new_dur = get_video_duration(output_path)
    _log(f"Video compattato con successo: {output_path.name} (nuova durata: {new_dur:.2f}s)")
    return output_path, new_dur
