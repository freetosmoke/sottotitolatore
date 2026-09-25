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

import os
import re

from rich.console import Console

console = Console(stderr=True)


from bootstrap_manager import get_ffmpeg_path, get_ffprobe_path


def _get_bin(name: str) -> str:
    """Restituisce il percorso del binario (ffmpeg/ffprobe) dando priorità al BootstrapManager."""
    if name == "ffmpeg":
        return get_ffmpeg_path()
    if name == "ffprobe":
        probe = get_ffprobe_path()
        return probe if probe else get_ffmpeg_path()

    candidates = [
        Path(__file__).resolve().parent / "bin" / name,
        Path(__file__).resolve().parent.parent / "bin" / name,
        Path(__file__).resolve().parent.parent / "Resources" / "bin" / name,
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    return name


def _hw_available() -> bool:
    r = subprocess.run([_get_bin("ffmpeg"), "-hide_banner", "-encoders"], capture_output=True, text=True)
    return "h264_videotoolbox" in r.stdout


def get_video_duration(video_path: Path) -> float:
    """Legge la durata del file video con ffprobe o direttamente con ffmpeg."""
    try:
        r = subprocess.run(
            [_get_bin("ffprobe"), "-v", "error",
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
        r = subprocess.run([_get_bin("ffmpeg"), "-i", str(video_path)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            h, mn, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
            return h * 3600 + mn * 60 + s
    except Exception as exc:
        raise RuntimeError(f"Impossibile leggere la durata del video con ffmpeg: {exc}")

    raise RuntimeError(f"Impossibile determinare la durata del video per: {video_path}")


def get_video_dimensions(video_path: Path) -> tuple[int, int]:
    """Legge larghezza e altezza del video con ffprobe o ffmpeg (default 1080x1920)."""
    try:
        r = subprocess.run(
            [_get_bin("ffprobe"), "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=s=x:p=0",
             str(video_path)],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split("x")
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
    except Exception:
        pass

    try:
        r = subprocess.run([_get_bin("ffmpeg"), "-i", str(video_path)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        m = re.search(r",\s*(\d{2,5})x(\d{2,5})", r.stderr)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass

    return 1080, 1920


def burn_subtitles(
    video_path: Path,
    ffconcat_path: Path,
    watermark_path: Path,
    output_path: Path,
    use_hw: bool | None = None,
    quality: str = "high",
    black_and_white: bool = False,
    video_filter: str = "none",
    mute_intervals: list[tuple[float, float]] | None = None,
    speed: float = 1.0,
    bgm_path: Path | None = None,
    bgm_volume: float = 0.20,
    bgm_fade_in: float = 1.0,
    bgm_fade_out: float = 1.0,
    total_duration: float | None = None,
) -> Path:
    """
    Sovrappone sottotitoli e watermark al video originale ad alta qualità,
    supportando filtri video rapidi (B&W Cinema, B&W Vintage, Vibrant), velocità modificata (0.5x - 2x)
    e musica di sottofondo con dissolvenza.
    """
    if use_hw is None:
        use_hw = _hw_available() and sys.platform == "darwin"

    # Risolve modalità B&W per retrocompatibilità
    is_bw = black_and_white or video_filter in ("bw", "bw_cinema", "bw_vintage")

    if use_hw:
        if quality == "max":
            q_val = "95"
        elif quality == "standard":
            q_val = "85"
        else:
            q_val = "90"
        vcodec = ["-c:v", "h264_videotoolbox", "-q:v", q_val, "-profile:v", "high"]
        console.log(f"[cyan]Codec:[/] h264_videotoolbox (Apple Silicon HW, q:v={q_val}, qualità={quality}, bw={is_bw}, filter={video_filter}, speed={speed}x)")
    else:
        if quality == "max":
            crf_val = "14"
        elif quality == "standard":
            crf_val = "18"
        else:
            crf_val = "16"
        vcodec = ["-c:v", "libx264", "-crf", crf_val, "-preset", "slow", "-pix_fmt", "yuv420p"]
        console.log(f"[cyan]Codec:[/] libx264 (software, crf={crf_val}, bw={is_bw}, filter={video_filter}, speed={speed}x)")

    # 1. Filtro video: effetti rapidi (B&W Cinema, B&W Vintage, Vibrant) e velocità
    v_filters = []
    if video_filter == "bw_cinema":
        v_filters.append("hue=s=0,eq=contrast=1.18:brightness=0.01")
    elif video_filter == "bw_vintage":
        v_filters.append("hue=s=0,eq=contrast=0.96:gamma=1.05")
    elif video_filter == "vibrant":
        v_filters.append("eq=saturation=1.35:contrast=1.06")
    elif is_bw:
        v_filters.append("hue=s=0")

    if speed != 1.0 and speed > 0:
        pts_factor = 1.0 / speed
        v_filters.append(f"setpts={pts_factor:.6f}*PTS")

    if v_filters:
        v_chain = ",".join(v_filters)
        video_prep = f"[0:v]{v_chain}[bg];"
        bg_stream = "[bg]"
    else:
        video_prep = ""
        bg_stream = "[0:v]"

    filter_complex_parts = [
        video_prep,
        f"{bg_stream}[1:v]overlay=0:0:eof_action=pass[v1];",
        "[v1][2:v]overlay=0:0:eof_action=pass,format=yuv420p[out];"
    ]

    # 2. Filtro audio principale (speaker muting + audio speed)
    main_a_filters = []
    if speed != 1.0 and speed > 0:
        # atempo supporta range 0.5 - 2.0
        clamped_speed = max(0.5, min(2.0, speed))
        main_a_filters.append(f"atempo={clamped_speed:.4f}")

    if mute_intervals:
        valid_intervals = [
            (max(0.0, float(s)), max(0.0, float(e)))
            for s, e in mute_intervals
            if float(e) > float(s)
        ]
        if valid_intervals:
            between_expr = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in valid_intervals)
            main_a_filters.append(f"volume=enable='{between_expr}':volume=0")
            console.log(f"[yellow]🔇 Applicato silenziamento audio per {len(valid_intervals)} intervalli[/]")

    # 3. Gestione Background Music (BGM)
    has_bgm = bgm_path is not None and Path(bgm_path).exists()
    extra_inputs = []

    if has_bgm:
        bgm_p = Path(bgm_path).resolve()
        extra_inputs = ["-i", str(bgm_p)]
        # bgm è input indice 3
        eff_dur = (total_duration / speed) if (total_duration and speed > 0) else (get_video_duration(video_path) / (speed if speed > 0 else 1.0))
        fade_out_st = max(0.1, eff_dur - bgm_fade_out)

        # Filtri BGM: volume, fade-in, fade-out
        bgm_f = f"[3:a]volume={bgm_volume:.3f},afade=t=in:ss=0:d={bgm_fade_in:.2f},afade=t=out:st={fade_out_st:.2f}:d={bgm_fade_out:.2f}[bgm_proc];"
        filter_complex_parts.append(bgm_f)

        if main_a_filters:
            main_f = f"[0:a]{','.join(main_a_filters)}[main_proc];"
            filter_complex_parts.append(main_f)
            filter_complex_parts.append("[main_proc][bgm_proc]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        else:
            filter_complex_parts.append("[0:a][bgm_proc]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        final_a_map = ["[aout]"]
    else:
        if main_a_filters:
            filter_complex_parts.append(f"[0:a]{','.join(main_a_filters)}[aout]")
            final_a_map = ["[aout]"]
        else:
            final_a_map = ["0:a?"]

    full_filter_complex = "".join(filter_complex_parts).rstrip(";")

    cmd = [
        _get_bin("ffmpeg"), "-y",
        "-i", str(video_path.resolve()),                           # [0] video
        "-f", "concat", "-safe", "0",
        "-i", str(ffconcat_path.resolve()),                        # [1] sottotitoli
        "-loop", "1", "-i", str(watermark_path.resolve()),         # [2] watermark
        *extra_inputs,                                             # [3] eventuale bgm
        "-filter_complex", full_filter_complex,
        "-map", "[out]",
        "-map", *final_a_map,
        *vcodec,
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        str(output_path.resolve()),
    ]

    console.log(f"[cyan]Rendering:[/] {video_path.name} → {output_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg fallito (exit {result.returncode}):\n{result.stderr}"
        )

    console.log(f"[green]✓ Video renderizzato:[/] {output_path}")
    return output_path
