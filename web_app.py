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
import cgi
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
    SUBTITLE_Y,
    WATERMARK_Y,
    FONT_SIZE_SUB,
    FONT_SIZE_WM,
    WATERMARK_TEXT,
    WIDTH,
    HEIGHT
)
from transcriber import group_into_chunks, transcribe
from video_renderer import burn_subtitles, get_video_duration

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

DEFAULT_PRESET = {
    "id": "voce_del_successo",
    "name": "La Voce del Successo",
    "description": "Preset ufficiale con font Raleway Light, Dimensione 8 (Ridim. 105%), Posizione Y: 0, Watermark Raleway SemiBold Dim. 5 (Ridim. 114%), Posizione Y: -207",
    "is_default": True,
    "capcut_size": 8,
    "capcut_sub_scale": 105,
    "capcut_x": 0,
    "capcut_y": 0,
    "capcut_wm_size": 5,
    "capcut_wm_scale": 114,
    "capcut_wm_x": 0,
    "capcut_wm_y": -207,
    "offset_sub_x": 0,
    "offset_sub_y": 0,              # Centro esatto 960px
    "offset_wm_x": 0,
    "offset_wm_y": 207,            # Y: -207 CapCut -> offset_y = +207 (1167px)
    "subtitle_y": SUBTITLE_Y,       # 960
    "watermark_y": 1167,            # 960 + 207
    "font_size_sub": 46,            # 8 * 1.05 * 5.5 = 46
    "font_size_wm": 31,             # 5 * 1.14 * 5.5 = 31
    "watermark_text": "@lavocedelsuccesso",
    "stroke_width": 0,
    "shadow_offset": 0,
    "font_family": "Raleway",
    "font_name": "Raleway",
    "pattern": "Light",
    "all_caps": False,
    "letter_spacing": 0,
}

DEFAULT_PRESETS = [
    DEFAULT_PRESET,
    {
        "id": "mc",
        "name": "MC",
        "description": "Preset con font Alata Bold, Dimensione 10, Posizione Y: -418, senza watermark",
        "is_default": False,
        "capcut_size": 10,
        "capcut_sub_scale": 100,
        "capcut_x": 0,
        "capcut_y": -418,
        "capcut_wm_size": 0,
        "capcut_wm_scale": 100,
        "capcut_wm_x": 0,
        "capcut_wm_y": 0,
        "offset_sub_x": 0,
        "offset_sub_y": 418,
        "offset_wm_x": 0,
        "offset_wm_y": 0,
        "subtitle_y": SUBTITLE_Y + 418, # 1378
        "watermark_y": WATERMARK_Y,
        "font_size_sub": 55,            # CapCut dimensione 10 -> 55pt
        "font_size_wm": 0,
        "watermark_text": "",           # no watermark
        "stroke_width": 0,
        "shadow_offset": 0,
        "font_family": "Alata",
        "font_name": "Alata",
        "pattern": "Bold",
        "all_caps": False,
        "letter_spacing": 0,
    },
    {
        "id": "minimal_modern",
        "name": "Minimal Modern",
        "description": "Stile compatto con font Raleway, Dimensione 7, Posizione Y: -20, Watermark Posizione Y: -110",
        "is_default": False,
        "capcut_size": 7,
        "capcut_sub_scale": 100,
        "capcut_x": 0,
        "capcut_y": -20,
        "capcut_wm_size": 5,
        "capcut_wm_scale": 100,
        "capcut_wm_x": 0,
        "capcut_wm_y": -110,
        "offset_sub_x": 0,
        "offset_sub_y": 20,
        "offset_wm_x": 0,
        "offset_wm_y": 110,
        "subtitle_y": SUBTITLE_Y + 20,
        "watermark_y": WATERMARK_Y + 10,
        "font_size_sub": 38,
        "font_size_wm": 26,
        "watermark_text": "@lavocedelsuccesso",
        "stroke_width": 2,
        "shadow_offset": 1,
        "font_family": "Raleway",
        "font_name": "Raleway",
        "pattern": "Normal",
        "all_caps": False,
        "letter_spacing": 0,
    }
]

