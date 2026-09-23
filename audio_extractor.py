"""
audio_extractor.py
Modulo per l'estrazione dell'audio da file video in formato WAV 16kHz mono.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

from video_renderer import _get_bin

console = Console(stderr=True)


def extract_audio(video_path: Path, output_wav: Path | None = None) -> Path:
    """
    Estrae l'audio dal video in WAV 16kHz mono.

    Args:
        video_path: Percorso del file video sorgente.
        output_wav:  Percorso di destinazione per il WAV (opzionale).
                     Se omesso viene creato un file temporaneo.

    Returns:
        Path del file WAV estratto.
    """
    if output_wav is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_wav = Path(tmp.name)
        tmp.close()

    console.log(f"[cyan]Estrazione audio:[/] {video_path.name} → {output_wav.name}")

    cmd = [
        _get_bin("ffmpeg"),
        "-y",                       # sovrascrittura senza prompt
        "-i", str(video_path),
        "-vn",                       # niente video
        "-ar", "16000",              # sample rate 16 kHz
        "-ac", "1",                  # mono
        "-c:a", "pcm_s16le",         # WAV PCM 16-bit
        str(output_wav),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg fallito durante l'estrazione audio:\n{result.stderr}"
        )

    console.log("[green]✓ Audio estratto correttamente[/]")
    return output_wav
