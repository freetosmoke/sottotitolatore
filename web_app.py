#!/usr/bin/env python3
"""
web_app.py
Interfaccia Web UI per Sottotitolatore Podcast Verticale 9:16
Preset: "La Voce del Successo"
- Supporto per selezione multipla di parole in grassetto nella stessa riga
- Anteprima visiva istantanea e solida (frame video o canvas podcast studio)
- Player sincronizzato e correzione errori
- Render finale Apple Silicon
"""
from __future__ import annotations

import base64
import io
import json
import mimetypes
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
import urllib.parse
import zipfile
from email.parser import BytesParser
from email.policy import default
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from audio_extractor import extract_audio
from keyword_selector import select_keyword
from subtitle_renderer import (
    render_all,
    render_subtitle,
    render_watermark,
    load_pair,
    load_font_variant,
    get_font_typo_metrics,
    SUBTITLE_Y,
    WATERMARK_Y,
    FONT_SIZE_SUB,
    FONT_SIZE_WM,
    WATERMARK_TEXT,
    WIDTH,
    HEIGHT
)
from transcriber import group_into_chunks, transcribe, resegment_subtitles
from video_renderer import burn_subtitles, get_video_duration, get_video_dimensions, _get_bin
from silence_remover import (
    detect_silence_segments,
    calculate_keep_intervals,
    remap_chunks_and_words,
    cut_and_compact_video_audio,
)

try:
    from rich.console import Console
    console = Console(stderr=True)
except Exception:
    import sys
    class _SimpleConsole:
        def log(self, msg, *args, **kwargs):
            sys.stderr.write(f"{msg}\n")
    console = _SimpleConsole()


PORT = int(os.environ.get("SOTTOTITOLATORE_PORT", 8501))
WORKSPACE = Path(__file__).resolve().parent
DATA_DIR_ENV = os.environ.get("SOTTOTITOLATORE_DATA_DIR")
DATA_DIR = Path(DATA_DIR_ENV) if DATA_DIR_ENV else WORKSPACE
UPLOADS_DIR = DATA_DIR / "web_uploads"
OUTPUTS_DIR = DATA_DIR / "web_outputs"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Assicura priorità ai binari standalone (ffmpeg Apple Silicon)
_candidate_bins = [
    WORKSPACE.parent / "bin",          # Resources/bin nel bundle .app
    WORKSPACE / "bin",                 # bin locale nel workspace
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
]
for _b in _candidate_bins:
    if _b.exists():
        _b_str = str(_b)
        if _b_str not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{_b_str}:{os.environ.get('PATH', '')}"

SYSTEM_PRESET_IDS = {"voce_del_successo"}

