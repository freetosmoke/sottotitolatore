"""
video_renderer.py
Burn-in sottotitoli con ffmpeg usando ffconcat + overlay.
- Input 0: video originale
- Input 1: sequenza sottotitoli (ffconcat → singolo stream)
- Input 2: watermark PNG (loop)
Solo 2 operazioni overlay invece di N, indipendente dal numero di chunk.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console(stderr=True)


def _hw_available() -> bool:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return "h264_videotoolbox" in r.stdout


import re

def get_video_duration(video_path: Path) -> float:
    """Legge la durata del file video con ffprobe o direttamente con ffmpeg."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(video_path)],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip())
    except Exception:
        pass

    try:
        r = subprocess.run(["ffmpeg", "-i", str(video_path)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            h, mn, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
            return h * 3600 + mn * 60 + s
    except Exception as exc:
        raise RuntimeError(f"Impossibile leggere la durata del video con ffmpeg: {exc}")

    raise RuntimeError(f"Impossibile determinare la durata del video per: {video_path}")


def burn_subtitles(
    video_path: Path,
    ffconcat_path: Path,
    watermark_path: Path,
    output_path: Path,
    use_hw: bool | None = None,
    quality: str = "high",
    black_and_white: bool = False,
) -> Path:
    """
    Sovrappone sottotitoli e watermark al video originale ad alta qualità.

    Usa ffconcat come singolo stream di input per i sottotitoli,
    riducendo a 2 le operazioni overlay totali.

    Qualità supportate:
    - 'high' (default): ~10-12 Mbps su Apple Silicon (-q:v 90), bitrate ideale e ultra-nitido per social HD.
    - 'max': ~18-20 Mbps (-q:v 95), qualità master senza alcuna perdita percepibile.
    - 'standard': ~6 Mbps (-q:v 85), allineato al bitrate sorgente medio.
    """
    if use_hw is None:
        use_hw = _hw_available() and sys.platform == "darwin"

    if use_hw:
        if quality == "max":
            q_val = "95"
        elif quality == "standard":
            q_val = "85"
        else:
            q_val = "90"
        vcodec = ["-c:v", "h264_videotoolbox", "-q:v", q_val, "-profile:v", "high"]
        console.log(f"[cyan]Codec:[/] h264_videotoolbox (Apple Silicon HW, q:v={q_val}, qualità={quality}, bw={black_and_white})")
    else:
        if quality == "max":
            crf_val = "14"
        elif quality == "standard":
            crf_val = "18"
        else:
            crf_val = "16"
        vcodec = ["-c:v", "libx264", "-crf", crf_val, "-preset", "slow", "-pix_fmt", "yuv420p"]
        console.log(f"[cyan]Codec:[/] libx264 (software, crf={crf_val}, bw={black_and_white})")

    # Se black_and_white è attivo, desatura il video di sfondo preservando i sottotitoli e watermark a colori
    if black_and_white:
        filter_complex = (
            "[0:v]hue=s=0[bw];"
            "[bw][1:v]overlay=0:0:eof_action=pass[v1];"
            "[v1][2:v]overlay=0:0:eof_action=pass,format=yuv420p[out]"
        )
    else:
        filter_complex = (
            "[0:v][1:v]overlay=0:0:eof_action=pass[v1];"
            "[v1][2:v]overlay=0:0:eof_action=pass,format=yuv420p[out]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path.resolve()),                           # [0] video
        "-f", "concat", "-safe", "0",
        "-i", str(ffconcat_path.resolve()),                        # [1] sottotitoli
        "-loop", "1", "-i", str(watermark_path.resolve()),         # [2] watermark
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "0:a",
        *vcodec,
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        str(output_path.resolve()),
    ]

    console.log(f"[cyan]Rendering:[/] {video_path.name} → {output_path.name}")
    result = subprocess.run(cmd, text=True)

    if result.returncode != 0:
        raise RuntimeError("ffmpeg fallito. Controlla l'output sopra.")

    console.log(f"[green]✓ Video renderizzato:[/] {output_path}")
    return output_path