PRESETS_FILE = DATA_DIR / "presets.json"

def load_presets() -> list[dict[str, Any]]:
    # Se il file dati utente non esiste, proviamo a copiare dal template di fabbrica
    if not PRESETS_FILE.exists():
        factory_file = WORKSPACE / "presets.json"
        if factory_file.exists():
            try:
                data = json.loads(factory_file.read_text(encoding="utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    save_presets(data)
                    return data
            except Exception:
                pass
        save_presets(DEFAULT_PRESETS)
        return list(DEFAULT_PRESETS)
    try:
        data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list) and len(data) > 0:
            modified = False
            voce_idx = next((i for i, p in enumerate(data) if p.get("id") == "voce_del_successo"), None)
            if voce_idx is None:
                data.insert(0, DEFAULT_PRESET)
                modified = True
            else:
                # Se il preset voce_del_successo esistente ha ancora i vecchi valori senza capcut_wm_scale
                p = data[voce_idx]
                if "capcut_wm_scale" not in p or p.get("offset_wm_y") == 100:
                    for k, v in DEFAULT_PRESET.items():
                        if k not in p or p.get(k) is None or k in ("capcut_wm_scale", "capcut_sub_scale", "capcut_wm_y", "offset_wm_y", "watermark_y"):
                            p[k] = v
                    modified = True

            has_mc = any(p.get("id") == "mc" or p.get("name") == "MC" for p in data)
            if not has_mc:
                mc_preset = next((p for p in DEFAULT_PRESETS if p.get("id") == "mc"), None)
                if mc_preset:
                    data.append(mc_preset)
                    modified = True
            if modified:
                save_presets(data)
            return data
    except Exception as e:
        console.log(f"[yellow]Attenzione lettura presets.json: {e}[/]")
    return list(DEFAULT_PRESETS)

def save_presets(presets: list[dict[str, Any]]):
    try:
        PRESETS_FILE.write_text(json.dumps(presets, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        console.log(f"[red]Errore salvataggio presets.json: {e}[/]")

def extract_video_frame(video_path: Path, timestamp: float, output_png: Path) -> bool:
    """Tenta l'estrazione di un fotogramma esatto dal video a 1080x1920 via ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y",
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
        "ffmpeg", "-y", "-i", str(video_path.resolve()),
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

        if path == "/api/preset":
            presets = load_presets()
            self.send_json({"preset": presets[0] if presets else DEFAULT_PRESET, "success": True})
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
                kw_idx = select_keyword(w_list)
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
                    fs_sub = round(float(payload["capcut_size"]) * sub_scale * 5.5)
                else:
                    fs_sub = int(payload.get("font_size_sub", FONT_SIZE_SUB))

                wm_text = payload.get("watermark_text", WATERMARK_TEXT)
                fs_wm = int(payload.get("font_size_wm", FONT_SIZE_WM))

                if "capcut_sub_x" in payload and payload["capcut_sub_x"] is not None:
                    sub_ox = int(payload["capcut_sub_x"])
                elif "capcut_x" in payload and payload["capcut_x"] is not None:
                    sub_ox = int(payload["capcut_x"])
                else:
                    sub_ox = int(payload.get("offset_sub_x", 0))

                if "capcut_sub_y" in payload and payload["capcut_sub_y"] is not None:
                    sub_oy = -int(payload["capcut_sub_y"])
                elif "capcut_y" in payload and payload["capcut_y"] is not None:
                    sub_oy = -int(payload["capcut_y"])
                elif "offset_sub_y" in payload:
                    sub_oy = int(payload["offset_sub_y"])
                else:
                    sub_oy = int(payload.get("subtitle_y", SUBTITLE_Y)) - 960

                if "capcut_wm_size" in payload and payload["capcut_wm_size"]:
                    wm_scale = float(payload.get("capcut_wm_scale", 100)) / 100.0
                    fs_wm = round(float(payload["capcut_wm_size"]) * wm_scale * 5.5)
                else:
                    fs_wm = int(payload.get("font_size_wm", FONT_SIZE_WM))

                if "capcut_wm_x" in payload and payload["capcut_wm_x"] is not None:
                    wm_ox = int(payload["capcut_wm_x"])
                else:
                    wm_ox = int(payload.get("offset_wm_x", 0))

                if "capcut_wm_y" in payload and payload["capcut_wm_y"] is not None:
                    wm_oy = -int(payload["capcut_wm_y"])
                elif "offset_wm_y" in payload:
                    wm_oy = int(payload["offset_wm_y"])
                else:
                    wm_oy = int(payload.get("watermark_y", WATERMARK_Y)) - 960

                stroke_w = int(payload.get("stroke_width", 0))
                shadow_off = int(payload.get("shadow_offset", 0))
                all_caps = bool(payload.get("all_caps", False))
                letter_spacing = int(payload.get("letter_spacing", 0))

                font_name = payload.get("font_name") or payload.get("font_family") or "Raleway"
                pattern = payload.get("pattern", "")

                light_sub, semibold_sub = load_pair(fs_sub, font_name=font_name)
                _, semibold_wm = load_pair(fs_wm, font_name=font_name)

                from PIL import Image

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
                        letter_spacing=letter_spacing
                    )
                    render_watermark(
                        semibold_wm, wm_png, watermark_text=wm_text,
                        offset_x=wm_ox, offset_y=wm_oy,
                        stroke_width=stroke_w, shadow_offset=shadow_off
                    )

                    if has_frame and frame_png.exists():
                        try:
                            base = Image.open(frame_png).convert("RGBA")
                        except Exception:
                            base = Image.new("RGBA", (WIDTH, HEIGHT), (16, 18, 22, 255))
                    else:
                        # Fallback sfondo scuro stile podcast
                        base = Image.new("RGBA", (WIDTH, HEIGHT), (16, 18, 22, 255))

                    s_img = Image.open(sub_png)
                    w_img = Image.open(wm_png)
                    base.alpha_composite(s_img)
                    base.alpha_composite(w_img)

                    thumb = base.resize((360, 640), Image.Resampling.LANCZOS)
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
                    _, ffconcat_path, wm_path = render_all(
                        chunks=chunks_data,
                        work_dir=tmp_p,
                        total_duration=duration,
                        preset=preset,
                    )
                    burn_subtitles(
                        video_path=video_path,
                        ffconcat_path=ffconcat_path,
                        watermark_path=wm_path,
                        output_path=output_file,
                        use_hw=True,
                        quality=quality,
                        black_and_white=black_and_white,
                    )
                except Exception as e:
                    self.send_error_json(f"Errore durante il rendering: {str(e)}", 500)
                    return

            self.send_json({
                "success": True,
                "output_filename": out_name,
                "download_url": f"/media/{out_name}",
                "output_path": str(output_file)
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
            if not p_id or p_id == "new":
                slug = re.sub(r"[^a-zA-Z0-9_]+", "_", p_name.lower()).strip("_")
                p_id = f"preset_{slug}_{int(time.time())}" if slug else f"preset_{int(time.time())}"
            preset_data["id"] = p_id
            preset_data["name"] = p_name

            def _to_num(v, default=0, is_float=False):
                try:
                    return float(v) if is_float else int(round(float(v)))
                except (ValueError, TypeError):
                    return default

            # Valori CapCut nativi
            capcut_size = _to_num(preset_data.get("capcut_size", 10), 10, is_float=True)
            capcut_sub_scale = _to_num(preset_data.get("capcut_sub_scale", 100), 100, is_float=True)
            capcut_x = _to_num(preset_data.get("capcut_x", 0), 0)
            capcut_y = _to_num(preset_data.get("capcut_y", -418), -418)

            capcut_wm_size = _to_num(preset_data.get("capcut_wm_size", 5), 5, is_float=True)
            capcut_wm_scale = _to_num(preset_data.get("capcut_wm_scale", 100), 100, is_float=True)
            capcut_wm_x = _to_num(preset_data.get("capcut_wm_x", 0), 0)
            capcut_wm_y = _to_num(preset_data.get("capcut_wm_y", -207), -207)

            preset_data["capcut_size"] = capcut_size
            preset_data["capcut_sub_scale"] = capcut_sub_scale
            preset_data["capcut_x"] = capcut_x
            preset_data["capcut_y"] = capcut_y

            preset_data["capcut_wm_size"] = capcut_wm_size
            preset_data["capcut_wm_scale"] = capcut_wm_scale
            preset_data["capcut_wm_x"] = capcut_wm_x
            preset_data["capcut_wm_y"] = capcut_wm_y

            # Calcolo coordinate assolute ed effettive per il motore di rendering
            eff_sub_size = capcut_size * (capcut_sub_scale / 100.0)
            preset_data["font_size_sub"] = _to_num(preset_data.get("font_size_sub", round(eff_sub_size * 5.5)), round(eff_sub_size * 5.5))
            preset_data["offset_sub_x"] = capcut_x
            preset_data["offset_sub_y"] = -capcut_y
            preset_data["subtitle_y"] = SUBTITLE_Y - capcut_y

            eff_wm_size = capcut_wm_size * (capcut_wm_scale / 100.0)
            preset_data["font_size_wm"] = _to_num(preset_data.get("font_size_wm", round(eff_wm_size * 5.5)), round(eff_wm_size * 5.5))
            preset_data["offset_wm_x"] = capcut_wm_x
            preset_data["offset_wm_y"] = -capcut_wm_y
            preset_data["watermark_y"] = WATERMARK_Y - capcut_wm_y

            # Stili e font
            font = str(preset_data.get("font_name") or preset_data.get("font_family", "Raleway")).strip()
            preset_data["font_name"] = font
            preset_data["font_family"] = font
            preset_data["pattern"] = str(preset_data.get("pattern", "Light")).strip()
            preset_data["all_caps"] = bool(preset_data.get("all_caps", False))
            preset_data["letter_spacing"] = _to_num(preset_data.get("letter_spacing", 0), 0)
            preset_data["watermark_text"] = str(preset_data.get("watermark_text", "")).strip()
            preset_data["stroke_width"] = _to_num(preset_data.get("stroke_width", 0), 0)
            preset_data["shadow_offset"] = _to_num(preset_data.get("shadow_offset", 0), 0)

            presets = load_presets()
            updated = False
            for idx, p in enumerate(presets):
                if p.get("id") == p_id:
                    preset_data["is_default"] = p.get("is_default", False)
                    if "description" in p and ("description" not in preset_data or not preset_data["description"]):
                        preset_data["description"] = p["description"]
                    presets[idx] = preset_data
                    updated = True
                    break

            if not updated:
                preset_data["is_default"] = False
                if "description" not in preset_data or not preset_data["description"]:
                    preset_data["description"] = f"Preset personalizzato {p_name}"
                presets.append(preset_data)

            save_presets(presets)
            self.send_json({
                "success": True,
                "preset": preset_data,
                "presets": presets
            })
            return

        if path == "/api/delete_preset":
            p_id = payload.get("id")
            if not p_id:
                self.send_error_json("ID preset mancante")
                return

            if p_id == "voce_del_successo":
                self.send_error_json("Il preset 'La Voce del Successo' è protetto e non può essere eliminato")
                return

            presets = load_presets()
            new_presets = [p for p in presets if p.get("id") != p_id]
            if len(new_presets) == len(presets):
                self.send_error_json("Preset non trovato", 404)
                return

            save_presets(new_presets)
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
            if p_id == "voce_del_successo":
                self.send_error_json("Il preset 'La Voce del Successo' è protetto e non può essere eliminato")
                return
            presets = load_presets()
            new_presets = [p for p in presets if p.get("id") != p_id]
            save_presets(new_presets)
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