def normalize_preset(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizza qualsiasi dizionario preset nel modello unificato TextPreset.
    Calcola in modo deterministico sia le proprietà logiche CapCut che i campi derivati per il rendering.
    """
    def _to_num(v, default=0, is_float=False):
        try:
            return float(v) if is_float else int(round(float(v)))
        except (ValueError, TypeError):
            return default

    p_id = str(raw.get("id", "")).strip()
    if p_id == "la_voce_del_successo_new":
        p_id = "voce_del_successo"
    p_name = str(raw.get("name", "")).strip() or "Preset senza nome"
    is_sys = bool(raw.get("is_system", False)) or (p_id in SYSTEM_PRESET_IDS)

    # Parametri logici del sottotitolo
    capcut_size = _to_num(raw.get("capcut_size", 10), 10, is_float=True)
    capcut_sub_scale = _to_num(raw.get("capcut_sub_scale", 100), 100, is_float=True)
    capcut_x = _to_num(raw.get("capcut_x", 0), 0)
    capcut_y = _to_num(raw.get("capcut_y", 0), 0)
    rotation_sub = _to_num(raw.get("rotation_sub", 0), 0, is_float=True)
    all_caps = bool(raw.get("all_caps", False))
    letter_spacing = _to_num(raw.get("letter_spacing", 0), 0)

    # Layout sottotitoli
    raw_layout = raw.get("subtitle_layout")
    if not isinstance(raw_layout, dict):
        raw_layout = {}

    min_words_per_line = max(
        1, _to_num(raw_layout.get("min_words_per_line", 2), 2)
    )
    max_words_per_line = max(
        min_words_per_line, _to_num(raw_layout.get("max_words_per_line", 7), 7)
    )
    num_lines = max(
        1, _to_num(raw_layout.get("num_lines", 2), 2)
    )

    subtitle_layout = {
        "min_words_per_line": min_words_per_line,
        "max_words_per_line": max_words_per_line,
        "num_lines": num_lines,
    }

    # Parametri logici del watermark
    watermark_text = str(raw.get("watermark_text", "")).strip()
    capcut_wm_size = _to_num(raw.get("capcut_wm_size", 5), 5, is_float=True)
    capcut_wm_scale = _to_num(raw.get("capcut_wm_scale", 100), 100, is_float=True)
    capcut_wm_x = _to_num(raw.get("capcut_wm_x", 0), 0)
    capcut_wm_y = _to_num(raw.get("capcut_wm_y", -207), -207)
    rotation_wm = _to_num(raw.get("rotation_wm", 0), 0, is_float=True)

    stroke_width = _to_num(raw.get("stroke_width", 0), 0)
    shadow_offset = _to_num(raw.get("shadow_offset", 0), 0)

    font = str(raw.get("font_name") or raw.get("font_family") or "Raleway").strip()
    pattern = str(raw.get("pattern", "Light")).strip()

    # Nuovo sistema di stile Normal / Keyword.
    # Se assente, mantiene esattamente il comportamento precedente.
    raw_subtitle_style = raw.get("subtitle_style")
    if not isinstance(raw_subtitle_style, dict):
        raw_subtitle_style = {}

    raw_normal_style = raw_subtitle_style.get("normal")
    if not isinstance(raw_normal_style, dict):
        raw_normal_style = {}

    raw_keyword_style = raw_subtitle_style.get("keyword")
    if not isinstance(raw_keyword_style, dict):
        raw_keyword_style = {}

    subtitle_style = {
        "normal": {
            "font_family": str(
                raw_normal_style.get("font_family") or font
            ).strip(),
            "font_variant": str(
                raw_normal_style.get("font_variant") or "Light"
            ).strip(),
            "color": str(
                raw_normal_style.get("color") or "#FFFFFF"
            ).strip(),
        },
        "keyword": {
            "font_family": str(
                raw_keyword_style.get("font_family") or font
            ).strip(),
            "font_variant": str(
                raw_keyword_style.get("font_variant") or "SemiBold"
            ).strip(),
            "color": str(
                raw_keyword_style.get("color") or "#FFFFFF"
            ).strip(),
        },
    }

    raw_keywords = raw.get("keywords")
    if not isinstance(raw_keywords, dict):
        raw_keywords = {}

    _kw_mode_raw = str(raw_keywords.get("mode") or "automatic").strip().lower()
    # Valida mode: solo valori ammessi
    if _kw_mode_raw not in {"automatic", "manual", "off"}:
        _kw_mode_raw = "automatic"

    # Evita il bug bool("false") == True: normalizza enabled da stringa se necessario
    _kw_enabled_raw = raw_keywords.get("enabled", True)
    if isinstance(_kw_enabled_raw, str):
        _kw_enabled_raw = _kw_enabled_raw.strip().lower() not in {"false", "0", "no", "off"}
    else:
        _kw_enabled_raw = bool(_kw_enabled_raw)

    keywords = {
        "enabled": _kw_enabled_raw,
        "mode": _kw_mode_raw,
    }

    # Campi derivati per rendering e retrocompatibilità
    eff_sub = capcut_size * (capcut_sub_scale / 100.0)
    font_size_sub = _to_num(raw.get("font_size_sub", round(eff_sub * 5.35)), round(eff_sub * 5.35))
    offset_sub_x = round(capcut_x * 0.50)
    offset_sub_y = -round(capcut_y * 0.50)
    subtitle_y = SUBTITLE_Y + offset_sub_y

    eff_wm = capcut_wm_size * (capcut_wm_scale / 100.0)
    font_size_wm = _to_num(raw.get("font_size_wm", round(eff_wm * 5.35)), round(eff_wm * 5.35))
    offset_wm_x = round(capcut_wm_x * 0.50)
    offset_wm_y = -round(capcut_wm_y * 0.50)
    watermark_y = SUBTITLE_Y + offset_wm_y

    return {
        "id": p_id,
        "name": p_name,
        "description": str(raw.get("description", "")),
        "is_system": is_sys,
        "is_default": bool(raw.get("is_default", False)),
        "font_family": font,
        "font_name": font,
        "pattern": pattern,
        "subtitle_style": subtitle_style,
        "keywords": keywords,
        "subtitle_layout": subtitle_layout,
        "all_caps": all_caps,
        "letter_spacing": letter_spacing,
        "capcut_size": capcut_size,
        "capcut_sub_scale": capcut_sub_scale,
        "capcut_x": capcut_x,
        "capcut_y": capcut_y,
        "rotation_sub": rotation_sub,
        "watermark_text": watermark_text,
        "capcut_wm_size": capcut_wm_size,
        "capcut_wm_scale": capcut_wm_scale,
        "capcut_wm_x": capcut_wm_x,
        "capcut_wm_y": capcut_wm_y,
        "rotation_wm": rotation_wm,
        "stroke_width": stroke_width,
        "shadow_offset": shadow_offset,
        # Derived fields
        "offset_sub_x": offset_sub_x,
        "offset_sub_y": offset_sub_y,
        "offset_wm_x": offset_wm_x,
        "offset_wm_y": offset_wm_y,
        "subtitle_y": subtitle_y,
        "watermark_y": watermark_y,
        "font_size_sub": font_size_sub,
        "font_size_wm": font_size_wm,
    }

DEFAULT_PRESET = normalize_preset({
    "id": "voce_del_successo",
    "name": "La Voce del Successo New",
    "description": "Preset ufficiale predefinito con font Raleway, Dimensione 8 (Ridim. 105%), Posizione Y: 0, Watermark Raleway Grassetto Dim. 5 (Ridim. 114%), Posizione Y: -197",
    "is_system": True,
    "is_default": True,
    "font_family": "Raleway",
    "font_name": "Raleway",
    "pattern": "Normal",
    "all_caps": False,
    "letter_spacing": 0,
    "capcut_size": 8.0,
    "capcut_sub_scale": 105.0,
    "capcut_x": 0,
    "capcut_y": 0,
    "rotation_sub": 0.0,
    "watermark_text": "@lavocedelsuccesso",
    "capcut_wm_size": 5.0,
    "capcut_wm_scale": 114.0,
    "capcut_wm_x": 0,
    "capcut_wm_y": -197,
    "rotation_wm": 0.0,
    "stroke_width": 0,
    "shadow_offset": 0,
    "offset_sub_x": 0,
    "offset_sub_y": 0,
    "offset_wm_x": 0,
    "offset_wm_y": 98,
    "subtitle_y": 960,
    "watermark_y": 1058,
    "font_size_sub": 45,
    "font_size_wm": 30
})

DEFAULT_PRESETS = [
    DEFAULT_PRESET
]

PRESETS_FILE = DATA_DIR / "presets.json"

def load_presets() -> list[dict[str, Any]]:
    """Carica i preset garantendo la presenza e immutabilità dei preset di sistema."""
    disk_presets = []
    if PRESETS_FILE.exists():
        try:
            raw_data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw_data, list):
                disk_presets = [normalize_preset(p) for p in raw_data if isinstance(p, dict)]
        except Exception as e:
            console.log(f"[yellow]Attenzione lettura presets.json: {e}[/]")

    # Se vuoto, tenta dal template workspace o usa i default
    if not disk_presets:
        factory_file = WORKSPACE / "presets.json"
        if factory_file.exists() and factory_file != PRESETS_FILE:
            try:
                raw_data = json.loads(factory_file.read_text(encoding="utf-8"))
                if isinstance(raw_data, list):
                    disk_presets = [normalize_preset(p) for p in raw_data if isinstance(p, dict)]
            except Exception:
                pass
        if not disk_presets:
            disk_presets = list(DEFAULT_PRESETS)

    # Assicura la presenza e l'esatta definizione dei preset di sistema
    system_map = {p["id"]: p for p in DEFAULT_PRESETS}
    final_presets: list[dict[str, Any]] = []

    # 1. Preset di sistema realmente definiti
    for sys_id in SYSTEM_PRESET_IDS:
        if sys_id in system_map:
            final_presets.append(dict(system_map[sys_id]))

    # 2. Preset utente salvati (esclusi quelli che collidono con id di sistema)
    for p in disk_presets:
        if p.get("id") not in SYSTEM_PRESET_IDS:
            p["is_system"] = False
            final_presets.append(p)

    return final_presets

def save_presets(presets: list[dict[str, Any]]):
    try:
        # Assicura che i preset di sistema siano sempre inclusi in cima al file salvato
        sys_ids_present = {p["id"] for p in presets if p.get("id") in SYSTEM_PRESET_IDS}
        system_map = {p["id"]: p for p in DEFAULT_PRESETS}
        full_list: list[dict[str, Any]] = []
        for sys_id in SYSTEM_PRESET_IDS:
            if sys_id in system_map:
                full_list.append(dict(system_map[sys_id]))
        for p in presets:
            if p.get("id") not in SYSTEM_PRESET_IDS:
                full_list.append(normalize_preset(p))

        PRESETS_FILE.write_text(json.dumps(full_list, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        console.log(f"[red]Errore salvataggio presets.json: {e}[/]")

def extract_video_frame(video_path: Path, timestamp: float, output_png: Path) -> bool:
    """Tenta l'estrazione di un fotogramma esatto dal video a 1080x1920 via ffmpeg."""
    try:
        cmd = [
            _get_bin("ffmpeg"), "-y",
            "-ss", f"{timestamp:.3f}",
            "-i", str(video_path.resolve()),
            "-vframes", "1",
            "-s", f"{WIDTH}x{HEIGHT}",
            str(output_png.resolve())
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        return res.returncode == 0 and output_png.exists() and output_png.stat().st_size > 0
    except Exception:
        return False

def get_unique_upload_path(filename: str) -> Path:
    """Genera un percorso univoco sicuro in UPLOADS_DIR per evitare sovrascritture in upload batch."""
    base_name = Path(filename).name if filename else "video.mp4"
    safe = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base_name)
    if not safe or safe.startswith("."):
        safe = "video.mp4"
    stem = Path(safe).stem
    suffix = Path(safe).suffix or ".mp4"
    candidate = UPLOADS_DIR / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = UPLOADS_DIR / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate

def extract_waveform_peaks(video_path: Path, num_peaks: int = 1200) -> dict[str, Any]:
    """
    Estrae rapidamente i picchi audio (0.0 - 1.0) dal video usando ffmpeg.
    Ritorna durata e array di picchi compatti per la visualizzazione nella timeline.
    """
    duration = get_video_duration(video_path)
    cmd = [
        _get_bin("ffmpeg"), "-y", "-i", str(video_path.resolve()),
        "-vn", "-ac", "1", "-ar", "4000",
        "-f", "s16le", "-"
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
        raw = proc.stdout
        if not raw:
            return {"success": True, "duration": duration, "peaks": [0.0] * 100}

        sample_count = len(raw) // 2
        samples = struct.unpack(f"<{sample_count}h", raw)
        step = max(1, sample_count // num_peaks)
        peaks = []
        for i in range(0, sample_count, step):
            chunk = samples[i:i + step]
            if chunk:
                max_val = max(abs(s) for s in chunk)
                peaks.append(round(max_val / 32768.0, 3))

        return {
            "success": True,
            "duration": duration,
            "peaks": peaks
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Errore estrazione waveform: {str(exc)}",
            "duration": duration,
            "peaks": []
        }

class AppRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        try:
            super().log_message(format, *args)
        except Exception:
            pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400):
        self.send_json({"error": message, "success": False}, status=status)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html_file = WORKSPACE / "web_static" / "index.html"
            if html_file.exists():
                content = html_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error_json("Interfaccia non trovata", 404)
                return

        if path == "/api/presets":
            presets = load_presets()
            self.send_json({"presets": presets, "default_id": "voce_del_successo", "success": True})
            return

        if path == "/api/font_metrics":
            qs = urllib.parse.parse_qs(parsed.query)
            font_name = qs.get("font", ["Raleway"])[0]
            try:
                font_size = int(qs.get("size", [45])[0])
            except ValueError:
                font_size = 45
            metrics = get_font_typo_metrics(font_name=font_name, font_size=font_size)
            self.send_json(metrics)
            return

        if path == "/api/preset":
            presets = load_presets()
            self.send_json({"preset": presets[0] if presets else DEFAULT_PRESET, "success": True})
            return

        if path == "/api/default_video":
            default_vid = UPLOADS_DIR / "uploaded_video.mp4"
            if not default_vid.exists():
                alt_vid = WORKSPACE / "web_uploads" / "uploaded_video.mp4"
                if alt_vid.exists():
                    default_vid = alt_vid
            if default_vid.exists():
                try:
                    dur = get_video_duration(default_vid)
                except Exception:
                    dur = 60.0
                self.send_json({
                    "success": True,
                    "server_path": str(default_vid.resolve()),
                    "video_url": f"/media/{default_vid.name}",
                    "filename": default_vid.name,
                    "duration": dur
                })
            else:
                self.send_error_json("Nessun video di default disponibile", 404)
            return

        if path.startswith("/fonts/"):
            font_filename = urllib.parse.unquote(path[len("/fonts/"):])
            target = (WORKSPACE / "fonts" / font_filename).resolve()
            if not target.exists():
                target = (Path(__file__).parent / "fonts" / font_filename).resolve()
            if target.exists() and target.is_file():
                content = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "font/ttf")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error_json("Font file not found", 404)
                return

        if path.startswith("/vendor/"):
            rel_path = urllib.parse.unquote(path[len("/vendor/"):])
            vendor_dir = (WORKSPACE / "web_static" / "vendor").resolve()
            target = (vendor_dir / rel_path).resolve()
            try:
                is_safe = target.is_relative_to(vendor_dir)
            except AttributeError:
                is_safe = str(target).startswith(str(vendor_dir))
            if is_safe and target.exists() and target.is_file():
                content = target.read_bytes()
                mime, _ = mimetypes.guess_type(str(target))
                mime = mime or "application/javascript"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error_json("Vendor file not found", 404)
                return

        if path.startswith("/media/"):
            filename = urllib.parse.unquote(path[len("/media/"):])
            target = (UPLOADS_DIR / filename).resolve()
            if not target.exists():
                target = (OUTPUTS_DIR / filename).resolve()

            if target.exists() and target.is_file():
                mime, _ = mimetypes.guess_type(str(target))
                mime = mime or "application/octet-stream"
                size = target.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(target, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
                return
            else:
                self.send_error_json("Media file not found", 404)
                return

        self.send_error_json("Not found", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/upload":
            content_type = self.headers.get("content-type", "")
            if "multipart/form-data" not in content_type:
                self.send_error_json("Richiesta non valida: multipart/form-data atteso")
                return

            content_len = int(self.headers.get("content-length", 0))
            if content_len <= 0:
                self.send_error_json("Contenuto vuoto o Content-Length mancante")
                return

            post_data = self.rfile.read(content_len)
            raw_msg = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + post_data

            uploaded_files = []
            try:
                msg = BytesParser(policy=default).parsebytes(raw_msg)
                for part in msg.iter_parts():
                    file_bytes = part.get_payload(decode=True)
                    if file_bytes:
                        raw_filename = part.get_filename() or "uploaded_video.mp4"
                        dest_file = get_unique_upload_path(raw_filename)
                        dest_file.write_bytes(file_bytes)
                        try:
                            duration = get_video_duration(dest_file)
                        except Exception:
                            duration = 0.0
                        uploaded_files.append({
                            "filename": dest_file.name,
                            "original_name": raw_filename,
                            "video_url": f"/media/{dest_file.name}",
                            "duration": duration,
                            "server_path": str(dest_file)
                        })
            except Exception as exc:
                self.send_error_json(f"Errore analisi upload: {str(exc)}", 500)
                return

            if not uploaded_files:
                self.send_error_json("Nessun video valido caricato")
                return

            first = uploaded_files[0]
            self.send_json({
                "success": True,
                "filename": first["filename"],
                "original_name": first["original_name"],
                "video_url": first["video_url"],
                "duration": first["duration"],
                "server_path": first["server_path"],
                "files": uploaded_files
            })
            return

        content_len = int(self.headers.get("content-length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(post_data.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/transcribe":
            video_path_str = payload.get("video_path")
            model_size = payload.get("model", "small")
            language = payload.get("language", "it")
            translate_to_it = bool(payload.get("translate_to_it", False))
            if language == "it":
                translate_to_it = False
            translation_engine = payload.get("translation_engine", "auto")
            gemini_api_key = payload.get("gemini_api_key")

            # Modalità keyword.
            # Default = automatic per mantenere il comportamento precedente.
            keywords_config = payload.get("keywords") or {}
            keyword_mode = str(
                keywords_config.get("mode") or "automatic"
            ).strip().lower()

            if keyword_mode not in {"automatic", "manual", "off"}:
                keyword_mode = "automatic"

            if not video_path_str:
                self.send_error_json("Manca video_path")
                return

            video_path = Path(video_path_str)
            if not video_path.exists():
                self.send_error_json("File video non trovato")
                return

            with tempfile.TemporaryDirectory(prefix="st_web_") as tmp_dir:
                tmp_p = Path(tmp_dir)
                wav_path = tmp_p / "audio.wav"
                try:
                    extract_audio(video_path, wav_path)
                    words = transcribe(
                        wav_path,
                        model_size=model_size,
                        compute_type="int8",
                        language=language,
                        translate_to_it=translate_to_it,
                        translation_engine=translation_engine,
                        api_key=gemini_api_key,
                    )
                    chunks = group_into_chunks(words)
                except Exception as e:
                    self.send_error_json(f"Errore trascrizione: {str(e)}", 500)
                    return

            chunks_data = []
            for i, c in enumerate(chunks):
                w_list = [w.word for w in c.words]

                if keyword_mode == "automatic":
                    kw_idx = select_keyword(w_list)
                else:
                    kw_idx = None

                chunks_data.append({
                    "id": i,
                    "start": round(c.start, 2),
                    "end": round(c.end, 2),
                    "words": [{"word": w, "start": round(token.start, 2), "end": round(token.end, 2)} for w, token in zip(w_list, c.words)],
                    "bold_indices": [kw_idx] if (kw_idx is not None and kw_idx >= 0) else [],
                    "text": c.text,
                })

            self.send_json({
                "success": True,
                "chunks": chunks_data,
                "count": len(chunks_data)
            })
            return

        if path == "/api/translate_chunks":
            chunks_data = payload.get("chunks", [])
            engine = payload.get("translation_engine", "auto")
            gemini_api_key = payload.get("gemini_api_key")

            if not chunks_data:
                self.send_error_json("Nessun sottotitolo fornito per la traduzione")
                return

            try:
                from translator import translate_chunks_data
                translated_chunks = translate_chunks_data(chunks_data, engine=engine, api_key=gemini_api_key)
                self.send_json({
                    "success": True,
                    "chunks": translated_chunks,
                    "count": len(translated_chunks)
                })
            except Exception as exc:
                self.send_error_json(f"Errore traduzione sottotitoli: {str(exc)}", 500)
            return

        if path == "/api/preview_chunk":
            try:
                video_path_str = payload.get("video_path")
                timestamp = float(payload.get("timestamp", 0.0))
                words = payload.get("words", [])
                bold_indices = payload.get("bold_indices", [])
                if "capcut_size" in payload and payload["capcut_size"]:
                    sub_scale = float(payload.get("capcut_sub_scale", 100)) / 100.0
                    fs_sub = round(float(payload["capcut_size"]) * sub_scale * 5.35)
                else:
                    fs_sub = int(payload.get("font_size_sub", FONT_SIZE_SUB))

                wm_text = payload.get("watermark_text", WATERMARK_TEXT)
                if "capcut_wm_size" in payload and payload["capcut_wm_size"]:
                    wm_scale = float(payload.get("capcut_wm_scale", 100)) / 100.0
                    fs_wm = round(float(payload["capcut_wm_size"]) * wm_scale * 5.35)
                else:
                    fs_wm = int(payload.get("font_size_wm", FONT_SIZE_WM))

                if "capcut_sub_x" in payload and payload["capcut_sub_x"] is not None:
                    sub_ox = round(float(payload["capcut_sub_x"]) * 0.50)
                elif "capcut_x" in payload and payload["capcut_x"] is not None:
                    sub_ox = round(float(payload["capcut_x"]) * 0.50)
                else:
                    sub_ox = int(payload.get("offset_sub_x", 0))

                if "capcut_sub_y" in payload and payload["capcut_sub_y"] is not None:
                    sub_oy = -round(float(payload["capcut_sub_y"]) * 0.50)
                elif "capcut_y" in payload and payload["capcut_y"] is not None:
                    sub_oy = -round(float(payload["capcut_y"]) * 0.50)
                elif "offset_sub_y" in payload:
                    sub_oy = int(payload["offset_sub_y"])
                else:
                    sub_oy = int(payload.get("subtitle_y", SUBTITLE_Y)) - 960

                if "capcut_wm_x" in payload and payload["capcut_wm_x"] is not None:
                    wm_ox = round(float(payload["capcut_wm_x"]) * 0.50)
                else:
                    wm_ox = int(payload.get("offset_wm_x", 0))

                if "capcut_wm_y" in payload and payload["capcut_wm_y"] is not None:
                    wm_oy = -round(float(payload["capcut_wm_y"]) * 0.50)
                elif "offset_wm_y" in payload:
                    wm_oy = int(payload["offset_wm_y"])
                else:
                    wm_oy = int(payload.get("watermark_y", WATERMARK_Y)) - 960

                rot_sub = float(payload.get("rotation_sub", 0.0))
                rot_wm = float(payload.get("rotation_wm", 0.0))

                stroke_w = int(payload.get("stroke_width", 0))
                shadow_off = int(payload.get("shadow_offset", 0))
                all_caps = bool(payload.get("all_caps", False))
                letter_spacing = int(payload.get("letter_spacing", 0))

                subtitle_layout = payload.get("subtitle_layout") or {}
                min_words_per_line = max(
                    1, int(subtitle_layout.get("min_words_per_line", 2))
                )
                max_words_per_line = max(
                    min_words_per_line,
                    int(subtitle_layout.get("max_words_per_line", 7))
                )
                num_lines = max(
                    1, int(subtitle_layout.get("num_lines", 2))
                )

                font_name = payload.get("font_name") or payload.get("font_family") or "Raleway"
                pattern = payload.get("pattern", "")

                # Nuovo sistema di stile Normal / Keyword.
                # Mantiene il vecchio comportamento se subtitle_style non è presente.
                subtitle_style = payload.get("subtitle_style") or {}

                normal_style = subtitle_style.get("normal") or {}
                keyword_style = subtitle_style.get("keyword") or {}

                normal_family = normal_style.get("font_family") or font_name
                normal_variant = normal_style.get("font_variant") or "Light"

                keyword_family = keyword_style.get("font_family") or font_name
                keyword_variant = keyword_style.get("font_variant") or "SemiBold"

                def _preview_parse_color(value, fallback=(255, 255, 255, 255)):
                    if isinstance(value, (list, tuple)) and len(value) in (3, 4):
                        try:
                            vals = tuple(int(x) for x in value)
                            return vals if len(vals) == 4 else vals + (255,)
                        except (TypeError, ValueError):
                            return fallback

                    if isinstance(value, str):
                        raw_color = value.strip().lstrip("#")
                        if len(raw_color) == 6:
                            try:
                                return (
                                    int(raw_color[0:2], 16),
                                    int(raw_color[2:4], 16),
                                    int(raw_color[4:6], 16),
                                    255,
                                )
                            except ValueError:
                                pass
                        elif len(raw_color) == 8:
                            try:
                                return (
                                    int(raw_color[0:2], 16),
                                    int(raw_color[2:4], 16),
                                    int(raw_color[4:6], 16),
                                    int(raw_color[6:8], 16),
                                )
                            except ValueError:
                                pass

                    return fallback

                normal_color = _preview_parse_color(
                    normal_style.get("color")
                )
                keyword_color = _preview_parse_color(
                    keyword_style.get("color")
                )

                light_sub = load_font_variant(
                    fs_sub,
                    font_name=normal_family,
                    variant=normal_variant,
                )

                semibold_sub = load_font_variant(
                    fs_sub,
                    font_name=keyword_family,
                    variant=keyword_variant,
                )

                # Il watermark resta invariato.
                _, semibold_wm = load_pair(fs_wm, font_name=font_name)

                from PIL import Image

                canvas_w, canvas_h = WIDTH, HEIGHT
                if video_path_str and Path(video_path_str).exists():
                    canvas_w, canvas_h = get_video_dimensions(Path(video_path_str))

                with tempfile.TemporaryDirectory(prefix="preview_") as tmp_d:
                    tmp_dir = Path(tmp_d)
                    frame_png = tmp_dir / "frame.png"
                    sub_png = tmp_dir / "sub.png"
                    wm_png = tmp_dir / "wm.png"

                    has_frame = False
                    if video_path_str and Path(video_path_str).exists():
                        has_frame = extract_video_frame(Path(video_path_str), timestamp, frame_png)

                    render_subtitle(
                        words, bold_indices, light_sub, semibold_sub, sub_png,
                        offset_x=sub_ox, offset_y=sub_oy,
                        stroke_width=stroke_w, shadow_offset=shadow_off,
                        pattern=pattern,
                        all_caps=all_caps,
                        letter_spacing=letter_spacing,
                        rotation=rot_sub,
                        canvas_width=canvas_w,
                        canvas_height=canvas_h,
                        normal_color=normal_color,
                        keyword_color=keyword_color,
                        min_words_per_line=min_words_per_line,
                        max_words_per_line=max_words_per_line,
                        num_lines=num_lines,
                    )
                    render_watermark(
                        semibold_wm, wm_png, watermark_text=wm_text,
                        offset_x=wm_ox, offset_y=wm_oy,
                        stroke_width=stroke_w, shadow_offset=shadow_off,
                        rotation=rot_wm,
                        canvas_width=canvas_w,
                        canvas_height=canvas_h,
                    )

                    if has_frame and frame_png.exists():
                        try:
                            base = Image.open(frame_png).convert("RGBA")
                        except Exception:
                            base = Image.new("RGBA", (canvas_w, canvas_h), (16, 18, 22, 255))
                    else:
                        # Fallback sfondo scuro stile podcast
                        base = Image.new("RGBA", (canvas_w, canvas_h), (16, 18, 22, 255))

                    s_img = Image.open(sub_png)
                    w_img = Image.open(wm_png)
                    base.alpha_composite(s_img)
                    base.alpha_composite(w_img)

                    aspect = canvas_h / max(canvas_w, 1)
                    thumb_w = 360
                    thumb_h = max(10, int(round(thumb_w * aspect)))
                    thumb = base.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    thumb.convert("RGB").save(buf, format="JPEG", quality=88)
                    thumb_bytes = buf.getvalue()

                b64 = base64.b64encode(thumb_bytes).decode("ascii")
                self.send_json({"success": True, "preview_base64": f"data:image/jpeg;base64,{b64}"})
            except Exception as exc:
                self.send_error_json(f"Errore generazione preview: {str(exc)}", 500)
            return

        if path == "/api/render":
            video_path_str = payload.get("video_path")
            chunks_data = payload.get("chunks", [])
            preset = payload.get("preset", DEFAULT_PRESET)
            quality = payload.get("quality", "high")
            black_and_white = bool(payload.get("black_and_white", False))
            custom_output_name = payload.get("output_filename")
            remove_silence = bool(payload.get("remove_silence", False))
            silence_threshold = float(payload.get("silence_threshold", 0.3))

            if not video_path_str or not chunks_data:
                self.send_error_json("Parametri mancanti per il rendering")
                return

            video_path = Path(video_path_str)
            if not video_path.exists():
                self.send_error_json("Video sorgente non trovato")
                return

            if custom_output_name and str(custom_output_name).strip():
                clean_name = Path(str(custom_output_name).strip()).name
                if not clean_name.lower().endswith(".mp4"):
                    clean_name += ".mp4"
                out_name = clean_name
            else:
                out_name = f"subtitled_{video_path.stem}.mp4"
            output_file = OUTPUTS_DIR / out_name

            with tempfile.TemporaryDirectory(prefix="render_job_") as tmp_dir:
                tmp_p = Path(tmp_dir)
                try:
                    duration = get_video_duration(video_path)
                    render_video_source = video_path
                    render_chunks = chunks_data
                    render_duration = duration
                    silence_cut_performed = False

                    if remove_silence:
                        cache_key = str(video_path.resolve())
                        if hasattr(self.server, "_silence_cache") and cache_key in self.server._silence_cache:
                            raw_silences, _ = self.server._silence_cache[cache_key]
                            # Filtra i silenzi con durata >= silence_threshold
                            silences = [(s[0], s[1]) for s in raw_silences if (s[1] - s[0]) >= (silence_threshold - 0.02)]
                        else:
                            silences = detect_silence_segments(video_path, min_silence_duration=silence_threshold)
                        if silences:
                            keeps = calculate_keep_intervals(duration, silences)
                            # Se ci sono tagli effettivi
                            if len(keeps) > 1 or (len(keeps) == 1 and (keeps[0][1] - keeps[0][0]) < (duration - 0.1)):
                                compact_video_file = tmp_p / f"compact_{video_path.name}"
                                _, comp_dur = cut_and_compact_video_audio(
                                    video_path=video_path,
                                    keep_intervals=keeps,
                                    output_path=compact_video_file,
                                    use_hw=True,
                                    quality=quality,
                                )
                                render_video_source = compact_video_file
                                render_duration = comp_dur
                                render_chunks = remap_chunks_and_words(chunks_data, keeps)
                                silence_cut_performed = True

                    canvas_w, canvas_h = get_video_dimensions(render_video_source)

                    # Ri-segmentazione dinamica basata sui parametri layout del preset
                    # Estrae tutte le parole dai chunk (preservando timestamp word-level)
                    all_words = []
                    for chunk in render_chunks:
                        for w in chunk.get("words", []):
                            all_words.append({
                                "word": w.get("word", ""),
                                "start": float(w.get("start", 0.0)),
                                "end": float(w.get("end", 0.0)),
                            })

                    # Legge parametri layout dal preset
                    subtitle_layout = preset.get("subtitle_layout") or {}
                    min_words_per_line = max(1, int(subtitle_layout.get("min_words_per_line", 2)))
                    max_words_per_line = max(min_words_per_line, int(subtitle_layout.get("max_words_per_line", 7)))
                    num_lines = max(1, int(subtitle_layout.get("num_lines", 2)))

                    # Ri-segmentazione: usa le WordToken originali (con modifiche utente preservate)
                    resegmented = resegment_subtitles(
                        all_words,
                        min_words_per_line=min_words_per_line,
                        max_words_per_line=max_words_per_line,
                        num_lines=num_lines,
                    )

                    # Converte SubtitleChunk in formato dict per render_all
                    render_chunks = []
                    for i, chunk in enumerate(resegmented):
                        render_chunks.append({
                            "id": i,
                            "start": round(chunk.start, 2),
                            "end": round(chunk.end, 2),
                            "words": [{"word": w.word, "start": round(w.start, 2), "end": round(w.end, 2)} for w in chunk.words],
                            "bold_indices": [],
                            "text": " ".join(w.word for w in chunk.words),
                        })

                    _, ffconcat_path, wm_path = render_all(
                        chunks=render_chunks,
                        work_dir=tmp_p,
                        total_duration=render_duration,
                        preset=preset,
                        canvas_width=canvas_w,
                        canvas_height=canvas_h,
                    )
                    burn_subtitles(
                        video_path=render_video_source,
                        ffconcat_path=ffconcat_path,
                        watermark_path=wm_path,
                        output_path=output_file,
                        use_hw=True,
                        quality=quality,
                        black_and_white=black_and_white,
                    )
                    actual_final_dur = get_video_duration(output_file)
                except Exception as e:
                    self.send_error_json(f"Errore durante il rendering: {str(e)}", 500)
                    return

            self.send_json({
                "success": True,
                "output_filename": out_name,
                "download_url": f"/media/{out_name}",
                "output_path": str(output_file),
                "final_duration": actual_final_dur,
                "silence_cut_performed": silence_cut_performed,
            })
            return

        if path == "/api/rename_output":
            old_name = payload.get("old_filename")
            new_name = payload.get("new_filename")
            if not old_name or not new_name:
                self.send_error_json("Parametri mancanti per la rinomina")
                return

            clean_new = Path(str(new_name).strip()).name
            if not clean_new.lower().endswith(".mp4"):
                clean_new += ".mp4"

            old_file = OUTPUTS_DIR / Path(str(old_name).strip()).name
            new_file = OUTPUTS_DIR / clean_new

            if not old_file.exists():
                self.send_error_json("File originale non trovato", 404)
                return

            try:
                old_file.rename(new_file)
                self.send_json({
                    "success": True,
                    "new_filename": clean_new,
                    "download_url": f"/media/{clean_new}",
                    "output_path": str(new_file)
                })
            except Exception as e:
                self.send_error_json(f"Errore rinomina file: {str(e)}", 500)
            return

        if path == "/api/waveform":
            video_path_str = payload.get("video_path")
            if not video_path_str:
                self.send_error_json("Manca video_path")
                return

            video_path = Path(video_path_str)
            if not video_path.exists():
                self.send_error_json("File video non trovato")
                return

            num_peaks = int(payload.get("num_peaks", 1200))
            result = extract_waveform_peaks(video_path, num_peaks=num_peaks)
            self.send_json(result)
            return

        if path == "/api/analyze_silences":
            video_path_str = payload.get("video_path")
            if not video_path_str:
                self.send_error_json("Manca video_path")
                return

            video_path = Path(video_path_str)
            if not video_path.exists():
                self.send_error_json("File video non trovato")
                return

            cache_key = str(video_path.resolve())
            if not hasattr(self.server, "_silence_cache"):
                self.server._silence_cache = {}

            if cache_key in self.server._silence_cache:
                raw_silences, total_dur = self.server._silence_cache[cache_key]
            else:
                try:
                    total_dur = get_video_duration(video_path)
                    # Analizza con soglia minima (0.08s) per catturare tutti i silenzi >= 0.1s una volta sola
                    raw_silences = detect_silence_segments(video_path, min_silence_duration=0.08, noise_threshold_db=-30.0)
                    self.server._silence_cache[cache_key] = (raw_silences, total_dur)
                except Exception as e:
                    self.send_error_json(f"Errore analisi silenzi: {str(e)}", 500)
                    return

            self.send_json({
                "success": True,
                "total_duration": total_dur,
                "silences": [{"start": s[0], "end": s[1], "duration": round(s[1] - s[0], 3)} for s in raw_silences]
            })
            return

        if path == "/api/batch_zip":
            file_names = payload.get("files", [])
            if not file_names:
                self.send_error_json("Nessun file fornito per l'archivio ZIP")
                return

            zip_filename = f"sottotitolati_batch_{int(time.time())}.zip"
            zip_path = OUTPUTS_DIR / zip_filename

            added = 0
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fn in file_names:
                    fpath = OUTPUTS_DIR / Path(fn).name
                    if not fpath.exists():
                        fpath = Path(fn)
                    if fpath.exists() and fpath.is_file():
                        zf.write(fpath, arcname=fpath.name)
                        added += 1

            if added == 0:
                self.send_error_json("Nessun file video trovato da comprimere nello ZIP", 404)
                return

            self.send_json({
                "success": True,
                "zip_filename": zip_filename,
                "download_url": f"/media/{zip_filename}",
                "count": added
            })
            return

        if path == "/api/duplicate_preset":
            source_id = payload.get("source_id") or payload.get("id")
            new_name = payload.get("name", "").strip()
            if not source_id:
                self.send_error_json("ID preset sorgente mancante")
                return
            presets = load_presets()
            src = next((p for p in presets if p.get("id") == source_id), None)
            if not src:
                self.send_error_json("Preset sorgente non trovato", 404)
                return

            if not new_name:
                new_name = f"{src.get('name', 'Preset')} (Copia)"

            slug = re.sub(r"[^a-zA-Z0-9_]+", "_", new_name.lower()).strip("_")
            new_id = f"preset_{slug}_{int(time.time())}" if slug else f"preset_{int(time.time())}"

            cloned_raw = dict(src)
            cloned_raw["id"] = new_id
            cloned_raw["name"] = new_name
            cloned_raw["is_system"] = False
            cloned_raw["is_default"] = False
            cloned_raw["description"] = f"Copia duplicata di {src.get('name')}"

            normalized = normalize_preset(cloned_raw)
            presets.append(normalized)
            save_presets([p for p in presets if p.get("id") not in SYSTEM_PRESET_IDS])

            self.send_json({
                "success": True,
                "preset": normalized,
                "presets": presets
            })
            return

        if path == "/api/presets":
            if isinstance(payload, dict) and "preset" in payload and isinstance(payload.get("preset"), dict):
                preset_data = payload["preset"]
            elif isinstance(payload, dict):
                preset_data = payload
            else:
                preset_data = None

            if not preset_data or not isinstance(preset_data, dict):
                self.send_error_json("Dati del preset non validi")
                return

            p_name = str(preset_data.get("name", "")).strip()
            if not p_name:
                self.send_error_json("Il nome del preset è obbligatorio")
                return

            p_id = str(preset_data.get("id", "")).strip()
            is_new = not p_id or p_id == "new"

            # Se è una modifica diretta di un preset di sistema, rifiuta per proteggerlo
            if not is_new and p_id in SYSTEM_PRESET_IDS:
                self.send_error_json(f"I preset di sistema non possono essere modificati direttamente. Usa 'Duplica' per creare una copia personalizzata.", 403)
                return

            if is_new:
                slug = re.sub(r"[^a-zA-Z0-9_]+", "_", p_name.lower()).strip("_")
                p_id = f"preset_{slug}_{int(time.time())}" if slug else f"preset_{int(time.time())}"
                preset_data["id"] = p_id
                preset_data["is_system"] = False
                preset_data["is_default"] = False

            preset_data["name"] = p_name
            normalized = normalize_preset(preset_data)

            presets = load_presets()
            updated = False
            for idx, p in enumerate(presets):
                if p.get("id") == p_id:
                    normalized["is_default"] = p.get("is_default", False)
                    if not normalized.get("description"):
                        normalized["description"] = p.get("description", f"Preset {p_name}")
                    presets[idx] = normalized
                    updated = True
                    break

            if not updated:
                normalized["is_default"] = False
                if not normalized.get("description"):
                    normalized["description"] = f"Preset personalizzato {p_name}"
                presets.append(normalized)

            # Salva solo i preset utente su disco (i preset di sistema sono costanti in codice)
            user_presets = [p for p in presets if p.get("id") not in SYSTEM_PRESET_IDS]
            save_presets(user_presets)

            self.send_json({
                "success": True,
                "preset": normalized,
                "presets": presets
            })
            return

        if path == "/api/delete_preset":
            p_id = payload.get("id")
            if not p_id:
                self.send_error_json("ID preset mancante")
                return

            if p_id in SYSTEM_PRESET_IDS:
                self.send_error_json(f"I preset di sistema non possono essere eliminati", 403)
                return

            presets = load_presets()
            new_presets = [p for p in presets if p.get("id") != p_id]
            if len(new_presets) == len(presets):
                self.send_error_json("Preset non trovato", 404)
                return

            user_presets = [p for p in new_presets if p.get("id") not in SYSTEM_PRESET_IDS]
            save_presets(user_presets)
            self.send_json({"success": True, "presets": new_presets})
            return

        self.send_error_json("Endpoint non valido", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/presets":
            qs = urllib.parse.parse_qs(parsed.query)
            p_id = qs.get("id", [""])[0]
            if not p_id:
                self.send_error_json("ID preset mancante")
                return
            if p_id in SYSTEM_PRESET_IDS:
                self.send_error_json(f"I preset di sistema non possono essere eliminati", 403)
                return
            presets = load_presets()
            new_presets = [p for p in presets if p.get("id") != p_id]
            user_presets = [p for p in new_presets if p.get("id") not in SYSTEM_PRESET_IDS]
            save_presets(user_presets)
            self.send_json({"success": True, "presets": new_presets})
            return
        self.send_error_json("Endpoint non valido", 404)

def run_server():
    server_address = ("127.0.0.1", PORT)
    httpd = ThreadingHTTPServer(server_address, AppRequestHandler)
    httpd.daemon_threads = True
    print(f"\n🚀 Sottotitolatore Web UI avviato con successo!")
    print(f"👉 Apri nel tuo browser: http://localhost:{PORT}")
    print("Premi Ctrl+C per arrestare il server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer arrestato.")

if __name__ == "__main__":
    run_server()
