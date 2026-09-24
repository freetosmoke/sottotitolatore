#!/usr/bin/env python3
"""
main.py — SubStudio CLI
Pipeline: estrazione audio → Whisper → Pillow PNG → ffconcat overlay.
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

if sys.version_info < (3, 10):
    print("Errore: richiesto Python 3.10+", file=sys.stderr)
    sys.exit(1)

from audio_extractor import extract_audio
from subtitle_renderer import render_all
from transcriber import group_into_chunks, transcribe
from video_renderer import burn_subtitles, get_video_duration

app = typer.Typer(name="substudio", add_completion=False, rich_markup_mode="rich")
console = Console(stderr=True)
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def process_video(input_path, output_path, model_size, compute_type, language, keep_temp, use_hw):
    console.print(Rule(f"[bold cyan]{input_path.name}[/]"))
    if not input_path.exists():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if output_path is None:
        output_path = input_path.with_stem(input_path.stem + "_subtitled")

    tmp_dir = Path(tempfile.mkdtemp(prefix="substudio_"))
    wav_path = tmp_dir / "audio.wav"

    try:
        # 1. Estrazione audio
        extract_audio(input_path, wav_path)

        # 2. Durata video
        duration = get_video_duration(input_path)
        console.log(f"[dim]Durata video: {duration:.2f}s[/]")

        # 3. Trascrizione
        words = transcribe(wav_path, model_size, compute_type, language)
        if not words:
            console.print("[yellow]⚠ Nessuna parola rilevata. Skip.[/]")
            return output_path

        # 4. Chunking
        chunks = group_into_chunks(words)

        # 5. Rendering PNG + ffconcat (Pillow, nessuna dipendenza libass)
        _, ffconcat_path, wm_path = render_all(chunks, tmp_dir, duration)

        # 6. Burn-in: 2 overlay totali, veloce
        burn_subtitles(
            video_path=input_path,
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=output_path,
            use_hw=use_hw,
        )
    finally:
        if not keep_temp:
            for f in tmp_dir.iterdir():
                try: f.unlink()
                except: pass
            try: tmp_dir.rmdir()
            except: pass
            console.log("[dim]File temporanei rimossi[/]")
        else:
            console.log(f"[dim]File temporanei in: {tmp_dir}[/]")

    console.print(Panel(f"[bold green]✓ Completato![/]\nOutput: [cyan]{output_path}[/]", expand=False))
    return output_path


@app.command()
def run(
    input_path:   Path       = typer.Option(...,     "--input",        "-i"),
    output_path:  Path       = typer.Option(None,    "--output",       "-o"),
    batch:        bool       = typer.Option(False,   "--batch",        "-b"),
    model:        str        = typer.Option("small", "--model",        "-m"),
    compute_type: str        = typer.Option("float16","--compute-type"),
    language:     str        = typer.Option("it",    "--language",     "-l"),
    keep_temp:    bool       = typer.Option(False,   "--keep-temp"),
    hw:           bool|None  = typer.Option(None,    "--hw/--no-hw"),
):
    """🎬 Sub Studio — Pipeline sottotitoli verticali 9:16."""
    console.print(Panel(
        "[bold]🎬 Sub Studio CLI[/] — Podcast Verticale 9:16\n"
        "[dim]Powered by faster-whisper + Pillow + ffmpeg[/]", expand=False))

    if batch:
        if not input_path.is_dir():
            console.print("[red]Errore:[/] --batch richiede una cartella."); raise typer.Exit(1)
        files = [f for f in sorted(input_path.iterdir()) if f.suffix.lower() in VIDEO_EXTENSIONS]
        if not files:
            console.print(f"[yellow]Nessun video in:[/] {input_path}"); raise typer.Exit(0)
        errors = []
        for i, vf in enumerate(files, 1):
            console.print(f"\n[bold]({i}/{len(files)})[/]")
            try:
                process_video(vf, None, model, compute_type, language, keep_temp, hw)
            except Exception as e:
                console.print(f"[red]✗ {vf.name}:[/] {e}"); errors.append(vf)
        if errors: raise typer.Exit(1)
    else:
        if input_path.is_dir():
            console.print("[red]Errore:[/] usa --batch per le cartelle."); raise typer.Exit(1)
        try:
            process_video(input_path, output_path, model, compute_type, language, keep_temp, hw)
        except (FileNotFoundError, RuntimeError) as e:
            console.print(f"[red]Errore:[/] {e}"); raise typer.Exit(1)

if __name__ == "__main__":
    app()
